"""Search pipeline: orchestrates all adapters, deduplication, and scoring."""
from __future__ import annotations
import asyncio
import logging
import unicodedata
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session

from ..adapters.base import RawArticle
from ..adapters.crossref import CrossrefAdapter
from ..adapters.openalex import OpenAlexAdapter
from ..adapters.semantic_scholar import SemanticScholarAdapter
from ..adapters.doaj import DOAJAdapter
from ..adapters.scopus import ScopusAdapter
from ..adapters.europe_pmc import EuropePMCAdapter
from ..adapters.arxiv import ArxivAdapter
from ..adapters.unpaywall import UnpaywallResolver
from ..adapters.scorer import score_article
from ..models.models import (
    Search, SearchParameter, SearchSourceLog, Article, ArticleAuthor,
    SearchArticle, Journal, SearchStatus, VerificationStatus, PublicationType
)
from ..schemas.schemas import SearchParameterSchema
from .journal_verifier import verify_and_link_article

logger = logging.getLogger(__name__)

ADAPTER_MAP = {
    "crossref": CrossrefAdapter,
    "openalex": OpenAlexAdapter,
    "semantic_scholar": SemanticScholarAdapter,
    "doaj": DOAJAdapter,
    "scopus": ScopusAdapter,
    "europe_pmc": EuropePMCAdapter,
    "arxiv": ArxivAdapter,
}


