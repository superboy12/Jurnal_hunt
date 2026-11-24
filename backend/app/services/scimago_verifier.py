"""
SCImago Journal & Country Rank (SJR) Verification Service.
Official Scopus verification powered by SCImago database (https://www.scimagojr.com/).
Validates whether a journal or publisher is authentically indexed in Scopus,
extracting its SJR score, Quartile (Q1-Q4), H-index, and official SCImago profile URL.
"""
from __future__ import annotations
import os
import re
import html
import sqlite3
import logging
import unicodedata
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scimago.db")


def normalize_journal_title(text: Optional[str]) -> str:
    """Normalize journal name for robust SCImago comparison."""
    if not text:
        return ""
    text = html.unescape(text)
    # Replace ampersands with 'and' for consistency
    text = re.sub(r"\s*&\s*", " and ", text)
    text = unicodedata.normalize("NFKD", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_conference_or_proceedings(norm_text: str) -> bool:
    """Detect if title is a conference proceeding rather than an indexed journal."""
    conf_kws = [
        "conference", "proceedings", "symposium", "workshop",
        "annual meeting", "congress", "seminar", "colloquium", "session"
    ]
    return any(kw in norm_text for kw in conf_kws)


def verify_journal_scimago(
    journal_name: Optional[str],
    issn: Optional[str] = None,
    eissn: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Verify whether a journal is indexed in Scopus via SCImago Journal Rank (https://www.scimagojr.com/).
    Returns None if not verified in SCImago.
    Returns metadata dict with Quartile, SJR, and SCImago URL if verified.
    """
    if not journal_name:
        return None

    norm_target = normalize_journal_title(journal_name)
    if not norm_target:
        return None

    if not os.path.exists(DB_PATH):
        logger.warning(f"SCImago database not found at {DB_PATH}")
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 1. Exact normalized match
        row = c.execute(
            """
            SELECT title, quartile, sjr, h_index, country, scimago_url, open_access, subject_area
            FROM scimago_journals
            WHERE norm_title = ?
            ORDER BY sjr DESC LIMIT 1
            """,
            (norm_target,)
        ).fetchone()

        if row:
            conn.close()
            return _format_scimago_result(row)

        # 1b. Check without subtitle (after colon) or parenthesized abbreviation
        stripped_raw = re.sub(r":.*$", "", re.sub(r"\(.*?\)", "", journal_name)).strip()
        stripped_norm = normalize_journal_title(stripped_raw)
        if stripped_norm and stripped_norm != norm_target:
            row = c.execute(
                """
                SELECT title, quartile, sjr, h_index, country, scimago_url, open_access, subject_area
                FROM scimago_journals
                WHERE norm_title = ?
                ORDER BY sjr DESC LIMIT 1
                """,
                (stripped_norm,)
            ).fetchone()
            if row:
                conn.close()
                return _format_scimago_result(row)

        # 2. Check if conference/proceeding - skip fuzzy matching for conferences to prevent false positives
        if _is_conference_or_proceedings(norm_target):
            conn.close()
            return None

        # 3. Clean common prefixes/suffixes: "the ...", "... journal", etc.
        core_target = re.sub(r"^(the|an|a)\s+", "", norm_target).strip()
        if core_target != norm_target:
            row = c.execute(
                """
                SELECT title, quartile, sjr, h_index, country, scimago_url, open_access, subject_area
                FROM scimago_journals
                WHERE norm_title = ?
                ORDER BY sjr DESC LIMIT 1
                """,
                (core_target,)
            ).fetchone()
            if row:
                conn.close()
                return _format_scimago_result(row)

        # 4. Strict fuzzy match for genuine journals with length >= 8 characters
        if len(norm_target) >= 8:
            candidates = c.execute(
                """
                SELECT title, norm_title, quartile, sjr, h_index, country, scimago_url, open_access, subject_area
                FROM scimago_journals
                WHERE norm_title LIKE ? 
                   OR (length(norm_title) >= 10 AND ? LIKE '%' || norm_title || '%')
                ORDER BY sjr DESC LIMIT 5
                """,
                (f"{norm_target}%", norm_target)
            ).fetchall()

            for cand in candidates:
                cand_norm = cand[1]
                # Length ratio guard: avoid matching a 1-word journal inside a 4-word title
                len_ratio = min(len(norm_target), len(cand_norm)) / max(len(norm_target), len(cand_norm))
                if len_ratio >= 0.65:
                    conn.close()
                    # Return formatted result without norm_title column
                    formatted_row = (cand[0], cand[2], cand[3], cand[4], cand[5], cand[6], cand[7], cand[8])
                    return _format_scimago_result(formatted_row)

        conn.close()
        return None

    except Exception as e:
        logger.error(f"Error querying SCImago database for '{journal_name}': {e}")
        return None


def _format_scimago_result(row) -> Dict[str, Any]:
    """Helper to structure SCImago result."""
    return {
        "is_scopus_indexed": True,
        "scimago_verified": True,
        "scimago_title": row[0],
        "scimago_quartile": row[1],
        "sjr_score": row[2],
        "h_index": row[3],
        "country": row[4],
        "scimago_url": row[5],
        "open_access": bool(row[6]),
        "subject_area": row[7],
    }


def analyze_scimago_status(journal_name: Optional[str], issn: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive SCImago analysis for user presentation and API responses.
    """
    clean_jname = journal_name.strip() if journal_name else ""
    encoded_jname = clean_jname.replace(" ", "%20")
    clean_issn = (issn or "").replace("-", "").strip()
    scimago_search_url = f"https://www.scimagojr.com/journalsearch.php?q={clean_issn if clean_issn else encoded_jname}"
    scopus_sources_url = f"https://www.scopus.com/sources.uri?query={encoded_jname}"

    res = verify_journal_scimago(journal_name, issn)
    if res:
        quartile = res.get("scimago_quartile") or "Terindeks"
        sjr = res.get("sjr_score")
        return {
            "is_scopus": True,
            "verified_by_scimago": True,
            "quartile": quartile,
            "sjr_score": sjr,
            "h_index": res.get("h_index"),
            "country": res.get("country"),
            "scimago_url": res.get("scimago_url") or scimago_search_url,
            "scopus_sources_url": scopus_sources_url,
            "message": f"Terverifikasi Scopus via SCImago JR ({quartile}, SJR: {sjr if sjr is not None else '-'})",
        }
    else:
        return {
            "is_scopus": False,
            "verified_by_scimago": False,
            "quartile": None,
            "sjr_score": None,
            "h_index": None,
            "country": None,
            "scimago_url": scimago_search_url,
            "scopus_sources_url": scopus_sources_url,
            "message": "Tidak terdaftar dalam indeks resmi SCImago JR (Bukan Jurnal Scopus)",
        }
