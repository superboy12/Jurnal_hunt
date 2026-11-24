"""arXiv search adapter for open access computer science, math, and AI preprints/papers."""
from __future__ import annotations
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
import httpx

from .base import SearchAdapter, RawArticle

logger = logging.getLogger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivAdapter(SearchAdapter):
    """Adapter for arXiv Open Access API."""

    name: str = "arxiv"
    display_name: str = "arXiv"
    base_url: str = "https://export.arxiv.org/api/query"

    async def search(
        self,
        keywords: List[str],
        synonyms: List[str],
        year_from: Optional[int],
        year_to: Optional[int],
        max_results: int = 25,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[RawArticle]:
        extra_params = extra_params or {}
        search_terms = " ".join(keywords) if keywords else ""
        if not search_terms:
            return []

        clean_query = re.sub(r"[^\w\s]", "", search_terms).strip()
        formatted_terms = "+AND+".join(f"all:{w}" for w in clean_query.split())

        params: Dict[str, Any] = {
            "search_query": formatted_terms,
            "start": 0,
            "max_results": min(max_results, 30),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        headers = {
            "User-Agent": "JournalHunter/1.0 (academic research aggregator; mailto:user@journalhunter.app)"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    logger.info(f"arXiv API returned status {resp.status_code}")
                    return []

                root = ET.fromstring(resp.text)
                entries = root.findall("atom:entry", ATOM_NS)
                articles: List[RawArticle] = []

                for entry in entries:
                    art = self._parse_entry(entry, year_from, year_to)
                    if art:
                        articles.append(art)

                return articles
        except Exception as e:
            logger.info(f"arXiv search handled: {e}")
            return []

    def _parse_entry(
        self,
        entry: ET.Element,
        year_from: Optional[int],
        year_to: Optional[int],
    ) -> Optional[RawArticle]:
        title_elem = entry.find("atom:title", ATOM_NS)
        if title_elem is None or not title_elem.text:
            return None

        title = " ".join(title_elem.text.split()).strip()

        # Published date & year
        published_elem = entry.find("atom:published", ATOM_NS)
        year = None
        pub_date = None
        if published_elem is not None and published_elem.text:
            pub_date = published_elem.text[:10]
            try:
                year = int(pub_date[:4])
            except ValueError:
                pass

        # Filter year if specified
        if year:
            if year_from and year < year_from:
                return None
            if year_to and year > year_to:
                return None

        # Abstract / summary
        summary_elem = entry.find("atom:summary", ATOM_NS)
        abstract = " ".join(summary_elem.text.split()).strip() if summary_elem is not None and summary_elem.text else None

        # Authors
        authors = []
        for a_elem in entry.findall("atom:author", ATOM_NS):
            name_elem = a_elem.find("atom:name", ATOM_NS)
            if name_elem is not None and name_elem.text:
                authors.append({"name": name_elem.text.strip(), "affiliation": None, "orcid": None})

        # Links (PDF & HTML)
        id_elem = entry.find("atom:id", ATOM_NS)
        article_url = id_elem.text.strip() if id_elem is not None and id_elem.text else None
        pdf_url = None

        for link in entry.findall("atom:link", ATOM_NS):
            if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                pdf_url = link.get("href")

        if not pdf_url and article_url and "arxiv.org/abs/" in article_url:
            pdf_url = article_url.replace("/abs/", "/pdf/") + ".pdf"

        # DOI if available
        doi = None
        doi_elem = entry.find("arxiv:doi", ATOM_NS)
        if doi_elem is not None and doi_elem.text:
            doi = self.normalize_doi(doi_elem.text.strip())

        # Journal ref
        journal_ref = entry.find("arxiv:journal_ref", ATOM_NS)
        journal_name = journal_ref.text.strip() if journal_ref is not None and journal_ref.text else "arXiv"

        return RawArticle(
            title=title,
            source=self.name,
            doi=doi,
            abstract=abstract,
            year=year,
            publication_date=pub_date,
            journal_name=journal_name,
            publisher="arXiv.org / Cornell University",
            keywords=[],
            authors=authors,
            is_open_access=True,
            open_access_url=article_url,
            pdf_url=pdf_url,
            article_url=article_url,
            source_id=article_url,
            raw={},
        )
