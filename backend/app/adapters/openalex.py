"""OpenAlex API adapter."""
from __future__ import annotations
import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from .base import SearchAdapter, RawArticle

logger = logging.getLogger(__name__)

OPENALEX_API = "https://api.openalex.org/works"


class OpenAlexAdapter(SearchAdapter):
    name = "openalex"
    display_name = "OpenAlex"
    base_url = OPENALEX_API

    async def search(
        self,
        keywords: List[str],
        synonyms: List[str],
        year_from: Optional[int],
        year_to: Optional[int],
        max_results: int,
        extra_params: Dict[str, Any],
    ) -> List[RawArticle]:
        query_terms = []
        for kw in keywords[:5]:
            kw_clean = kw.strip().strip('"')
            if kw_clean and kw_clean.lower() not in [q.lower() for q in query_terms]:
                query_terms.append(kw_clean)

        query = " ".join(query_terms)
        if synonyms:
            for s in synonyms[:2]:
                s_clean = s.strip().strip('"')
                if s_clean and s_clean.lower() not in query.lower():
                    query += f" {s_clean}"

        filters = []
        if year_from and year_to:
            filters.append(f"publication_year:{year_from}-{year_to}")
        elif year_from:
            filters.append(f"publication_year:>{year_from - 1}")
        elif year_to:
            filters.append(f"publication_year:<{year_to + 1}")

        if extra_params.get("open_access_only"):
            filters.append("is_oa:true")

        params: Dict[str, Any] = {
            "search": query,
            "per_page": min(max_results, 200),
            "select": "id,title,doi,abstract_inverted_index,authorships,publication_year,publication_date,primary_location,best_oa_location,open_access,cited_by_count,keywords,type",
            "mailto": "user@journalhunter.app",
        }

        if filters:
            params["filter"] = ",".join(filters)

        articles = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    resp = await client.get(OPENALEX_API, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    for item in data.get("results", []):
                        article = self._parse_item(item)
                        if article:
                            articles.append(article)
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        logger.error(f"OpenAlex HTTP error: {e}")
                        break
                except Exception as e:
                    logger.error(f"OpenAlex error (attempt {attempt+1}): {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)

        return articles

    def _decode_abstract(self, inverted_index: Optional[Dict]) -> Optional[str]:
        """Reconstruct abstract from OpenAlex inverted index."""
        if not inverted_index:
            return None
        positions = []
        for word, pos_list in inverted_index.items():
            for pos in pos_list:
                positions.append((pos, word))
        positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in positions)

    def _parse_item(self, item: Dict) -> Optional[RawArticle]:
        title = item.get("title")
        if not title:
            return None

        doi = self.normalize_doi(item.get("doi"))

        # Abstract
        abstract = self._decode_abstract(item.get("abstract_inverted_index"))

        # Year
        year = item.get("publication_year")

        # Primary location (journal)
        journal_name = None
        issn = None
        eissn = None
        publisher = None
        article_url = None

        loc = item.get("primary_location") or {}
        source = loc.get("source") or {}
        if source:
            journal_name = source.get("display_name")
            issns = source.get("issn", []) or []
            issn = issns[0] if issns else None
            eissn = source.get("issn_l")
            publisher = source.get("host_organization_name")
        article_url = loc.get("landing_page_url")

        # Open access
        oa = item.get("open_access") or {}
        is_open_access = oa.get("is_oa")
        open_access_url = oa.get("oa_url")

        # Best OA location for PDF
        best_oa = item.get("best_oa_location") or {}
        pdf_url = best_oa.get("pdf_url")

        # Authors
        authors = []
        for i, authorship in enumerate(item.get("authorships", [])):
            author = authorship.get("author") or {}
            name = author.get("display_name", "")
            if name:
                inst = (authorship.get("institutions") or [{}])[0]
                authors.append({
                    "name": name,
                    "affiliation": inst.get("display_name") if inst else None,
                    "orcid": author.get("orcid"),
                    "order": i,
                })

        # Keywords
        keywords = [k.get("display_name", "") for k in (item.get("keywords") or [])]

        # Type
        pub_type = item.get("type", "journal-article")

        return RawArticle(
            title=title,
            source=self.name,
            doi=doi,
            abstract=abstract,
            year=year,
            publication_date=item.get("publication_date"),
            journal_name=journal_name,
            publisher=publisher,
            language=None,
            keywords=keywords,
            authors=authors,
            is_open_access=is_open_access,
            open_access_url=open_access_url,
            pdf_url=pdf_url,
            article_url=article_url,
            citation_count=item.get("cited_by_count"),
            issn=issn,
            eissn=eissn,
            source_id=item.get("id"),
            raw=item,
        )
