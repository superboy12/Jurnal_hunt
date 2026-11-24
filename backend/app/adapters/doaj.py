"""DOAJ (Directory of Open Access Journals) API adapter."""
from __future__ import annotations
import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from .base import SearchAdapter, RawArticle

import urllib.parse

logger = logging.getLogger(__name__)

DOAJ_ARTICLES_API = "https://doaj.org/api/search/articles"
DOAJ_JOURNALS_API = "https://doaj.org/api/search/journals"


class DOAJAdapter(SearchAdapter):
    name = "doaj"
    display_name = "DOAJ"
    base_url = DOAJ_ARTICLES_API

    async def search(
        self,
        keywords: List[str],
        synonyms: List[str],
        year_from: Optional[int],
        year_to: Optional[int],
        max_results: int,
        extra_params: Dict[str, Any],
    ) -> List[RawArticle]:
        query_parts = keywords[:5]
        query = " OR ".join(f'"{kw}"' if " " in kw else kw for kw in query_parts)

        if year_from or year_to:
            yf = year_from or 1900
            yt = year_to or 2100
            query += f" AND bibjson.year:[{yf} TO {yt}]"

        params: Dict[str, Any] = {
            "pageSize": min(max_results, 100),
            "page": 1,
        }

        url = f"{DOAJ_ARTICLES_API}/{urllib.parse.quote(query, safe='')}"

        articles = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    for item in data.get("results", []):
                        article = self._parse_article(item)
                        if article:
                            articles.append(article)
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        logger.error(f"DOAJ HTTP error: {e}")
                        break
                except Exception as e:
                    logger.error(f"DOAJ error (attempt {attempt+1}): {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)

        return articles

    def _parse_article(self, item: Dict) -> Optional[RawArticle]:
        bib = item.get("bibjson") or {}
        title = bib.get("title")
        if not title:
            return None

        # DOI
        doi = None
        for id_item in bib.get("identifier", []):
            if id_item.get("type") == "doi":
                doi = self.normalize_doi(id_item.get("id"))
                break

        # Year
        year = None
        try:
            year = int(bib.get("year", "")) if bib.get("year") else None
        except ValueError:
            pass

        # Journal info
        journal_info = bib.get("journal") or {}
        journal_name = journal_info.get("title")
        issn = None
        for id_item in journal_info.get("identifier", []):
            if id_item.get("type") == "pissn":
                issn = id_item.get("id")
                break

        # Authors
        authors = []
        for i, auth in enumerate(bib.get("author", [])):
            name = auth.get("name", "")
            if name:
                authors.append({
                    "name": name,
                    "affiliation": auth.get("affiliation"),
                    "orcid": None,
                    "order": i,
                })

        # Abstract
        abstract = None
        abstracts = bib.get("abstract", [])
        if isinstance(abstracts, str):
            abstract = abstracts
        elif isinstance(abstracts, list) and abstracts:
            abstract = abstracts[0].get("text") if isinstance(abstracts[0], dict) else abstracts[0]

        # Keywords
        keywords = bib.get("keywords", [])

        # Links
        article_url = None
        pdf_url = None
        for link in bib.get("link", []):
            link_type = link.get("type", "")
            if link_type == "fulltext":
                article_url = link.get("url")
            elif link_type == "pdf":
                pdf_url = link.get("url")

        # Volume/Issue/Pages
        volume = journal_info.get("volume")
        issue = journal_info.get("number")
        pages = bib.get("start_page", "")
        if bib.get("end_page"):
            pages = f"{pages}-{bib['end_page']}"

        return RawArticle(
            title=title,
            source=self.name,
            doi=doi,
            abstract=abstract,
            year=year,
            journal_name=journal_name,
            volume=str(volume) if volume else None,
            issue=str(issue) if issue else None,
            pages=pages or None,
            keywords=keywords,
            authors=authors,
            is_open_access=True,  # DOAJ is always open access
            article_url=article_url,
            pdf_url=pdf_url,
            issn=issn,
            source_id=item.get("id"),
            raw=item,
        )
