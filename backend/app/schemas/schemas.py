"""Pydantic schemas for request/response validation."""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────

class SearchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VerificationStatus(str, Enum):
    VERIFIED_SCOPUS = "verified_scopus"
    VERIFIED_SINTA = "verified_sinta"
    VERIFIED_BOTH = "verified_both"
    NOT_VERIFIED = "not_verified"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"
    PENDING = "pending"


class ArticleStatus(str, Enum):
    WANT_TO_READ = "want_to_read"
    READ = "read"
    CANDIDATE = "candidate"
    NOT_RELEVANT = "not_relevant"


class PublicationType(str, Enum):
    JOURNAL = "journal"
    CONFERENCE = "conference"
    REVIEW = "review"
    COMMUNITY_SERVICE = "community_service"
    OTHER = "other"


# ── Search ─────────────────────────────────────────────────────────────

class SearchCommandRequest(BaseModel):
    command: str = Field(..., min_length=3, max_length=2000, description="Natural language search command")
    preset: Optional[str] = Field(None, description="Search preset: scopus_only, sinta_only, open_access, etc.")
    presets: Optional[List[str]] = Field(None, description="Multiple search presets selected by user")


class SearchParameterSchema(BaseModel):
    topic: Optional[str] = None
    keywords: List[str] = []
    synonyms: List[str] = []
    language: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    max_results: int = 50
    indexing_target: Optional[str] = None   # scopus, sinta, both, any
    sinta_rank_min: Optional[int] = None
    sinta_rank_max: Optional[int] = None
    publication_type: Optional[str] = None
    selected_categories: Optional[List[str]] = None
    open_access_only: bool = False
    require_doi: bool = False
    require_pdf: bool = False
    max_apc: Optional[float] = None
    sources: List[str] = ["crossref", "openalex", "semantic_scholar", "doaj"]
    extra_params: Dict[str, Any] = {}


class StartSearchRequest(BaseModel):
    command: str
    parameters: SearchParameterSchema


class SearchSourceLogSchema(BaseModel):
    source_name: str
    status: str
    articles_found: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request_count: int = 0

    class Config:
        from_attributes = True


class SearchSummarySchema(BaseModel):
    id: str
    user_command: str
    status: SearchStatus
    total_found: int
    total_after_dedup: int
    total_verified: int
    total_open_access: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    source_logs: List[SearchSourceLogSchema] = []

    class Config:
        from_attributes = True


# ── Article ────────────────────────────────────────────────────────────

class AuthorSchema(BaseModel):
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    order: int = 0

    class Config:
        from_attributes = True


class ArticleSchema(BaseModel):
    id: str
    doi: Optional[str] = None
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    publication_date: Optional[str] = None
    journal_name: Optional[str] = None
    publisher: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    language: Optional[str] = None
    keywords: List[str] = []
    publication_type: Optional[str] = None
    is_open_access: Optional[bool] = None
    open_access_url: Optional[str] = None
    pdf_url: Optional[str] = None
    article_url: Optional[str] = None
    sci_hub_url: Optional[str] = None
    citation_count: Optional[int] = None
    subject_category: Optional[str] = None
    sources: List[str] = []
    verification_status: Optional[VerificationStatus] = None
    authors: List[AuthorSchema] = []

    class Config:
        from_attributes = True


class SearchArticleSchema(BaseModel):
    article: ArticleSchema
    relevance_score: float
    relevance_reason: Optional[str] = None
    rank: Optional[int] = None
    source_found_in: List[str] = []
    # Journal verification info (joined)
    sinta_rank: Optional[int] = None
    is_scopus: Optional[bool] = None
    scimago_quartile: Optional[str] = None
    sjr_score: Optional[float] = None
    scimago_url: Optional[str] = None
    sci_hub_url: Optional[str] = None
    subject_category: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedArticles(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: List[SearchArticleSchema]
    available_categories: List[str] = []
    category_counts: Dict[str, int] = {}


# ── Journal ────────────────────────────────────────────────────────────

class JournalSchema(BaseModel):
    id: str
    name: str
    issn: Optional[str] = None
    eissn: Optional[str] = None
    publisher: Optional[str] = None
    is_scopus_indexed: Optional[bool] = None
    scopus_coverage_start: Optional[int] = None
    scopus_coverage_end: Optional[int] = None
    sinta_rank: Optional[int] = None
    sinta_id: Optional[str] = None
    sinta_profile_url: Optional[str] = None
    scopus_source_url: Optional[str] = None
    scimago_quartile: Optional[str] = None
    sjr_score: Optional[float] = None
    scimago_url: Optional[str] = None
    h_index: Optional[int] = None
    doaj_url: Optional[str] = None
    is_open_access: Optional[bool] = None
    apc_amount: Optional[float] = None
    apc_currency: Optional[str] = None
    verification_source: Optional[str] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Bookmark ───────────────────────────────────────────────────────────

class BookmarkCreate(BaseModel):
    article_id: str
    project_id: Optional[str] = None
    status: ArticleStatus = ArticleStatus.WANT_TO_READ
    notes: Optional[str] = None


class BookmarkUpdate(BaseModel):
    status: Optional[ArticleStatus] = None
    notes: Optional[str] = None
    project_id: Optional[str] = None


class BookmarkSchema(BaseModel):
    id: str
    article_id: str
    project_id: Optional[str] = None
    status: ArticleStatus
    notes: Optional[str] = None
    created_at: datetime
    article: Optional[ArticleSchema] = None

    class Config:
        from_attributes = True


# ── Research Project ───────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class ProjectSchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Command Interpretation ─────────────────────────────────────────────

class InterpretedCommand(BaseModel):
    topic: str
    keywords: List[str]
    synonyms: List[str]
    language: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    max_results: int = 50
    indexing_target: Optional[str] = None
    sinta_rank_min: Optional[int] = None
    sinta_rank_max: Optional[int] = None
    publication_type: Optional[str] = None
    open_access_only: bool = False
    require_doi: bool = False
    require_pdf: bool = False
    max_apc: Optional[float] = None
    sources: List[str] = ["crossref", "openalex", "semantic_scholar", "doaj"]
    interpretation_notes: str = ""


# ── Health ─────────────────────────────────────────────────────────────

class HealthCheck(BaseModel):
    status: str
    version: str
    database: str
    ai_provider: str
    available_sources: List[str]