async def run_search_pipeline(
    search_id: str,
    params: SearchParameterSchema,
    db: Session,
    progress_callback: Optional[Callable] = None,
) -> None:
    """Main pipeline: search → merge → dedup → score → save."""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        return

    # Mark as running
    search.status = SearchStatus.RUNNING
    search.started_at = datetime.now(timezone.utc)
    db.commit()

    try:
        # Determine sources to use
        requested_sources = params.sources or list(ADAPTER_MAP.keys())
        adapters = []
        for source in requested_sources:
            cls = ADAPTER_MAP.get(source)
            if cls:
                adapter = cls()
                adapters.append(adapter)

        # Create source logs
        source_logs: Dict[str, SearchSourceLog] = {}
        for adapter in adapters:
            log = SearchSourceLog(
                search_id=search_id,
                source_name=adapter.name,
                status="pending" if adapter.is_available else "skipped",
            )
            db.add(log)
            source_logs[adapter.name] = log
        db.commit()

        # Run all adapters concurrently
        tasks = []
        for adapter in adapters:
            if adapter.is_available:
                tasks.append(_run_adapter(
                    adapter, params, source_logs[adapter.name], db
                ))

        all_results: List[RawArticle] = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Adapter failed: {result}")
                elif isinstance(result, list):
                    all_results.extend(result)

        total_found = len(all_results)

        # Deduplication
        deduped = _deduplicate(all_results)
        total_deduped = len(deduped)

        # Apply filters
        filtered = _apply_filters(deduped, params)

        # Score articles
        scored: List[tuple[RawArticle, float, str]] = []
        for article in filtered:
            score, reason = score_article(
                article,
                keywords=params.keywords,
                synonyms=params.synonyms,
                year_from=params.year_from,
                year_to=params.year_to,
                open_access_only=params.open_access_only,
                require_pdf=params.require_pdf,
                publication_type=params.publication_type,
            )
            scored.append((article, score, reason))

        # Sort by score descending and filter out zero-score (irrelevant) articles
        scored.sort(key=lambda x: x[1], reverse=True)
        valid_scored = [s for s in scored if s[1] > 0]
        if valid_scored:
            scored = valid_scored[:params.max_results]
        else:
            scored = scored[:params.max_results]

        # Resolve Open Access & legal direct PDF links via Unpaywall in parallel for top articles
        async def _enrich_oa(raw_art: RawArticle):
            if raw_art.doi and (raw_art.is_open_access is not True or not raw_art.pdf_url):
                try:
                    oa_info = await UnpaywallResolver.resolve_oa_location(raw_art.doi)
                    if oa_info:
                        if oa_info.get("is_oa"):
                            raw_art.is_open_access = True
                            if oa_info.get("pdf_url") and not raw_art.pdf_url:
                                raw_art.pdf_url = oa_info.get("pdf_url")
                            if oa_info.get("landing_url") and not raw_art.open_access_url:
                                raw_art.open_access_url = oa_info.get("landing_url")
                        elif oa_info.get("is_oa") is False:
                            if raw_art.is_open_access is None:
                                raw_art.is_open_access = False
                except Exception as e:
                    logger.debug(f"Unpaywall lookup error for {raw_art.doi}: {e}")

        oa_tasks = [_enrich_oa(art) for art, _, _ in scored if art.doi]
        if oa_tasks:
            await asyncio.gather(*oa_tasks, return_exceptions=True)

        # Batch SINTA & Scopus verification for candidate journals
        from .ai_service import ai_service
        raw_jnames = list({art.journal_name.strip() for art, _, _ in scored if art.journal_name and len(art.journal_name.strip()) > 3})
        unverified_jnames = []
        for jn in raw_jnames:
            existing_j = db.query(Journal).filter(
                (Journal.name.ilike(f"%{jn}%")) | (Journal.name == jn)
            ).first()
            if not existing_j or (existing_j.sinta_rank is None and not existing_j.is_scopus_indexed):
                unverified_jnames.append(jn)

        if unverified_jnames:
            try:
                sinta_map = await ai_service.verify_journals_sinta_batch(unverified_jnames)
                for jn, info in sinta_map.items():
                    if isinstance(info, dict) and info.get("is_sinta") and info.get("sinta_rank"):
                        s_rank = info.get("sinta_rank")
                        if isinstance(s_rank, str):
                            m_rank = re.search(r"\d+", s_rank)
                            s_rank = int(m_rank.group(0)) if m_rank else None

                        if s_rank and 1 <= s_rank <= 6:
                            is_scop = bool(info.get("is_scopus", False) or s_rank == 1)
                            existing_j = db.query(Journal).filter(
                                (Journal.name.ilike(f"%{jn}%")) | (Journal.name == jn)
                            ).first()
                            if existing_j:
                                existing_j.sinta_rank = s_rank
                                if is_scop:
                                    existing_j.is_scopus_indexed = True
                                existing_j.verification_source = "sinta_verified"
                            else:
                                new_j = Journal(
                                    name=jn,
                                    sinta_rank=s_rank,
                                    is_scopus_indexed=is_scop,
                                    is_open_access=True,
                                    verification_source="sinta_verified",
                                    verified_at=datetime.now(timezone.utc),
                                )
                                db.add(new_j)
                            db.commit()
            except Exception as e:
                logger.warning(f"Batch SINTA verification step error: {e}")

        # Save articles to DB
        total_oa = 0
        total_verified = 0

        # Instant subject category classification (heuristic + fast AI refinement)
        category_map: Dict[str, str] = {}
        for raw_art, _, _ in scored:
            art_key = raw_art.doi or raw_art.title[:40]
            category_map[art_key] = _classify_subject_heuristic(
                raw_art.title, raw_art.abstract or "", raw_art.journal_name or ""
            )

        for rank, (raw_art, score, reason) in enumerate(scored, 1):
            # Attach subject category from classification result
            art_key = raw_art.doi or raw_art.title[:40]
            subject_cat = category_map.get(art_key)
            db_article = _save_article(raw_art, db, subject_category=subject_cat)
            if db_article:
                # Link to search
                existing = db.query(SearchArticle).filter(
                    SearchArticle.search_id == search_id,
                    SearchArticle.article_id == db_article.id
                ).first()
                if not existing:
                    sa = SearchArticle(
                        search_id=search_id,
                        article_id=db_article.id,
                        relevance_score=score,
                        relevance_reason=reason,
                        rank=rank,
                        source_found_in=raw_art.sources if hasattr(raw_art, 'sources') else [raw_art.source],
                    )
                    db.add(sa)
                if db_article.is_open_access or raw_art.is_open_access:
                    total_oa += 1
                if db_article.verification_status in (
                    VerificationStatus.VERIFIED_SCOPUS,
                    VerificationStatus.VERIFIED_SINTA,
                    VerificationStatus.VERIFIED_BOTH,
                ):
                    total_verified += 1

        db.commit()

        # Update search summary
        search.total_found = total_found
        search.total_after_dedup = total_deduped
        search.total_open_access = total_oa
        search.total_verified = total_verified
        search.status = SearchStatus.COMPLETED
        search.completed_at = datetime.now(timezone.utc)
        db.commit()

    except asyncio.CancelledError:
        search.status = SearchStatus.CANCELLED
        search.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        logger.error(f"Pipeline failed for search {search_id}: {e}", exc_info=True)
        search.status = SearchStatus.FAILED
        search.error_message = str(e)
        search.completed_at = datetime.now(timezone.utc)
        db.commit()


