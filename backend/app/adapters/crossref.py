"""Crossref API adapter."""
from __future__ import annotations
import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from .base import SearchAdapter, RawArticle
from ..core.config import settings

logger = logging.getLogger(__name__)

CROSSREF_API = "https://api.crossref.org/works"


class CrossrefAdapter(SearchAdapter):
    name = "crossref"
    display_name = "Crossref"
    base_url = CROSSREF_API

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

        params: Dict[str, Any] = {
            "query": query,
            "rows": min(max_results, 100),
            "select": "DOI,title,author,published-print,published-online,container-title,publisher,ISSN,abstract,is-referenced-by-count,URL,link,subject,type,volume,issue,page",
            "mailto": settings.crossref_email,
        }

        if year_from and year_to:
            params["filter"] = f"from-pub-date:{year_from}-01-01,until-pub-date:{year_to}-12-31"
        elif year_from:
            params["filter"] = f"from-pub-date:{year_from}-01-01"
        elif year_to:
            params["filter"] = f"until-pub-date:{year_to}-12-31"

        articles = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    resp = await client.get(CROSSREF_API, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    items = data.get("message", {}).get("items", [])
                    for item in items:
                        article = self._parse_item(item)
                        if article:
                            articles.append(article)
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        wait = 2 ** attempt
                        logger.warning(f"Crossref rate limited, waiting {wait}s")
                        await asyncio.sleep(wait)
                    else:
                        logger.error(f"Crossref HTTP error: {e}")
                        break
                except Exception as e:
                    logger.error(f"Crossref error (attempt {attempt+1}): {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)

        return articles

    def _parse_item(self, item: Dict) -> Optional[RawArticle]:
        title_list = item.get("title", [])
        if not title_list:
            return None
        title = title_list[0] if isinstance(title_list, list) else title_list

        doi = self.normalize_doi(item.get("DOI"))

        # Year
        year = None
        for date_field in ["published-print", "published-online", "created"]:
            dp = item.get(date_field, {})
            parts = dp.get("date-parts", [[]])
            if parts and parts[0]:
                year = parts[0][0]
                break

        pub_date = None
        for date_field in ["published-print", "published-online"]:
            dp = item.get(date_field, {})
            parts = dp.get("date-parts", [[]])
            if parts and parts[0]:
                p = parts[0]
                pub_date = "-".join(str(x) for x in p)
                break

        # Journal
        ct = item.get("container-title", [])
        journal_name = ct[0] if ct else None

        # ISSN
        issns = item.get("ISSN", [])
        issn = issns[0] if issns else None
        eissn = issns[1] if len(issns) > 1 else None

        # Authors
        authors = []
        for auth in item.get("author", []):
            name = f"{auth.get('given', '')} {auth.get('family', '')}".strip()
            if not name:
                name = auth.get("name", "")
            if name:
                authors.append({
                    "name": name,
                    "affiliation": auth.get("affiliation", [{}])[0].get("name") if auth.get("affiliation") else None,
                    "orcid": auth.get("ORCID"),
                    "order": auth.get("sequence", ""),
                })

        # PDF / URL
        pdf_url = None
        article_url = item.get("URL")
        is_oa = None

        links = item.get("link", []) or []
        for link in links:
            content_type = str(link.get("content-type", "")).lower()
            url_str = str(link.get("URL", ""))
            if "application/pdf" in content_type or url_str.endswith(".pdf") or "viewfile" in url_str.lower() or "/download/" in url_str.lower():
                if not pdf_url:
                    pdf_url = url_str
                is_oa = True
                break

        # Check licenses
        licenses = item.get("license", []) or []
        for lic in licenses:
            lic_url = str(lic.get("URL", "")).lower()
            if any(term in lic_url for term in ["creativecommons.org", "open-access", "publicdomain", "free-to-read"]):
                is_oa = True
                break

        # Check publisher / journal indicators (Indonesian OJS / University journals are Diamond Open Access)
        publisher_str = str(item.get("publisher", "")).lower()
        journal_str = str(journal_name or "").lower()
        url_str = str(article_url or "").lower()

        indo_oa_kws = [
            ".ac.id", "universitas", "institut", "politeknik", "stmik", "lppm",
            "iaes", "insis", "undip", "ugm", "itb", "ui", "unair", "ub", "unhas",
            "dinus", "uad", "telkom", "mdp", "ejournal", "jurnal"
        ]
        if any(kw in publisher_str or kw in journal_str or kw in url_str for kw in indo_oa_kws):
            is_oa = True

        pure_oa_pubs = ["plos", "mdpi", "biomed central", "bmc", "frontiers", "hindawi", "copernicus", "doaj"]
        if any(pub in publisher_str for pub in pure_oa_pubs):
            is_oa = True

        # Abstract
        abstract = item.get("abstract")
        if abstract:
            # Remove HTML tags common in Crossref abstracts
            import re
            abstract = re.sub(r"<[^>]+>", " ", abstract).strip()

        return RawArticle(
            title=title,
            source=self.name,
            doi=doi,
            abstract=abstract,
            year=year,
            publication_date=pub_date,
            journal_name=journal_name,
            publisher=item.get("publisher"),
            volume=item.get("volume"),
            issue=item.get("issue"),
            pages=item.get("page"),
            language=item.get("language"),
            keywords=item.get("subject", []),
            authors=authors,
            is_open_access=is_oa,
            article_url=article_url,
            pdf_url=pdf_url,
            citation_count=item.get("is-referenced-by-count"),
            issn=issn,
            eissn=eissn,
            source_id=doi,
            raw=item,
        )
