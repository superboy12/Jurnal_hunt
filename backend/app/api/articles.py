"""Articles, bookmarks, journals, and export API routes."""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session, joinedload
import io

from ..core.database import get_db
from ..models.models import (
    Article, ArticleAuthor, ArticleBookmark, ResearchProject, Journal,
    SearchArticle, Search
)
from ..schemas.schemas import (
    ArticleSchema, AuthorSchema, BookmarkCreate, BookmarkUpdate,
    BookmarkSchema, ProjectCreate, ProjectSchema, JournalSchema
)
from ..services.export_service import (
    export_csv, export_bibtex, export_ris, export_apa7, export_xlsx
)

router = APIRouter(prefix="/api", tags=["articles"])
logger = logging.getLogger(__name__)


# ── Articles ────────────────────────────────────────────────────────────

@router.get("/articles/search-by-title")
async def search_by_title(
    title: str = Query(..., min_length=3, description="Judul artikel yang ingin dicari"),
    limit: int = Query(10, le=20),
):
    """Search articles by exact/fuzzy title using Crossref and OpenAlex."""
    import httpx
    results = []

    async with httpx.AsyncClient(timeout=15) as client:
        # 1. Try Crossref
        try:
            r = await client.get(
                "https://api.crossref.org/works",
                params={"query.bibliographic": title, "rows": limit, "select": "DOI,title,author,published,container-title,is-referenced-by-count,link,abstract"},
                headers={"User-Agent": "AI-Journal-Hunter/1.0 (mailto:support@journalhunter.app)"}
            )
            if r.status_code == 200:
                items = r.json().get("message", {}).get("items", [])
                for item in items:
                    titles = item.get("title", [])
                    if not titles:
                        continue
                    doi = item.get("DOI", "")
                    year = None
                    pub = item.get("published", {}).get("date-parts", [[None]])
                    if pub and pub[0]:
                        year = pub[0][0]
                    authors = []
                    for a in item.get("author", [])[:5]:
                        name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                        if name:
                            authors.append(name)
                    journal = (item.get("container-title") or [""])[0]
                    results.append({
                        "source": "Crossref",
                        "doi": doi,
                        "title": titles[0],
                        "year": year,
                        "authors": authors,
                        "journal_name": journal,
                        "citation_count": item.get("is-referenced-by-count"),
                        "is_open_access": None,
                        "open_access_url": None,
                        "sci_hub_url": f"https://sci-hub.box/{doi}" if doi else None,
                        "abstract": (item.get("abstract") or "")[:500],
                    })
        except Exception:
            pass

        # 2. Try OpenAlex
        try:
            r = await client.get(
                "https://api.openalex.org/works",
                params={"search": title, "per-page": limit, "select": "doi,title,authorships,publication_year,primary_location,cited_by_count,open_access,abstract_inverted_index"},
                headers={"User-Agent": "AI-Journal-Hunter/1.0"}
            )
            if r.status_code == 200:
                for item in r.json().get("results", []):
                    doi = (item.get("doi") or "").replace("https://doi.org/", "")
                    # Dedup with crossref
                    if doi and any(r.get("doi") == doi for r in results):
                        continue
                    authors = []
                    for a in item.get("authorships", [])[:5]:
                        name = (a.get("author") or {}).get("display_name", "")
                        if name:
                            authors.append(name)
                    loc = item.get("primary_location") or {}
                    source = loc.get("source") or {}
                    journal = source.get("display_name", "")
                    oa = item.get("open_access") or {}
                    is_oa = oa.get("is_oa", False)
                    oa_url = oa.get("oa_url")
                    results.append({
                        "source": "OpenAlex",
                        "doi": doi,
                        "title": item.get("title", ""),
                        "year": item.get("publication_year"),
                        "authors": authors,
                        "journal_name": journal,
                        "citation_count": item.get("cited_by_count"),
                        "is_open_access": is_oa,
                        "open_access_url": oa_url,
                        "sci_hub_url": f"https://sci-hub.box/{doi}" if doi else None,
                        "abstract": "",
                    })
        except Exception:
            pass

    return {
        "query": title,
        "total": len(results),
        "results": results[:limit]
    }