async def _run_adapter(
    adapter,
    params: SearchParameterSchema,
    log: SearchSourceLog,
    db: Session,
) -> List[RawArticle]:
    """Run a single adapter and update its log."""
    log.status = "running"
    log.started_at = datetime.now(timezone.utc)
    db.commit()

    try:
        articles = await adapter.search(
            keywords=params.keywords,
            synonyms=params.synonyms,
            year_from=params.year_from,
            year_to=params.year_to,
            max_results=params.max_results,
            extra_params={
                "open_access_only": params.open_access_only,
                "publication_type": params.publication_type,
                "indexing_target": params.indexing_target,
            },
        )
        log.status = "completed"
        log.articles_found = len(articles)
        log.completed_at = datetime.now(timezone.utc)
        db.commit()
        return articles
    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)
        log.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.error(f"Adapter {adapter.name} failed: {e}")
        return []


def _normalize_title(title: str) -> str:
    """Normalize title for deduplication."""
    if not title:
        return ""
    t = unicodedata.normalize("NFKD", title.lower())
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _deduplicate(articles: List[RawArticle]) -> List[RawArticle]:
    """Deduplicate by DOI first, then normalized title."""
    seen_doi: Dict[str, RawArticle] = {}
    seen_title: Dict[str, RawArticle] = {}
    result: List[RawArticle] = []

    for art in articles:
        doi = art.doi
        norm_title = _normalize_title(art.title)

        if doi and doi in seen_doi:
            # Merge sources
            existing = seen_doi[doi]
            if hasattr(existing, '_sources'):
                existing._sources.append(art.source)
            else:
                existing._sources = [existing.source, art.source]
            # Prefer richer data
            if not existing.abstract and art.abstract:
                existing.abstract = art.abstract
            if not existing.is_open_access and art.is_open_access:
                existing.is_open_access = art.is_open_access
                existing.pdf_url = existing.pdf_url or art.pdf_url
            continue

        if norm_title and norm_title in seen_title:
            existing = seen_title[norm_title]
            if hasattr(existing, '_sources'):
                existing._sources.append(art.source)
            else:
                existing._sources = [existing.source, art.source]
            # If new one has DOI, prefer it
            if not existing.doi and art.doi:
                existing.doi = art.doi
            if not existing.abstract and art.abstract:
                existing.abstract = art.abstract
            continue

        art._sources = [art.source]
        result.append(art)
        if doi:
            seen_doi[doi] = art
        if norm_title:
            seen_title[norm_title] = art

    return result


def _apply_filters(articles: List[RawArticle], params: SearchParameterSchema) -> List[RawArticle]:
    """Apply user filters to article list."""
    filtered = []
    for art in articles:
        if params.open_access_only and not art.is_open_access:
            continue
        if params.require_doi and not art.doi:
            continue
        if params.require_pdf and not art.pdf_url:
            continue
        if params.year_from and art.year and art.year < params.year_from:
            continue
        if params.year_to and art.year and art.year > params.year_to:
            continue
        if params.language and art.language and art.language != params.language:
            continue
        filtered.append(art)
    return filtered


