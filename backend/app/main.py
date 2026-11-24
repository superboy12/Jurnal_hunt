"""FastAPI main application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.database import engine, Base
from .api.search import router as search_router
from .api.articles import router as articles_router
from .models import models  # Ensure models are registered

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events."""
    logger.info("Starting AI Journal Hunter API...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Seed reference journals and default users
    from .core.database import SessionLocal
    from .services.journal_verifier import seed_journals_if_empty
    db = SessionLocal()
    try:
        seed_journals_if_empty(db)
    except Exception as e:
        logger.warning(f"Could not seed initial data: {e}")
    finally:
        db.close()

    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="AI Journal Hunter API",
    description="Intelligent Academic Journal Discovery, Search & Verification System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(search_router)
app.include_router(articles_router)



@app.get("/api/models")
async def get_models():
    """Get list of 15 supported AI models and provider status."""
    from .services.ai_service import SUPPORTED_MODELS
    return {
        "default_model": settings.default_model,
        "models": SUPPORTED_MODELS,
        "active_gemini_keys": len(settings.gemini_keys),
        "ai_provider": settings.ai_provider,
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from .adapters.crossref import CrossrefAdapter
    from .adapters.openalex import OpenAlexAdapter
    from .adapters.semantic_scholar import SemanticScholarAdapter
    from .adapters.doaj import DOAJAdapter
    from .adapters.scopus import ScopusAdapter
    from .adapters.europe_pmc import EuropePMCAdapter
    from .adapters.arxiv import ArxivAdapter

    adapters = [
        CrossrefAdapter(), OpenAlexAdapter(), SemanticScholarAdapter(),
        DOAJAdapter(), ScopusAdapter(), EuropePMCAdapter(), ArxivAdapter()
    ]
    available = [a.name for a in adapters if a.is_available]

    return {
        "status": "ok",
        "version": "1.0.0",
        "database": "connected",
        "ai_provider": settings.ai_provider,
        "available_sources": available,
    }


@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    from .core.database import SessionLocal
    from .models.models import Search, Article, Journal, ArticleBookmark
    db = SessionLocal()
    try:
        return {
            "total_searches": db.query(Search).count(),
            "total_articles": db.query(Article).count(),
            "total_journals": db.query(Journal).count(),
            "total_bookmarks": db.query(ArticleBookmark).count(),
            "open_access_articles": db.query(Article).filter(Article.is_open_access == True).count(),
        }
    finally:
        db.close()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
