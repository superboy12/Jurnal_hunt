"""SQLAlchemy ORM models for AI Journal Hunter."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


# ── Enums ──────────────────────────────────────────────────────────────

class SearchStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VerificationStatus(str, enum.Enum):
    VERIFIED_SCOPUS = "verified_scopus"
    VERIFIED_SINTA = "verified_sinta"
    VERIFIED_BOTH = "verified_both"
    NOT_VERIFIED = "not_verified"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"
    PENDING = "pending"


class ArticleStatus(str, enum.Enum):
    WANT_TO_READ = "want_to_read"
    READ = "read"
    CANDIDATE = "candidate"
    NOT_RELEVANT = "not_relevant"


class PublicationType(str, enum.Enum):
    JOURNAL = "journal"
    CONFERENCE = "conference"
    REVIEW = "review"
    COMMUNITY_SERVICE = "community_service"
    OTHER = "other"


# ── Models ─────────────────────────────────────────────────────────────


class Search(Base):
    __tablename__ = "searches"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_command = Column(Text, nullable=False)
    status = Column(SQLEnum(SearchStatus), default=SearchStatus.PENDING, nullable=False)
    total_found = Column(Integer, default=0)
    total_after_dedup = Column(Integer, default=0)
    total_verified = Column(Integer, default=0)
    total_open_access = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    parameters = relationship("SearchParameter", back_populates="search", uselist=False, cascade="all, delete-orphan")
    source_logs = relationship("SearchSourceLog", back_populates="search", cascade="all, delete-orphan")
    articles = relationship("SearchArticle", back_populates="search", cascade="all, delete-orphan")


class SearchParameter(Base):
    __tablename__ = "search_parameters"

    id = Column(String, primary_key=True, default=gen_uuid)
    search_id = Column(String, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    topic = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)   # List[str]
    synonyms = Column(JSON, default=list)   # List[str]
    language = Column(String, nullable=True)
    year_from = Column(Integer, nullable=True)
    year_to = Column(Integer, nullable=True)
    max_results = Column(Integer, default=50)
    indexing_target = Column(String, nullable=True)  # scopus, sinta, both, any
    sinta_rank_min = Column(Integer, nullable=True)
    sinta_rank_max = Column(Integer, nullable=True)
    publication_type = Column(String, nullable=True)
    open_access_only = Column(Boolean, default=False)
    require_doi = Column(Boolean, default=False)
    require_pdf = Column(Boolean, default=False)
    max_apc = Column(Float, nullable=True)
    sources = Column(JSON, default=list)    # List[str] - selected sources
    extra_params = Column(JSON, default=dict)

    search = relationship("Search", back_populates="parameters")


class SearchSourceLog(Base):
    __tablename__ = "search_source_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    search_id = Column(String, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String, nullable=False)   # crossref, openalex, semantic_scholar, doaj, scopus
    status = Column(String, default="pending")     # pending, running, completed, failed, skipped
    articles_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    request_count = Column(Integer, default=0)

    search = relationship("Search", back_populates="source_logs")


class Journal(Base):
    __tablename__ = "journals"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(Text, nullable=False)
    issn = Column(String, nullable=True)
    eissn = Column(String, nullable=True)
    publisher = Column(Text, nullable=True)
    is_scopus_indexed = Column(Boolean, nullable=True)
    scopus_coverage_start = Column(Integer, nullable=True)
    scopus_coverage_end = Column(Integer, nullable=True)
    sinta_rank = Column(Integer, nullable=True)      # 1-6
    sinta_id = Column(String, nullable=True)
    sinta_profile_url = Column(String, nullable=True)
    scopus_source_url = Column(String, nullable=True)
    scimago_quartile = Column(String, nullable=True)   # Q1, Q2, Q3, Q4
    sjr_score = Column(Float, nullable=True)           # e.g. 0.926, 1.87
    scimago_url = Column(String, nullable=True)         # https://www.scimagojr.com/...
    h_index = Column(Integer, nullable=True)           # e.g. 45
    doaj_url = Column(String, nullable=True)
    is_open_access = Column(Boolean, nullable=True)
    apc_amount = Column(Float, nullable=True)
    apc_currency = Column(String, nullable=True)
    verification_source = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_journals_issn", "issn"),
        Index("ix_journals_eissn", "eissn"),
    )

    articles = relationship("Article", back_populates="journal")


class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=gen_uuid)
    doi = Column(String, nullable=True, unique=True, index=True)
    title = Column(Text, nullable=False)
    title_normalized = Column(Text, nullable=True, index=True)
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True, index=True)
    publication_date = Column(String, nullable=True)
    journal_id = Column(String, ForeignKey("journals.id"), nullable=True)
    journal_name = Column(Text, nullable=True)
    publisher = Column(Text, nullable=True)
    volume = Column(String, nullable=True)
    issue = Column(String, nullable=True)
    pages = Column(String, nullable=True)
    language = Column(String, nullable=True)
    keywords = Column(JSON, default=list)
    publication_type = Column(SQLEnum(PublicationType), default=PublicationType.JOURNAL)
    is_open_access = Column(Boolean, nullable=True)
    open_access_url = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    article_url = Column(String, nullable=True)
    citation_count = Column(Integer, nullable=True)
    subject_category = Column(String, nullable=True, index=True)  # e.g. "Cyber Security", "Hukum", "Kesehatan"
    sources = Column(JSON, default=list)   # List[str] - which APIs returned this
    source_ids = Column(JSON, default=dict) # {"crossref": "doi", "openalex": "W12345"}
    raw_metadata = Column(JSON, default=dict)
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    journal = relationship("Journal", back_populates="articles")
    authors = relationship("ArticleAuthor", back_populates="article", cascade="all, delete-orphan")
    search_articles = relationship("SearchArticle", back_populates="article")
    bookmarks = relationship("ArticleBookmark", back_populates="article", cascade="all, delete-orphan")


class ArticleAuthor(Base):
    __tablename__ = "article_authors"

    id = Column(String, primary_key=True, default=gen_uuid)
    article_id = Column(String, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    affiliation = Column(Text, nullable=True)
    orcid = Column(String, nullable=True)
    order = Column(Integer, default=0)

    article = relationship("Article", back_populates="authors")


class SearchArticle(Base):
    """Junction table: which articles belong to which search, with relevance score."""
    __tablename__ = "search_articles"

    id = Column(String, primary_key=True, default=gen_uuid)
    search_id = Column(String, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(String, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    relevance_score = Column(Float, default=0.0)
    relevance_reason = Column(Text, nullable=True)
    rank = Column(Integer, nullable=True)
    source_found_in = Column(JSON, default=list)

    __table_args__ = (
        UniqueConstraint("search_id", "article_id", name="uq_search_article"),
    )

    search = relationship("Search", back_populates="articles")
    article = relationship("Article", back_populates="search_articles")


class IndexingVerification(Base):
    __tablename__ = "indexing_verifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    journal_id = Column(String, ForeignKey("journals.id"), nullable=True)
    issn = Column(String, nullable=True)
    journal_name = Column(Text, nullable=True)
    verification_type = Column(String, nullable=False)  # scopus, sinta
    status = Column(String, nullable=False)             # verified, not_verified, unavailable
    sinta_rank = Column(Integer, nullable=True)
    scopus_source_id = Column(String, nullable=True)
    coverage_start = Column(Integer, nullable=True)
    coverage_end = Column(Integer, nullable=True)
    profile_url = Column(String, nullable=True)
    verification_source = Column(String, nullable=True)  # API name or "manual"
    notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), default=utcnow)


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    bookmarks = relationship("ArticleBookmark", back_populates="project")


class ArticleBookmark(Base):
    __tablename__ = "article_bookmarks"

    id = Column(String, primary_key=True, default=gen_uuid)
    article_id = Column(String, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("research_projects.id"), nullable=True)
    status = Column(SQLEnum(ArticleStatus), default=ArticleStatus.WANT_TO_READ)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    article = relationship("Article", back_populates="bookmarks")
    project = relationship("ResearchProject", back_populates="bookmarks")

    __table_args__ = (
        UniqueConstraint("article_id", "project_id", name="uq_bookmark_article_project"),
    )

