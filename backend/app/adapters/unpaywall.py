"""Unpaywall adapter and Open Access full-text legal PDF resolver."""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class UnpaywallResolver:
    """Service to look up legal Open Access PDF locations via Unpaywall API."""

    base_url: str = "https://api.unpaywall.org/v2"

    @classmethod
    async def resolve_oa_location(cls, doi: str) -> Optional[Dict[str, Any]]:
        """Look up DOI in Unpaywall to find direct legal PDF link and OA status."""
        if not doi:
            return None

        clean_doi = doi.strip()
        email = getattr(settings, "crossref_email", "user@journalhunter.app")
        url = f"{cls.base_url}/{clean_doi}"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params={"email": email})
                if resp.status_code == 200:
                    data = resp.json()
                    is_oa = data.get("is_oa", False)
                    best_loc = data.get("best_oa_location") or {}
                    return {
                        "is_oa": is_oa,
                        "oa_status": data.get("oa_status"),
                        "pdf_url": best_loc.get("url_for_pdf"),
                        "landing_url": best_loc.get("url_for_landing_page"),
                        "license": best_loc.get("license"),
                        "version": best_loc.get("version"),
                        "host_type": best_loc.get("host_type"),
                    }
        except Exception as e:
            logger.debug(f"Unpaywall lookup error for {doi}: {e}")

        return None
