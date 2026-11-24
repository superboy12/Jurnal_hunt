"""Semantic Scholar API adapter."""
from __future__ import annotations
import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from .base import SearchAdapter, RawArticle
from ..core.config import settings

logger = logging.getLogger(__name__)

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"


class SemanticScholarAdapter(SearchAdapter):
    name = "semantic_scholar"
    display_name = "Semantic Scholar"
    base_url = S2_API

    FIELDS = "paperId,title,abstract,year,publicationDate,journal,externalIds,authors,isOpenAccess,openAccessPdf,publicationTypes,fieldsOfStudy,citationCount"

    async def search(
        self,
        keywords: List[str],
        synonyms: List[str],
        year_from: Optional[int],
        year_to: Optional[int],
        max_results: int,
        extra_params: Dict[str, Any],
    ) -> List[RawArticle]:
        query = " ".join(keywords[:5])

        params: Dict[str, Any] = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": self.FIELDS,
        }

        if year_from or year_to:
            yf = year_from or 1900
            yt = year_to or 2100
            params["year"] = f"{yf}-{yt}"

        headers: Dict[str, str] = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key

        articles = []
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            for attempt in range(self.max_retries):
                try:
                    resp = await client.get(S2_API, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    for item in data.get("data", []):
                        article = self._parse_item(item)
                        if article:
                            articles.append(article)
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        if not settings.semantic_scholar_api_key:
                            logger.info("Semantic Scholar unauthenticated rate limit reached, skipping.")
                            break
                        wait = 2 ** (attempt + 1)
                        logger.warning(f"Semantic Scholar rate limited, waiting {wait}s")
                        await asyncio.sleep(wait)
                    else:
                        logger.error(f"Semantic Scholar HTTP error: {e}")
                        break
                except Exception as e:
                    logger.error(f"Semantic Scholar error (attempt {attempt+1}): {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)

        return articles

    def _parse_item(self, item: Dict) -> Optional[RawArticle]:
        title = item.get("title")
        if not title:
            return None

        ext_ids = item.get("externalIds") or {}
        doi = self.normalize_doi(ext_ids.get("DOI"))

        journal_info = item.get("journal") or {}
        journal_name = journal_info.get("name")
        volume = journal_info.get("volume")
        pages = journal_info.get("pages")

        authors = []
        for i, auth in enumerate(item.get("authors") or []):
            name = auth.get("name", "")
            if name:
                authors.append({
                    "name": name,
                    "affiliation": None,
                    "orcid": None,
                    "order": i,
                })

        oa_pdf = item.get("openAccessPdf") or {}
        pdf_url = oa_pdf.get("url")
        is_oa = item.get("isOpenAccess")

        pub_types = item.get("publicationTypes") or []

        return RawArticle(
            title=title,
            source=self.name,
            doi=doi,
            abstract=item.get("abstract"),
            year=item.get("year"),
            publication_date=item.get("publicationDate"),
            journal_name=journal_name,
            volume=volume,
            pages=pages,
            keywords=item.get("fieldsOfStudy") or [],
            authors=authors,
            is_open_access=is_oa,
            pdf_url=pdf_url,
            citation_count=item.get("citationCount"),
            source_id=item.get("paperId"),
            raw=item,
        )
