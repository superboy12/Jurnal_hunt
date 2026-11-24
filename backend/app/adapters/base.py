"""Base adapter interface for academic search sources."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import unicodedata
import re


@dataclass
class RawArticle:
    """Normalized article data from any source adapter."""
    title: str
    source: str  # adapter name
    doi: Optional[str] = None
    abstract: Optional[str] = None
    year: Optional[int] = None
    publication_date: Optional[str] = None
    journal_name: Optional[str] = None
    publisher: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    language: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    authors: List[Dict[str, Any]] = field(default_factory=list)  # [{name, affiliation, orcid}]
    is_open_access: Optional[bool] = None
    open_access_url: Optional[str] = None
    pdf_url: Optional[str] = None
    article_url: Optional[str] = None
    citation_count: Optional[int] = None
    issn: Optional[str] = None
    eissn: Optional[str] = None
    source_id: Optional[str] = None  # ID in the source system
    raw: Dict[str, Any] = field(default_factory=dict)


class SearchAdapter(ABC):
    """Abstract base class for all academic search adapters."""

    name: str = "base"
    display_name: str = "Base Adapter"
    base_url: str = ""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def search(
        self,
        keywords: List[str],
        synonyms: List[str],
        year_from: Optional[int],
        year_to: Optional[int],
        max_results: int,
        extra_params: Dict[str, Any],
    ) -> List[RawArticle]:
        """Execute a search and return normalized articles."""
        ...

    @property
    def is_available(self) -> bool:
        """Return True if this adapter can be used (API key configured if needed)."""
        return True

    @property
    def requires_api_key(self) -> bool:
        return False

    def normalize_doi(self, doi: Optional[str]) -> Optional[str]:
        """Normalize DOI to lowercase without URL prefix."""
        if not doi:
            return None
        doi = doi.strip()
        doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
        doi = doi.strip("/").lower()
        return doi if doi else None

    def normalize_title(self, title: str) -> str:
        """Normalize title for deduplication."""
        if not title:
            return ""
        title = unicodedata.normalize("NFKD", title.lower())
        title = re.sub(r"[^\w\s]", " ", title)
        title = re.sub(r"\s+", " ", title).strip()
        return title