def _classify_subject_heuristic(title: str, abstract: str = "", journal_name: str = "") -> str:
    """Heuristic subject categorization fallback."""
    text = f"{title} {abstract} {journal_name}".lower()

    # Hukum & Kebijakan
    legal_keywords = [
        "hukum", "pidana", "perdata", "yuridis", "undang-undang", "uu ite", "kebijakan",
        "regulasi", "penegakan hukum", "kriminologi", "putusan hakim", "pasal", "tindak pidana",
        "law", "legal", "jurisdiction", "regulation", "court", "legislation", "justice"
    ]
    # Keamanan Siber
    cyber_keywords = [
        "keamanan", "siber", "cyber", "dns", "firewall", "malware", "phishing", "threat",
        "vulnerability", "encryption", "kriptografi", "enkripsi", "ddos", "pemblokiran",
        "blocking", "content filtering", "ids/ips", "intrusion", "network security", "antivirus",
        "keamanan jaringan", "keamanan informasi", "penetration testing", "cyber security"
    ]
    # Teknologi Informasi & Komputer
    it_keywords = [
        "sistem informasi", "teknologi informasi", "komputer", "algoritma", "machine learning",
        "deep learning", "kecerdasan buatan", "artificial intelligence", "software", "perangkat lunak",
        "basis data", "database", "web", "aplikasi", "mobile", "cloud", "iot", "internet of things",
        "neural network", "data mining", "klasifikasi", "information technology", "computer science"
    ]
    # Kesehatan
    health_keywords = ["kesehatan", "medis", "kedokteran", "klinis", "farmasi", "keperawatan", "health", "medical"]
    # Pendidikan
    edu_keywords = ["pendidikan", "pembelajaran", "kurikulum", "sekolah", "siswa", "mahasiswa", "education", "learning"]
    # Ekonomi & Bisnis
    econ_keywords = ["ekonomi", "bisnis", "manajemen", "keuangan", "akuntansi", "pasar", "economy", "finance", "business"]

    # Count hits
    def count_hits(keywords):
        return sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text))

    legal_score = count_hits(legal_keywords)
    cyber_score = count_hits(cyber_keywords)
    it_score = count_hits(it_keywords)
    health_score = count_hits(health_keywords)
    edu_score = count_hits(edu_keywords)
    econ_score = count_hits(econ_keywords)

    scores = [
        ("Hukum & Kebijakan", legal_score),
        ("Keamanan Siber", cyber_score),
        ("Teknologi Informasi & Komputer", it_score),
        ("Kesehatan & Kedokteran", health_score),
        ("Pendidikan", edu_score),
        ("Ekonomi & Bisnis", econ_score),
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    if scores[0][1] > 0:
        return scores[0][0]
    return "Teknologi Informasi & Komputer"


def _save_article(raw: RawArticle, db: Session, subject_category: Optional[str] = None) -> Optional[Article]:
    """Save or update article in database."""
    try:
        existing = None

        # Determine subject category (AI result or heuristic fallback)
        if not subject_category:
            subject_category = _classify_subject_heuristic(raw.title, raw.abstract or "", raw.journal_name or "")

        # Try to find by DOI
        if raw.doi:
            existing = db.query(Article).filter(Article.doi == raw.doi).first()

        # Try by normalized title
        if not existing:
            norm_title = _normalize_title(raw.title)
            existing = db.query(Article).filter(
                Article.title_normalized == norm_title
            ).first()

        if existing:
            # Update with richer data
            if not existing.subject_category:
                existing.subject_category = subject_category
            if not existing.abstract and raw.abstract:
                existing.abstract = raw.abstract
            if raw.is_open_access is True:
                existing.is_open_access = True
            if not existing.pdf_url and raw.pdf_url:
                existing.pdf_url = raw.pdf_url
            if not existing.open_access_url and raw.open_access_url:
                existing.open_access_url = raw.open_access_url
            sources = existing.sources or []
            if raw.source not in sources:
                sources.append(raw.source)
                existing.sources = sources
            if not existing.journal_id or existing.verification_status == VerificationStatus.PENDING:
                j, _ = verify_and_link_article(db, existing, getattr(raw, 'issn', None), getattr(raw, 'eissn', None))
                if j and (j.sinta_rank or j.is_open_access):
                    existing.is_open_access = True
            elif existing.journal and (existing.journal.sinta_rank or existing.journal.is_open_access):
                existing.is_open_access = True
            if existing.pdf_url:
                existing.is_open_access = True
            db.commit()
            return existing

        # Determine publication type
        pub_type = PublicationType.JOURNAL
        if raw.journal_name:
            j_lower = raw.journal_name.lower()
            if any(kw in j_lower for kw in ["pengabdian", "abdimas", "community service"]):
                pub_type = PublicationType.COMMUNITY_SERVICE
            elif any(kw in j_lower for kw in ["proceedings", "conference"]):
                pub_type = PublicationType.CONFERENCE

        article = Article(
            doi=raw.doi,
            title=raw.title,
            title_normalized=_normalize_title(raw.title),
            abstract=raw.abstract,
            year=raw.year,
            publication_date=raw.publication_date,
            journal_name=raw.journal_name,
            publisher=raw.publisher,
            volume=raw.volume,
            issue=raw.issue,
            pages=raw.pages,
            language=raw.language,
            keywords=raw.keywords,
            publication_type=pub_type,
            is_open_access=raw.is_open_access,
            open_access_url=raw.open_access_url,
            pdf_url=raw.pdf_url,
            article_url=raw.article_url,
            citation_count=raw.citation_count,
            subject_category=subject_category,
            sources=[raw.source],
            source_ids={raw.source: raw.source_id or ""},
            verification_status=VerificationStatus.PENDING,
        )
        db.add(article)
        db.flush()  # Get ID

        # Save authors
        for i, auth_data in enumerate(raw.authors):
            author = ArticleAuthor(
                article_id=article.id,
                name=auth_data.get("name", ""),
                affiliation=auth_data.get("affiliation"),
                orcid=auth_data.get("orcid"),
                order=i,
            )
            db.add(author)

        # Verify indexing with SINTA & Scopus
        j, status = verify_and_link_article(db, article, getattr(raw, 'issn', None), getattr(raw, 'eissn', None))
        if j and (j.sinta_rank or j.is_open_access):
            article.is_open_access = True
        if article.pdf_url:
            article.is_open_access = True

        db.commit()
        return article

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save article '{raw.title[:50]}': {e}")
        return None
