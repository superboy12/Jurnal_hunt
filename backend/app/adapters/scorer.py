"""Relevance scoring engine."""
from __future__ import annotations
import math
import re
from typing import List, Optional, Dict, Any
from .base import RawArticle


def score_article(
    article: RawArticle,
    keywords: List[str],
    synonyms: List[str],
    year_from: Optional[int],
    year_to: Optional[int],
    open_access_only: bool,
    require_pdf: bool,
    publication_type: Optional[str],
) -> tuple[float, str]:
    """
    Score article relevance 0–100. Returns (score, reason).
    Relevance is about topic match, NOT journal quality.
    """
    score = 0.0
    reasons = []

    search_terms = [kw.lower() for kw in keywords] + [s.lower() for s in synonyms]

    combined_content = f"{article.title or ''} {article.abstract or ''} {' '.join(article.keywords or [])}".lower()

    # ── Core topic domain relevance check ────────────────────────────
    # For online gambling (judi online), must contain gambling-related terminology
    is_gambling_search = any(w in " ".join(keywords).lower() for w in ["judi", "gambling", "perjudian", "judol", "taruhan", "betting"])
    if is_gambling_search:
        has_gambling_content = any(w in combined_content for w in ["judi", "gambling", "perjudian", "judol", "taruhan", "betting", "casinos", "poker"])
        if not has_gambling_content:
            return 0.0, "Tidak memuat pembahasan judi online / perjudian"

    # ── Title match (40 points) ──────────────────────────────────────
    title_score = _text_match(article.title or "", search_terms)
    score += title_score * 40
    if title_score > 0.5:
        reasons.append(f"Judul sangat relevan ({title_score:.0%})")
    elif title_score > 0.2:
        reasons.append(f"Judul relevan ({title_score:.0%})")

    # ── Abstract match (30 points) ───────────────────────────────────
    if article.abstract:
        abs_score = _text_match(article.abstract, search_terms)
        score += abs_score * 30
        if abs_score > 0.3:
            reasons.append("Abstrak memuat kata kunci utama")

    # ── Keyword match (15 points) ────────────────────────────────────
    if article.keywords:
        kw_text = " ".join(article.keywords).lower()
        kw_score = _text_match(kw_text, search_terms)
        score += kw_score * 15
        if kw_score > 0.3:
            reasons.append("Kata kunci artikel sesuai")

    # ── Year proximity (10 points) ───────────────────────────────────
    if article.year:
        year_score = _year_score(article.year, year_from, year_to)
        score += year_score * 10
        if year_score >= 0.8:
            reasons.append(f"Tahun terbit {article.year} sesuai rentang yang diminta")

    # ── User filter fulfillment (5 points) ───────────────────────────
    filter_bonus = 0.0
    if open_access_only and article.is_open_access:
        filter_bonus += 2.5
        reasons.append("Open access ✓")
    if require_pdf and article.pdf_url:
        filter_bonus += 2.5
        reasons.append("PDF tersedia ✓")
    if publication_type and _type_matches(article, publication_type):
        filter_bonus += 2.5
        reasons.append(f"Tipe publikasi sesuai ({publication_type})")
    score += min(filter_bonus, 5.0)

    # Clamp
    score = min(max(score, 0.0), 100.0)

    reason = " | ".join(reasons) if reasons else "Relevansi rendah"
    return round(score, 1), reason


def _text_match(text: str, terms: List[str]) -> float:
    """Compute keyword overlap score (0–1), matching phrases and key tokens."""
    if not text or not terms:
        return 0.0
    text_lower = text.lower()

    expanded_terms = []
    for t in terms:
        t_clean = t.strip().lower()
        if t_clean:
            expanded_terms.append(t_clean)
            words = [
                w for w in re.findall(r"\b\w+\b", t_clean)
                if len(w) > 3 and w not in ("dalam", "pada", "atau", "yang", "dengan", "from", "with", "about", "over", "into", "untuk", "sebagai")
            ]
            expanded_terms.extend(words)

    unique_terms = list(dict.fromkeys(expanded_terms))
    if not unique_terms:
        return 0.0

    matched = sum(1 for t in unique_terms if t in text_lower)
    weighted = sum((1.0 / (i + 1)) for i, t in enumerate(unique_terms) if t in text_lower)
    max_weight = sum(1.0 / (i + 1) for i in range(len(unique_terms)))
    return weighted / max_weight if max_weight > 0 else 0.0


def _year_score(year: int, year_from: Optional[int], year_to: Optional[int]) -> float:
    """Score year proximity."""
    if year_from and year_to:
        if year_from <= year <= year_to:
            return 1.0
        dist = min(abs(year - year_from), abs(year - year_to))
        return max(0.0, 1.0 - dist / 5.0)
    elif year_from:
        if year >= year_from:
            return 1.0
        return max(0.0, 1.0 - (year_from - year) / 5.0)
    elif year_to:
        if year <= year_to:
            return 1.0
        return max(0.0, 1.0 - (year - year_to) / 5.0)
    return 0.5  # No year constraint → neutral


def _type_matches(article: RawArticle, pub_type: str) -> bool:
    """Check if article type matches requested type."""
    if not pub_type:
        return False
    title_lower = (article.title or "").lower()
    journal_lower = (article.journal_name or "").lower()
    combined = title_lower + " " + journal_lower
    type_keywords = {
        "community_service": ["pengabdian", "abdimas", "community service", "pkm"],
        "review": ["review", "systematic review", "meta-analysis", "literature review"],
        "conference": ["proceedings", "conference", "symposium", "seminar"],
    }
    if pub_type in type_keywords:
        return any(kw in combined for kw in type_keywords[pub_type])
    return True
