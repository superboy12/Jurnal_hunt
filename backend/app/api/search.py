"""Search API routes."""
from __future__ import annotations
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from ..core.database import get_db
from ..core.config import settings
from ..models.models import (
    Search, SearchParameter, SearchArticle, Article, Journal, SearchStatus
)
from ..schemas.schemas import (
    SearchCommandRequest, StartSearchRequest, SearchParameterSchema,
    SearchSummarySchema, PaginatedArticles, SearchArticleSchema, ArticleSchema,
    AuthorSchema, InterpretedCommand
)
from ..services.command_interpreter import interpret_command, interpret_command_async
from ..services.search_pipeline import run_search_pipeline

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)

# Track running search tasks
_running_tasks: dict[str, asyncio.Task] = {}


@router.post("/interpret-command", response_model=InterpretedCommand)
async def interpret_search_command(req: SearchCommandRequest):
    """Parse a natural language command and return structured parameters with Gemini AI."""
    active_presets = req.presets or ([req.preset] if req.preset else [])
    result = await interpret_command_async(req.command, req.preset, active_presets)
    return result


@router.post("/search", response_model=SearchSummarySchema)
async def create_search(
    req: StartSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new search and start it in the background."""
    # Create search record
    search = Search(user_command=req.command, status=SearchStatus.PENDING)
    db.add(search)
    db.flush()

    # Save parameters
    param = SearchParameter(
        search_id=search.id,
        topic=req.parameters.topic,
        keywords=req.parameters.keywords,
        synonyms=req.parameters.synonyms,
        language=req.parameters.language,
        year_from=req.parameters.year_from,
        year_to=req.parameters.year_to,
        max_results=min(req.parameters.max_results, settings.max_results_per_search),
        indexing_target=req.parameters.indexing_target,
        sinta_rank_min=req.parameters.sinta_rank_min,
        sinta_rank_max=req.parameters.sinta_rank_max,
        publication_type=req.parameters.publication_type,
        open_access_only=req.parameters.open_access_only,
        require_doi=req.parameters.require_doi,
        require_pdf=req.parameters.require_pdf,
        max_apc=req.parameters.max_apc,
        sources=req.parameters.sources,
        extra_params=req.parameters.extra_params,
    )
    db.add(param)
    db.commit()
    db.refresh(search)

    # Run in background
    background_tasks.add_task(_background_search, search.id, req.parameters)

    return _to_search_summary(search, db)


async def _background_search(search_id: str, params: SearchParameterSchema):
    """Background task wrapper for search pipeline."""
    from ..core.database import SessionLocal
    db = SessionLocal()
    try:
        await run_search_pipeline(search_id, params, db)
    finally:
        db.close()


@router.get("/search/{search_id}", response_model=SearchSummarySchema)
async def get_search(search_id: str, db: Session = Depends(get_db)):
    """Get search status and summary."""
    search = db.query(Search).options(
        joinedload(Search.source_logs)
    ).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(404, "Search not found")
    return _to_search_summary(search, db)


@router.get("/search/{search_id}/results", response_model=PaginatedArticles)
async def get_search_results(
    search_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("relevance", pattern="^(relevance|year|citations|title)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    open_access_only: bool = Query(False),
    min_score: float = Query(0.0, ge=0, le=100),
    sinta_rank: Optional[int] = Query(None, ge=1, le=6),
    scopus_only: bool = Query(False),
    indexing_target: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get paginated search results with optional SINTA rank, Scopus, and subject category filters."""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(404, "Search not found")

    # Aggregate category counts for all articles in this search
    cat_agg = db.query(Article.subject_category, func.count(Article.id)).join(
        SearchArticle, SearchArticle.article_id == Article.id
    ).filter(SearchArticle.search_id == search_id).group_by(Article.subject_category).all()
    category_counts = {c or "Lainnya": count for c, count in cat_agg if c}
    available_categories = sorted(list(category_counts.keys()))

    query = db.query(SearchArticle).options(
        joinedload(SearchArticle.article).joinedload(Article.authors),
        joinedload(SearchArticle.article).joinedload(Article.journal),
    ).filter(SearchArticle.search_id == search_id)

    # Parse multi-categories
    cat_list = []
    if categories:
        cat_list = [c.strip() for c in categories.split(",") if c.strip() and c.strip().lower() != "all"]
    elif category and category.lower() != "all":
        cat_list = [c.strip() for c in category.split(",") if c.strip()]

    need_journal_join = (
        sinta_rank is not None or scopus_only or
        (indexing_target is not None and indexing_target != "all")
    )
    need_article_join = (
        open_access_only or need_journal_join or
        bool(cat_list) or
        sort_by in ("year", "citations", "title")
    )
    if need_article_join:
        query = query.join(Article, SearchArticle.article_id == Article.id)

    if cat_list:
        query = query.filter(or_(*[Article.subject_category.ilike(f"%{c}%") for c in cat_list]))

    if need_journal_join:
        query = query.join(Journal, Article.journal_id == Journal.id)
        if indexing_target == "both":
            query = query.filter(or_(Journal.is_scopus_indexed == True, Journal.sinta_rank.isnot(None)))
        elif indexing_target == "scopus" or scopus_only:
            query = query.filter(Journal.is_scopus_indexed == True)
        elif indexing_target == "sinta":
            query = query.filter(Journal.sinta_rank.isnot(None))
        elif sinta_rank is not None:
            query = query.filter(Journal.sinta_rank == sinta_rank)

    if min_score > 0:
        query = query.filter(SearchArticle.relevance_score >= min_score)

    if open_access_only:
        query = query.filter(Article.is_open_access == True)

    # Sorting
    sort_col_map = {
        "relevance": SearchArticle.relevance_score,
        "year": Article.year,
        "citations": Article.citation_count,
        "title": Article.title,
    }
    sort_col = sort_col_map.get(sort_by, SearchArticle.relevance_score)
    if order == "desc":
        query = query.order_by(sort_col.desc().nullslast())
    else:
        query = query.order_by(sort_col.asc().nullsfirst())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedArticles(
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        items=[_to_search_article_schema(sa) for sa in items],
        available_categories=available_categories,
        category_counts=category_counts,
    )


@router.post("/search/{search_id}/cancel")
async def cancel_search(search_id: str, db: Session = Depends(get_db)):
    """Cancel a running search."""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(404, "Search not found")
    if search.status != SearchStatus.RUNNING:
        raise HTTPException(400, f"Search is not running (status: {search.status})")

    search.status = SearchStatus.CANCELLED
    db.commit()
    return {"message": "Search cancelled"}


@router.get("/history", response_model=list[SearchSummarySchema])
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recent search history."""
    searches = db.query(Search).options(
        joinedload(Search.source_logs)
    ).order_by(Search.created_at.desc()).limit(limit).all()
    return [_to_search_summary(s, db) for s in searches]


# ── Helpers ────────────────────────────────────────────────────────────

def _to_search_summary(search: Search, db: Session) -> SearchSummarySchema:
    return SearchSummarySchema(
        id=search.id,
        user_command=search.user_command,
        status=search.status,
        total_found=search.total_found,
        total_after_dedup=search.total_after_dedup,
        total_verified=search.total_verified,
        total_open_access=search.total_open_access,
        error_message=search.error_message,
        created_at=search.created_at,
        started_at=search.started_at,
        completed_at=search.completed_at,
        source_logs=[
            {
                "source_name": log.source_name,
                "status": log.status,
                "articles_found": log.articles_found,
                "error_message": log.error_message,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
                "request_count": log.request_count,
            }
            for log in (search.source_logs or [])
        ],
    )


def _to_search_article_schema(sa: SearchArticle) -> SearchArticleSchema:
    art = sa.article
    if not art:
        return None

    clean_doi = ""
    if art.doi:
        clean_doi = art.doi.strip()
        if clean_doi.startswith("http"):
            clean_doi = re.sub(r"^https?://[^/]+/", "", clean_doi)
    sci_hub_url = f"https://sci-hub.box/{clean_doi}" if clean_doi else None

    return SearchArticleSchema(
        article=ArticleSchema(
            id=art.id,
            doi=art.doi,
            title=art.title,
            abstract=art.abstract,
            year=art.year,
            publication_date=art.publication_date,
            journal_name=art.journal_name,
            publisher=art.publisher,
            volume=art.volume,
            issue=art.issue,
            pages=art.pages,
            language=art.language,
            keywords=art.keywords or [],
            publication_type=art.publication_type.value if art.publication_type else None,
            is_open_access=art.is_open_access,
            open_access_url=art.open_access_url,
            pdf_url=art.pdf_url,
            article_url=art.article_url,
            sci_hub_url=sci_hub_url,
            citation_count=art.citation_count,
            sources=art.sources or [],
            verification_status=art.verification_status,
            authors=[
                AuthorSchema(
                    name=a.name,
                    affiliation=a.affiliation,
                    orcid=a.orcid,
                    order=a.order,
                )
                for a in sorted(art.authors, key=lambda x: x.order)
            ],
        ),
        relevance_score=sa.relevance_score,
        relevance_reason=sa.relevance_reason,
        rank=sa.rank,
        source_found_in=sa.source_found_in or [],
        sinta_rank=art.journal.sinta_rank if art.journal else None,
        is_scopus=art.journal.is_scopus_indexed if art.journal else None,
        scimago_quartile=art.journal.scimago_quartile if art.journal else None,
        sjr_score=art.journal.sjr_score if art.journal else None,
        scimago_url=art.journal.scimago_url if art.journal else None,
        sci_hub_url=sci_hub_url,
        subject_category=art.subject_category,
    )
