"""Scopus API adapter (requires API key from Elsevier)."""
from __future__ import annotations
import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from .base import SearchAdapter, RawArticle
from ..core.config import settings

logger = logging.getLogger(__name__)

SCOPUS_SEARCH_API = "https://api.elsevier.com/content/search/scopus"
SCOPUS_SOURCES_URL = "https://www.scopus.com/sources"


class ScopusAdapter(SearchAdapter):
    name = "scopus"
    display_name = "Scopus"
    base_url = SCOPUS_SEARCH_API

    @property
    def is_available(self) -> bool:
        return bool(settings.scopus_api_key)

    @property
    def requires_api_key(self) -> bool:
        return True

    async def search(
        self,
        keywords: List[str],
        synonyms: List[str],
        year_from: Optional[int],
        year_to: Optional[int],
        max_results: int,
        extra_params: Dict[str, Any],
    ) -> List[RawArticle]:
        if not self.is_available:
            logger.info("Scopus API key not configured, skipping Scopus search")
            return []

        kw_str = " AND ".join(f'TITLE-ABS-KEY("{kw}")' if " " in kw else f"TITLE-ABS-KEY({kw})" for kw in keywords[:5])
        query = kw_str

        if year_from or year_to:
            yf = year_from or 1900
            yt = year_to or 2030
            query += f" AND PUBYEAR > {yf - 1} AND PUBYEAR < {yt + 1}"

        params: Dict[str, Any] = {
            "query": query,
            "count": min(max_results, 200),
            "field": "dc:title,dc:creator,prism:doi,prism:publicationName,prism:issn,prism:eIssn,prism:coverDate,prism:volume,prism:issueIdentifier,prism:pageRange,citedby-count,dc:description,openaccess,openaccessFlag,prism:url",
            "httpAccept": "application/json",
        }

        headers = {
            "X-ELS-APIKey": settings.scopus_api_key,
        }
        if settings.scopus_inst_token:
            headers["X-ELS-Insttoken"] = settings.scopus_inst_token

        articles = []
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            for attempt in range(self.max_retries):
                try:
                    resp = await client.get(SCOPUS_SEARCH_API, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    entries = data.get("search-results", {}).get("entry", [])
                    for entry in entries:
                        article = self._parse_entry(entry)
                        if article:
                            articles.append(article)
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                    elif e.response.status_code == 401:
                        logger.error("Scopus: Invalid API key or insufficient access")
                        break
                    else:
                        logger.error(f"Scopus HTTP error: {e}")
                        break
                except Exception as e:
                    logger.error(f"Scopus error (attempt {attempt+1}): {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)

        return articles

    def _parse_entry(self, entry: Dict) -> Optional[RawArticle]:
        title = entry.get("dc:title")
        if not title:
            return None

        doi = self.normalize_doi(entry.get("prism:doi"))

        authors = []
        creator = entry.get("dc:creator")
        if creator:
            authors.append({"name": creator, "affiliation": None, "orcid": None, "order": 0})

        year = None
        cover_date = entry.get("prism:coverDate", "")
        if cover_date and len(cover_date) >= 4:
            try:
                year = int(cover_date[:4])
            except ValueError:
                pass

        is_oa = entry.get("openaccess") == "1" or entry.get("openaccessFlag") == "true"

        return RawArticle(
            title=title,
            source=self.name,
            doi=doi,
            year=year,
            publication_date=cover_date,
            journal_name=entry.get("prism:publicationName"),
            volume=entry.get("prism:volume"),
            issue=entry.get("prism:issueIdentifier"),
            pages=entry.get("prism:pageRange"),
            authors=authors,
            is_open_access=is_oa,
            article_url=entry.get("prism:url"),
            citation_count=int(entry.get("citedby-count", 0) or 0),
            issn=entry.get("prism:issn"),
            eissn=entry.get("prism:eIssn"),
            source_id=entry.get("dc:identifier"),
            raw=entry,
        )