@router.get("/articles/{article_id}", response_model=ArticleSchema)
async def get_article(article_id: str, db: Session = Depends(get_db)):
    art = db.query(Article).options(
        joinedload(Article.authors)
    ).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(404, "Article not found")
    return _to_article_schema(art)


# ── Bookmarks ────────────────────────────────────────────────────────────

@router.post("/articles/{article_id}/save", response_model=BookmarkSchema)
async def save_article(
    article_id: str,
    req: BookmarkCreate,
    db: Session = Depends(get_db)
):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(404, "Article not found")

    existing = db.query(ArticleBookmark).filter(
        ArticleBookmark.article_id == article_id,
        ArticleBookmark.project_id == req.project_id,
    ).first()
    if existing:
        existing.status = req.status
        existing.notes = req.notes
        db.commit()
        return _to_bookmark_schema(existing, art)

    bookmark = ArticleBookmark(
        article_id=article_id,
        project_id=req.project_id,
        status=req.status,
        notes=req.notes,
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return _to_bookmark_schema(bookmark, art)


@router.get("/saved-articles", response_model=list[BookmarkSchema])
async def get_saved_articles(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ArticleBookmark).options(
        joinedload(ArticleBookmark.article).joinedload(Article.authors)
    )
    if project_id:
        query = query.filter(ArticleBookmark.project_id == project_id)
    bookmarks = query.order_by(ArticleBookmark.created_at.desc()).all()
    return [_to_bookmark_schema(b, b.article) for b in bookmarks]


@router.patch("/saved-articles/{bookmark_id}", response_model=BookmarkSchema)
async def update_bookmark(
    bookmark_id: str,
    req: BookmarkUpdate,
    db: Session = Depends(get_db)
):
    bookmark = db.query(ArticleBookmark).options(
        joinedload(ArticleBookmark.article)
    ).filter(ArticleBookmark.id == bookmark_id).first()
    if not bookmark:
        raise HTTPException(404, "Bookmark not found")
    if req.status:
        bookmark.status = req.status
    if req.notes is not None:
        bookmark.notes = req.notes
    if req.project_id is not None:
        bookmark.project_id = req.project_id
    db.commit()
    return _to_bookmark_schema(bookmark, bookmark.article)


@router.delete("/saved-articles/{bookmark_id}")
async def delete_bookmark(bookmark_id: str, db: Session = Depends(get_db)):
    bookmark = db.query(ArticleBookmark).filter(ArticleBookmark.id == bookmark_id).first()
    if not bookmark:
        raise HTTPException(404, "Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark removed"}


# ── Projects ────────────────────────────────────────────────────────────

@router.get("/projects", response_model=list[ProjectSchema])
async def get_projects(db: Session = Depends(get_db)):
    return db.query(ResearchProject).order_by(ResearchProject.created_at.desc()).all()


@router.post("/projects", response_model=ProjectSchema)
async def create_project(req: ProjectCreate, db: Session = Depends(get_db)):
    project = ResearchProject(name=req.name, description=req.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


# ── Journals ────────────────────────────────────────────────────────────

@router.get("/journals", response_model=list[JournalSchema])
async def get_journals(
    search: Optional[str] = Query(None),
    sinta_rank: Optional[int] = Query(None),
    scopus_only: bool = Query(False),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Journal)
    if search:
        query = query.filter(Journal.name.ilike(f"%{search}%"))
    if sinta_rank:
        query = query.filter(Journal.sinta_rank == sinta_rank)
    if scopus_only:
        query = query.filter(Journal.is_scopus_indexed == True)
    return query.limit(limit).all()


@router.get("/journals/{journal_id}", response_model=JournalSchema)
async def get_journal(journal_id: str, db: Session = Depends(get_db)):
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(404, "Journal not found")
    return journal


# ── Export ────────────────────────────────────────────────────────────

@router.get("/search/{search_id}/export/{format}")
async def export_search_results(
    search_id: str,
    format: str,
    db: Session = Depends(get_db),
):
    """Export search results. Format: csv, xlsx, bibtex, ris, apa7"""
    if format not in ("csv", "xlsx", "bibtex", "ris", "apa7"):
        raise HTTPException(400, "Invalid export format")

    search_articles = db.query(SearchArticle).options(
        joinedload(SearchArticle.article).joinedload(Article.authors)
    ).filter(
        SearchArticle.search_id == search_id
    ).order_by(SearchArticle.rank).all()

    if not search_articles:
        raise HTTPException(404, "No articles found for this search")

    filename = f"journal_hunter_results.{format if format != 'bibtex' else 'bib'}"

    if format == "csv":
        content = export_csv(search_articles)
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif format == "xlsx":
        content = export_xlsx(search_articles)
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif format == "bibtex":
        content = export_bibtex(search_articles)
        return StreamingResponse(
            io.StringIO(content),
            media_type="application/x-bibtex",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif format == "ris":
        content = export_ris(search_articles)
        return StreamingResponse(
            io.StringIO(content),
            media_type="application/x-research-info-systems",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif format == "apa7":
        content = export_apa7(search_articles)
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=references_apa7.txt"}
        )


# ── Citation ─────────────────────────────────────────────────────────

@router.get("/articles/{article_id}/citation")
async def get_citation(
    article_id: str,
    format: str = Query("apa7", pattern="^(apa7|bibtex|ris)$"),
    db: Session = Depends(get_db),
):
    """Get citation for a single article."""
    art = db.query(Article).options(
        joinedload(Article.authors)
    ).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(404, "Article not found")

    # Create a fake SearchArticle for the export functions
    class FakeSA:
        article = art
        rank = None
        relevance_score = 0
        relevance_reason = None
        source_found_in = []

    sa = FakeSA()
    if format == "apa7":
        return {"citation": export_apa7([sa]), "format": "apa7"}
    elif format == "bibtex":
        return {"citation": export_bibtex([sa]), "format": "bibtex"}
    elif format == "ris":
        return {"citation": export_ris([sa]), "format": "ris"}


# ── AI Research Tools ────────────────────────────────────────────────

@router.post("/articles/{article_id}/ai-summary")
async def get_article_ai_summary(
    article_id: str,
    model: str = Query("gemini-3-flash-preview"),
    db: Session = Depends(get_db),
):
    """Generate structured AI summary with key takeaways using 15-model AI engine."""
    from ..services.ai_service import ai_service
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(404, "Article not found")

    summary = await ai_service.summarize_article(art.title, art.abstract or "", model=model)
    return summary


@router.post("/articles/{article_id}/auto-resolve-access")
async def auto_resolve_article_access_post(article_id: str, db: Session = Depends(get_db)):
    """Alias POST for auto-resolve access."""
    return await auto_resolve_article_access(article_id, db)


@router.get("/articles/{article_id}/auto-resolve-access")
async def auto_resolve_article_access(article_id: str, db: Session = Depends(get_db)):
    """Auto-resolve full text access: check Unpaywall first, fallback to Sci-Hub."""
    import re
    import httpx
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(404, "Article not found")

    clean_doi = ""
    if art.doi:
        clean_doi = art.doi.strip()
        if clean_doi.startswith("http"):
            clean_doi = re.sub(r"^https?://[^/]+/", "", clean_doi)

    # If already open access
    if art.is_open_access and (art.open_access_url or art.pdf_url):
        return {
            "status": "open_access",
            "method": "direct",
            "url": art.pdf_url or art.open_access_url,
            "doi": clean_doi,
            "message": "Artikel ini sudah Open Access, dapat diakses langsung."
        }

    # Try Unpaywall
    if clean_doi:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"https://api.unpaywall.org/v2/{clean_doi}",
                    params={"email": "support@journalhunter.app"}
                )
                if r.status_code == 200:
                    data = r.json()
                    if data.get("is_oa"):
                        pdf_url = data.get("best_oa_location", {}).get("url_for_pdf") or data.get("best_oa_location", {}).get("url")
                        if pdf_url:
                            return {
                                "status": "open_access",
                                "method": "unpaywall",
                                "url": pdf_url,
                                "doi": clean_doi,
                                "message": f"Ditemukan versi Open Access legal via Unpaywall."
                            }
        except Exception:
            pass

        # Fallback to Sci-Hub
        return {
            "status": "sci_hub",
            "method": "sci_hub",
            "url": f"https://sci-hub.box/{clean_doi}",
            "doi": clean_doi,
            "message": "Dibuka via Sci-Hub. Naskah lengkap tersedia melalui portal ini."
        }

    return {
        "status": "unavailable",
        "method": None,
        "url": None,
        "doi": None,
        "message": "Artikel ini tidak memiliki DOI, tidak dapat di-resolve otomatis."
    }


@router.post("/search/{search_id}/ai-synthesis")
async def synthesize_search_results(
    search_id: str,
    model: str = Query("gemini-3-flash-preview"),
    db: Session = Depends(get_db),
):
    """Generate comprehensive literature review draft synthesizing search results."""
    from ..services.ai_service import ai_service
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(404, "Search not found")

    search_articles = db.query(SearchArticle).options(
        joinedload(SearchArticle.article).joinedload(Article.authors)
    ).filter(SearchArticle.search_id == search_id).order_by(SearchArticle.rank).limit(10).all()

    if not search_articles:
        raise HTTPException(404, "No articles found to synthesize")

    articles_data = []
    for sa in search_articles:
        art = sa.article
        articles_data.append({
            "title": art.title,
            "abstract": art.abstract,
            "year": art.year,
            "journal_name": art.journal_name,
            "authors": [{"name": a.name} for a in (art.authors or [])],
        })

    review = await ai_service.generate_literature_review(
        topic=search.user_command,
        articles=articles_data,
        model=model,
    )
    return {"topic": search.user_command, "model": model, "literature_review": review}


# ── Academic Directory & Scopus Verifier ───────────────────────────────

@router.get("/scopus/directory")
async def get_scopus_directory():
    """Return categorized academic search engines, Scopus verification portals, and OA publishers."""
    return {
        "search_engines": [
            {
                "id": "openalex",
                "name": "OpenAlex",
                "url": "https://openalex.org/",
                "api_status": "active",
                "role": "Mencari artikel berdasarkan kata kunci & tahun",
                "description": "Graf akademik terbuka terbesar di dunia dengan 250M+ karya ilmiah, sitasi, dan pemetaan institusi.",
                "features": ["Pencarian Kata Kunci", "Filter Rentang Tahun", "Kutipan Terbuka", "API Tanpa Kunci"],
                "badge": "Prioritas Utama 1",
            },
            {
                "id": "crossref",
                "name": "Crossref",
                "url": "https://www.crossref.org/",
                "api_status": "active",
                "role": "Melengkapi metadata dan DOI resmi",
                "description": "Otoritas pendaftaran DOI global utama untuk artikel ilmiah, buku, dan prosiding konferensi.",
                "features": ["Registrasi DOI Resmi", "Metadata Bibliografi", "Polite Pool API", "Verifikasi Penerbit"],
                "badge": "Prioritas Utama 2",
            },
            {
                "id": "unpaywall",
                "name": "Unpaywall",
                "url": "https://unpaywall.org/",
                "api_status": "active",
                "role": "Menemukan lokasi artikel Open Access yang legal",
                "description": "Basis data 50M+ artikel ilmiah dengan tautan langsung ke PDF legal bebas bayar.",
                "features": ["Direct Legal PDF", "OA License Check", "Pencarian Berbasis DOI", "Green & Gold OA"],
                "badge": "Prioritas OA Legal",
            },
            {
                "id": "doaj",
                "name": "DOAJ (Directory of Open Access Journals)",
                "url": "https://doaj.org/",
                "api_status": "active",
                "role": "Mencari jurnal & artikel Open Access terakreditasi",
                "description": "Direktori global independen yang mengindeks dan memvalidasi jurnal peer-reviewed Open Access berkualitas tinggi.",
                "features": ["Jurnal Tanpa Biaya APC", "Indeksasi Terakreditasi", "Lisensi Creative Commons", "Pencarian Artikel"],
                "badge": "Prioritas Peer-Reviewed OA",
            },
            {
                "id": "semantic_scholar",
                "name": "Semantic Scholar",
                "url": "https://www.semanticscholar.org/",
                "api_status": "active",
                "role": "Sumber tambahan untuk penelusuran artikel ilmiah berbasis AI",
                "description": "Mesin pencari ilmiah cerdas dari Allen Institute for AI dengan pemetaan kutipan berpengaruh.",
                "features": ["Highly Influential Citations", "Ringkasan TLDR", "Grafik Penulis", "AI Semantic Search"],
                "badge": "AI Semantic Graph",
            },
            {
                "id": "core",
                "name": "CORE",
                "url": "https://core.ac.uk/",
                "api_status": "active",
                "role": "Menemukan artikel dari repositori penelitian",
                "description": "Agregator repositori akses terbuka terbesar di dunia dari ribuan perpustakaan dan universitas.",
                "features": ["Repositori Universitas", "Disertasi & Tesis", "Naskah Pra-Cetak", "Akses Teks Lengkap"],
                "badge": "Repositori Terbesar",
            },
            {
                "id": "europe_pmc",
                "name": "Europe PMC",
                "url": "https://europepmc.org/",
                "api_status": "active",
                "role": "Repositori sains global & ilmu hayati dengan teks lengkap",
                "description": "Pusat literatur ilmiah terbuka dengan 40M+ naskah, terintegrasi PubMed Central dan data grant riset.",
                "features": ["40M+ Artikel Lengkap", "BioMed & Interdisipliner", "Tautan PDF Langsung", "REST API Cepat"],
                "badge": "40M+ Artikel Bebas",
            },
            {
                "id": "pmc",
                "name": "PubMed Central (PMC)",
                "url": "https://pmc.ncbi.nlm.nih.gov/",
                "api_status": "active",
                "role": "Arsip literatur biomedis dan ilmu hayati dari NIH/NLM",
                "description": "Arsip naskah ilmiah digital permanen milik National Institutes of Health Amerika Serikat.",
                "features": ["Arsip Permanen NIH", "Teks Lengkap Terbuka", "Verifikasi NLM", "Standar Internasional"],
                "badge": "Arsip NIH/NLM",
            },
            {
                "id": "arxiv",
                "name": "arXiv",
                "url": "https://arxiv.org/",
                "api_status": "active",
                "role": "Repositori pra-cetak komputer, AI, dan sains kuantitatif",
                "description": "Layanan distribusi akses terbuka 2.4M+ makalah ilmiah di bidang ilmu komputer, AI, matematika, dan fisika.",
                "features": ["Riset AI Terkini", "2.4M+ Pra-Cetak Bebas", "Direct PDF Cornell", "Open Science"],
                "badge": "Pusat Riset AI",
            },
            {
                "id": "openaire",
                "name": "OpenAIRE",
                "url": "https://explore.openaire.eu/",
                "api_status": "active",
                "role": "Infrastruktur sains terbuka Uni Eropa untuk publikasi & data",
                "description": "Jaringan infrastruktur penelitian terbuka Eropa yang menghubungkan publikasi, kumpulan data riset, dan hibah.",
                "features": ["Open Science Horizon", "Interkoneksi Data Riset", "Kepatuhan FAIR", "Monitoring Dampak"],
                "badge": "Infrastruktur Eropa",
            },
            {
                "id": "sci_hub",
                "name": "Sci-Hub Academic Unlocker",
                "url": "https://sci-hub.box/",
                "api_status": "active",
                "role": "Membuka akses naskah lengkap artikel berbayar/terkunci via DOI",
                "description": "Portal pembebas paywall riset global yang memungkinkan pengunduhan teks lengkap naskah akademik berbayar menggunakan nomor DOI.",
                "features": ["Bypass Paywall Berbayar", "Akses via Nomor DOI", "Unduhan PDF Langsung", "Global Academic Access"],
                "badge": "Paywall Bypass via DOI",
            },
        ],
        "scopus_verification": [
            {
                "id": "scopus_sources",
                "name": "Scopus Sources",
                "url": "https://www.scopus.com/sources",
                "role": "Portal resmi Elsevier untuk memverifikasi indeks jurnal Scopus",
                "description": "Daftar sumber resmi Scopus dengan metrik CiteScore, SJR, SNIP, kuartil, dan status cakupan aktif/discontinued.",
                "verification_method": "Cari berdasarkan Judul Jurnal, ISSN, atau Publisher",
                "badge": "Otoritas Resmi Scopus",
            },
            {
                "id": "scimago_jr",
                "name": "SCImago Journal & Country Rank (SJR)",
                "url": "https://www.scimagojr.com/",
                "role": "Verifikasi kuartil jurnal Scopus (Q1, Q2, Q3, Q4) dan metrik SJR",
                "description": "Portal publikasi ranking jurnal ilmiah internasional berbasis data Scopus (Elsevier) dengan peta visual kuartil tahunan.",
                "verification_method": "Ketik ISSN atau nama jurnal untuk melihat riwayat kuartil Q1–Q4",
                "badge": "Standar Kuartil Q1-Q4",
            },
            {
                "id": "elsevier_dev",
                "name": "Elsevier Developer Portal",
                "url": "https://dev.elsevier.com/",
                "role": "Portal integrasi API resmi Scopus dan ScienceDirect",
                "description": "Pusat dokumentasi dan kunci API untuk query Scopus Abstract API, Scopus Search API, dan SciVerse API.",
                "verification_method": "Pengembang dapat mendaftarkan API Key institusional",
                "badge": "API Pengembang Resmi",
            },
        ],
        "open_access_publishers": [
            {"name": "PLOS", "url": "https://plos.org/", "type": "Pure Open Access", "scope": "PLOS ONE, Biologi, Kedokteran, Sains Terbuka"},
            {"name": "BioMed Central (BMC)", "url": "https://www.biomedcentral.com/", "type": "Springer Nature OA", "scope": "300+ Jurnal Peer-reviewed Biomedis & Teknologi"},
            {"name": "MDPI", "url": "https://www.mdpi.com/", "type": "Open Access Multidisciplinary", "scope": "Sensors, Applied Sciences, Electronics, Sustainability"},
            {"name": "Frontiers", "url": "https://www.frontiersin.org/", "type": "Community-driven OA", "scope": "Frontiers in AI, Computer Science, Neuroscience, Robotics"},
            {"name": "Springer Nature", "url": "https://link.springer.com/", "type": "Hybrid & Open Access", "scope": "Nature Communications, Scientific Reports, Springer Open"},
            {"name": "IEEE Xplore", "url": "https://ieeexplore.ieee.org/", "type": "Engineering & Technology", "scope": "IEEE Access (Open Access), Transaksi, Prosiding"},
            {"name": "ACM Digital Library", "url": "https://dl.acm.org/", "type": "Computing & Informatics", "scope": "ACM Open, Jurnal Komputasi, Konferensi Internasional"},
            {"name": "ScienceDirect", "url": "https://www.sciencedirect.com/", "type": "Elsevier Platform", "scope": "Jurnal Scopus Q1-Q4, artikel Gold Open Access Elsevier"},
            {"name": "Wiley Online Library", "url": "https://onlinelibrary.wiley.com/", "type": "Wiley & Hindawi OA", "scope": "Ratusan jurnal terindeks Scopus & Open Access"},
            {"name": "Taylor & Francis Online", "url": "https://www.tandfonline.com/", "type": "Taylor & Francis Open", "scope": "Cogent OA, Jurnal Multidisiplin Internasional"},
        ],
        "recommendations": {
            "title": "Alur Rekomendasi Otomasi Pencarian Jurnal Ilmiah",
            "steps": [
                {"step": 1, "source": "OpenAlex", "action": "Mencari artikel berdasarkan kata kunci dan tahun publikasi."},
                {"step": 2, "source": "Crossref", "action": "Melengkapi metadata bibliografi dan DOI resmi penerbit."},
                {"step": 3, "source": "Unpaywall", "action": "Menemukan lokasi artikel Open Access yang legal dan tautan PDF bebas unduh."},
                {"step": 4, "source": "DOAJ", "action": "Mencari jurnal Open Access terakreditasi dan status APC."},
                {"step": 5, "source": "Scopus Sources & SCImago", "action": "Memverifikasi indeks jurnal Scopus dan klasifikasi kuartil Q1-Q4."},
                {"step": 6, "source": "Semantic Scholar & Europe PMC", "action": "Sumber tambahan untuk penelusuran naskah lengkap dan sitasi berpengaruh."},
                {"step": 7, "source": "CORE & arXiv", "action": "Menemukan artikel dari repositori penelitian global dan pra-cetak AI terkini."},
                {"step": 8, "source": "Sci-Hub (Bypass Paywall)", "action": "Mengunduh naskah lengkap artikel berbayar/terkunci secara bebas menggunakan DOI di https://sci-hub.box/."},
            ]
        }
    }


@router.get("/articles/{article_id}/verification-links")
async def get_article_verification(article_id: str, db: Session = Depends(get_db)):
    """Generate 1-click verification links and SCImago analysis for an article's journal."""
    import re
    from ..services.journal_verifier import get_scopus_verification_links
    from ..services.scimago_verifier import analyze_scimago_status
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(404, "Article not found")

    journal = art.journal
    canonical_jname = (journal.name if journal else None) or art.journal_name or art.publisher or ""
    links = get_scopus_verification_links(canonical_jname)
    clean_doi = ""
    if art.doi:
        clean_doi = art.doi.strip()
        if clean_doi.startswith("http"):
            clean_doi = re.sub(r"^https?://[^/]+/", "", clean_doi)
        links["unpaywall_direct"] = f"https://api.unpaywall.org/v2/{clean_doi}?email=user@journalhunter.app"
        links["doi_resolver"] = f"https://doi.org/{clean_doi}"
        links["sci_hub"] = f"https://sci-hub.box/{clean_doi}"
        links["sci_hub_base"] = "https://sci-hub.box/"

    if journal and journal.is_scopus_indexed:
        scimago_analysis = {
            "is_scopus": True,
            "verified_by_scimago": True,
            "quartile": journal.scimago_quartile or "Terindeks",
            "sjr_score": journal.sjr_score,
            "h_index": journal.h_index,
            "country": "Indonesia" if (journal.sinta_rank or "indonesia" in canonical_jname.lower()) else None,
            "scimago_url": journal.scimago_url or f"https://www.scimagojr.com/journalsearch.php?q={canonical_jname.replace(' ', '%20')}",
            "scopus_sources_url": f"https://www.scopus.com/sources.uri?query={canonical_jname.replace(' ', '%20')}",
            "message": f"Terverifikasi Scopus via SCImago JR ({journal.scimago_quartile or 'Terindeks'}, SJR: {journal.sjr_score if journal.sjr_score is not None else '-'})",
        }
    else:
        scimago_analysis = analyze_scimago_status(canonical_jname)

    return {
        "article_id": art.id,
        "title": art.title,
        "journal_name": canonical_jname,
        "doi": art.doi,
        "clean_doi": clean_doi,
        "sci_hub_url": f"https://sci-hub.box/{clean_doi}" if clean_doi else "https://sci-hub.box/",
        "verification_links": links,
        "scimago_analysis": scimago_analysis,
    }


# ── Helpers ────────────────────────────────────────────────────────────

def _to_article_schema(art: Article) -> ArticleSchema:
    import re
    clean_doi = ""
    if art.doi:
        clean_doi = art.doi.strip()
        if clean_doi.startswith("http"):
            clean_doi = re.sub(r"^https?://[^/]+/", "", clean_doi)
    sci_hub_url = f"https://sci-hub.box/{clean_doi}" if clean_doi else None

    return ArticleSchema(
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
    )


def _to_bookmark_schema(bookmark: ArticleBookmark, art: Article) -> BookmarkSchema:
    return BookmarkSchema(
        id=bookmark.id,
        article_id=bookmark.article_id,
        project_id=bookmark.project_id,
        status=bookmark.status,
        notes=bookmark.notes,
        created_at=bookmark.created_at,
        article=_to_article_schema(art) if art else None,
    )
