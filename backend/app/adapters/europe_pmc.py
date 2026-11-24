"""Europe PMC search adapter: Access 40M+ life science & general scientific articles."""
from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any
import httpx

from .base import SearchAdapter, RawArticle

logger = logging.getLogger(__name__)


class EuropePMCAdapter(SearchAdapter):
    """Adapter for Europe PMC (EBI) Open Access REST API."""

    name: str = "europe_pmc"
    display_name: str = "Europe PMC"
    base_url: str = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    async def search(
        self,
        keywords: List[str],
        synonyms: List[str],
        year_from: Optional[int],
        year_to: Optional[int],
        max_results: int = 50,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[RawArticle]:
        extra_params = extra_params or {}
        search_terms = " ".join(keywords) if keywords else ""
        if not search_terms:
            return []

        # Construct query query string
        query_parts = [search_terms]
        if year_from and year_to:
            query_parts.append(f"(PUB_YEAR:[{year_from} TO {year_to}])")
        elif year_from:
            query_parts.append(f"(PUB_YEAR:[{year_from} TO 2026])")

        query = " AND ".join(query_parts)

        params: Dict[str, Any] = {
            "query": query,
            "format": "json",
            "pageSize": min(max_results, 50),
            "resultType": "core",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Europe PMC returned status {resp.status_code}")
                    return []

                data = resp.json()
                results = data.get("resultList", {}).get("result", [])
                articles: List[RawArticle] = []

                for item in results:
                    art = self._parse_article(item)
                    if art:
                        articles.append(art)

                return articles
        except Exception as e:
            logger.warning(f"Europe PMC search failed: {e}")
            return []

    def _parse_article(self, item: Dict[str, Any]) -> Optional[RawArticle]:
        title = item.get("title", "").strip().rstrip(".")
        if not title:
            return None

        doi = self.normalize_doi(item.get("doi"))
        year_str = item.get("pubYear")
        year = None
        if year_str:
            try:
                year = int(year_str)
            except ValueError:
                pass

        # Authors
        authors = []
        author_string = item.get("authorString", "")
        if author_string:
            for a_name in author_string.split(","):
                clean = a_name.strip()
                if clean:
                    authors.append({"name": clean, "affiliation": None, "orcid": None})

        # Open Access & PDF
        is_oa = item.get("isOpenAccess") == "Y"
        pdf_url = None
        article_url = f"https://europepmc.org/article/MED/{item.get('id')}" if item.get("id") else None

        # Check full text URLs
        urls = item.get("fullTextUrlList", {}).get("fullTextUrl", [])
        for u in urls:
            if u.get("documentStyle") == "pdf":
                pdf_url = u.get("url")
            elif not article_url:
                article_url = u.get("url")

        journal_title = item.get("journalTitle") or item.get("journalInfo", {}).get("journal", {}).get("title")

        return RawArticle(
            title=title,
            source=self.name,
            doi=doi,
            abstract=item.get("abstractText"),
            year=year,
            publication_date=item.get("firstPublicationDate"),
            journal_name=journal_title,
            publisher=item.get("journalInfo", {}).get("journal", {}).get("publisher"),
            keywords=[],
            authors=authors,
            is_open_access=is_oa,
            open_access_url=article_url if is_oa else None,
            pdf_url=pdf_url,
            article_url=article_url,
            citation_count=item.get("citedByCount"),
            source_id=item.get("id"),
            raw=item,
        )
