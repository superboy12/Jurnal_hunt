"""AI Command Interpreter: parse natural language search commands."""
from __future__ import annotations
import re
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from ..schemas.schemas import InterpretedCommand
from ..core.config import settings


# ── Keyword extraction helpers ─────────────────────────────────────────

SINTA_PATTERNS = [
    r"sinta\s*(\d+)\s*(?:sampai|to|[-–—]|hingga|s/d)\s*sinta\s*(\d+)",
    r"sinta\s*(\d+)\s*(?:to|[-–—])\s*(\d+)",
    r"sinta\s*(\d+)",
]

YEAR_PATTERNS = [
    r"(?:tahun|year|published?|terbit|dari|from|since)\s*(\d{4})\s*(?:sampai|hingga|to|[-–—]|s/d)\s*(\d{4})",
    r"(\d{4})\s*(?:sampai|hingga|to|[-–—]|s/d)\s*(\d{4})",
    r"(\d+)\s*tahun\s*terakhir",
    r"last\s*(\d+)\s*years?",
    r"(?:tahun|year|in)\s*(\d{4})",
]

NUMBER_PATTERNS = [
    r"(?:cari|search|find|ambil|tampilkan|show|get)\s+(\d+)\s+(?:artikel|article|paper|jurnal|journal)",
    r"(\d+)\s+(?:artikel|article|paper|jurnal|journal)",
]

INDEXING_KEYWORDS = {
    "scopus": ["scopus", "scoupus", "terindeks scopus", "terindeks scoupus", "scopus indexed", "scopus only"],
    "sinta": ["sinta", "terindeks sinta", "sinta indexed", "sinta only"],
    "both": [
        "scopus dan sinta", "scopus and sinta", "scopus & sinta", "scopus + sinta",
        "sinta dan scopus", "sinta and scopus", "sinta & scopus", "sinta + scopus",
        "sinta atau scopus", "scopus atau sinta", "sinta or scopus", "scopus or sinta",
        "sinta atau scoupus", "scoupus atau sinta", "sinta maupun scopus", "scopus maupun sinta",
    ],
}

OPEN_ACCESS_KEYWORDS = [
    "open access", "akses terbuka", "gratis", "free", "freely available",
    "open-access", "oa journal"
]

PDF_KEYWORDS = ["pdf", "full text", "full-text", "fulltext", "teks lengkap", "unduh"]
DOI_KEYWORDS = ["doi", "digital object identifier"]

COMMUNITY_SERVICE_KEYWORDS = [
    "pengabdian masyarakat", "community service", "abdimas", "pengabdian",
    "pkm", "jurnal pengabdian"
]

REVIEW_KEYWORDS = [
    "review", "systematic review", "literature review", "tinjauan pustaka",
    "meta-analysis", "meta analysis", "metaanalysis"
]

CONFERENCE_KEYWORDS = [
    "conference", "konferensi", "proceedings", "prosiding", "seminar",
    "symposium", "workshop paper"
]

SYNONYM_MAP: Dict[str, List[str]] = {
    "judi online": ["online gambling", "perjudian online", "cyber gambling", "internet gambling", "gambling website"],
    "pemblokiran": ["blocking", "dns filtering", "content filtering", "filtering", "penapisan situs"],
    "generative ai": ["gen ai", "large language model", "llm", "gpt", "artificial intelligence generatif"],
    "machine learning": ["ml", "deep learning", "neural network", "pembelajaran mesin"],
    "cloud computing": ["komputasi awan", "cloud services", "iaas", "paas", "saas"],
    "cybersecurity": ["keamanan siber", "information security", "keamanan informasi", "cyber security"],
    "e-government": ["government digitalization", "digital government", "smart government", "pemerintahan digital"],
    "natural language processing": ["nlp", "text mining", "pemrosesan bahasa alami"],
    "internet of things": ["iot", "smart sensor", "connected devices"],
}

PRESETS = {
    "scopus_only": {"indexing_target": "scopus", "sources": ["crossref", "openalex", "semantic_scholar"]},
    "sinta_only": {"indexing_target": "sinta", "sources": ["crossref", "openalex", "doaj"]},
    "scopus_sinta": {"indexing_target": "both", "sources": ["crossref", "openalex", "semantic_scholar", "doaj"]},
    "cyber_security": {"category": "Keamanan Siber"},
    "it_computing": {"category": "Teknologi Informasi & Komputer"},
    "law_policy": {"category": "Hukum & Kebijakan"},
    "open_access": {"open_access_only": True, "sources": ["openalex", "doaj", "crossref", "semantic_scholar"]},
    "community_service": {"publication_type": "community_service", "sources": ["crossref", "openalex", "doaj"]},
    "latest_research": {"year_from": datetime.now().year - 2, "sources": ["crossref", "openalex", "semantic_scholar", "doaj"]},
    "literature_review": {"publication_type": "review", "sources": ["crossref", "openalex", "semantic_scholar"]},
}


def interpret_command(command: str, preset: Optional[Union[str, List[str]]] = None, presets: Optional[List[str]] = None) -> InterpretedCommand:
    """Parse a natural language search command into structured parameters."""
    cmd_lower = command.lower()
    notes = []

    # --- Apply preset(s) as base ---
    if isinstance(preset, list):
        active_presets = preset
    elif presets:
        active_presets = presets
    elif preset:
        active_presets = [preset]
    else:
        active_presets = []

    preset_data = {}
    for p in active_presets:
        if isinstance(p, str):
            preset_data.update(PRESETS.get(p, {}))

    # --- Extract number of results ---
    max_results = settings.default_max_results
    for pat in NUMBER_PATTERNS:
        m = re.search(pat, cmd_lower)
        if m:
            max_results = min(int(m.group(1)), settings.max_results_per_search)
            break

    # --- Extract year range ---
    year_from = preset_data.get("year_from", None)
    year_to = None
    current_year = datetime.now().year

    # Check "N tahun terakhir / last N years"
    m = re.search(r"(\d+)\s*tahun\s*terakhir", cmd_lower)
    if not m:
        m = re.search(r"last\s*(\d+)\s*years?", cmd_lower)
    if m:
        n = int(m.group(1))
        year_from = current_year - n
        year_to = current_year
        notes.append(f"Rentang tahun: {year_from}–{year_to}")
    else:
        for pat in YEAR_PATTERNS[:2]:
            m = re.search(pat, cmd_lower)
            if m and len(m.groups()) == 2:
                year_from = int(m.group(1))
                year_to = int(m.group(2))
                break
        if not year_from:
            for pat in YEAR_PATTERNS[2:]:
                m = re.search(pat, cmd_lower)
                if m:
                    year_from = int(m.group(1))
                    break

    if not year_to and year_from:
        year_to = current_year

    # --- Extract SINTA rank ---
    sinta_rank_min = None
    sinta_rank_max = None

    m = re.search(SINTA_PATTERNS[0], cmd_lower)
    if m:
        sinta_rank_min = int(m.group(1))
        sinta_rank_max = int(m.group(2))
        notes.append(f"SINTA {sinta_rank_min}–{sinta_rank_max}")
    else:
        m = re.search(SINTA_PATTERNS[1], cmd_lower)
        if m:
            sinta_rank_min = int(m.group(1))
            sinta_rank_max = int(m.group(2))
        else:
            m = re.search(SINTA_PATTERNS[2], cmd_lower)
            if m:
                rank = int(m.group(1))
                sinta_rank_min = sinta_rank_max = rank

    # Normalize typos
    cmd_lower = cmd_lower.replace("scoupus", "scopus")

    # --- Indexing target ---
    indexing_target = preset_data.get("indexing_target")
    # If user explicitly asked for both in command, command takes precedence over single preset
    if any(kw in cmd_lower for kw in INDEXING_KEYWORDS["both"]) or ("sinta" in cmd_lower and "scopus" in cmd_lower):
        indexing_target = "both"
    elif not indexing_target:
        if any(kw in cmd_lower for kw in INDEXING_KEYWORDS["scopus"]):
            indexing_target = "scopus"
        elif any(kw in cmd_lower for kw in INDEXING_KEYWORDS["sinta"]) or sinta_rank_min:
            indexing_target = "sinta"

    if sinta_rank_min and not indexing_target:
        indexing_target = "sinta"

    # --- Open access ---
    open_access_only = preset_data.get("open_access_only", False)
    if any(kw in cmd_lower for kw in OPEN_ACCESS_KEYWORDS):
        open_access_only = True

    # --- PDF / DOI requirements ---
    require_pdf = any(kw in cmd_lower for kw in PDF_KEYWORDS)
    require_doi = any(kw in cmd_lower for kw in DOI_KEYWORDS)

    # --- Publication type ---
    publication_type = preset_data.get("publication_type")
    if not publication_type:
        if any(kw in cmd_lower for kw in COMMUNITY_SERVICE_KEYWORDS):
            publication_type = "community_service"
        elif any(kw in cmd_lower for kw in REVIEW_KEYWORDS):
            publication_type = "review"
        elif any(kw in cmd_lower for kw in CONFERENCE_KEYWORDS):
            publication_type = "conference"
        else:
            publication_type = "journal"

    # --- Language ---
    language = None
    if "bahasa indonesia" in cmd_lower or "berbahasa indonesia" in cmd_lower:
        language = "id"
    elif "english" in cmd_lower or "bahasa inggris" in cmd_lower:
        language = "en"

    # --- Extract topic and keywords ---
    topic, keywords = _extract_keywords(command, cmd_lower)

    # --- Expand with synonyms ---
    synonyms = _get_synonyms(keywords)

    # --- Sources ---
    sources = preset_data.get("sources", ["crossref", "openalex", "semantic_scholar", "doaj"])
    if indexing_target == "scopus" and "crossref" not in sources:
        sources = ["crossref", "openalex", "semantic_scholar"] + sources

    # --- Build notes ---
    if open_access_only:
        notes.append("Filter: Open access saja")
    if require_pdf:
        notes.append("Filter: Memerlukan link PDF")
    if language:
        notes.append(f"Bahasa: {language}")
    if publication_type and publication_type != "journal":
        notes.append(f"Tipe: {publication_type}")

    interpretation_notes = " | ".join(notes) if notes else "Menggunakan parameter default"

    return InterpretedCommand(
        topic=topic,
        keywords=keywords[:10],
        synonyms=synonyms[:10],
        language=language,
        year_from=year_from,
        year_to=year_to,
        max_results=max_results,
        indexing_target=indexing_target,
        sinta_rank_min=sinta_rank_min,
        sinta_rank_max=sinta_rank_max,
        publication_type=publication_type,
        open_access_only=open_access_only,
        require_doi=require_doi,
        require_pdf=require_pdf,
        sources=sources,
        interpretation_notes=interpretation_notes,
    )


def _extract_keywords(command: str, cmd_lower: str) -> tuple[str, List[str]]:
    """Extract main topic and keywords from command."""
    clean = cmd_lower.replace("scoupus", "scopus")

    # Remove common command verbs and conversational prefixes
    clean = re.sub(
        r"^(?:tolong\s+carikan|carikan\s+saya|tolong\s+cari|carikan|saya\s+butuh|mohon\s+carikan|mohon\s+cari|cari|search|find|tampilkan|show|get|berikan|ambil)\s+",
        "", clean
    )
    clean = re.sub(
        r"(?:\d+\s*)?(?:artikel|article|paper|jurnal|journal)\s*(?:ilmiah)?\s*(?:sinta\s+atau\s+scopus|scopus\s+atau\s+sinta|sinta\s+dan\s+scopus|scopus\s+dan\s+sinta|sinta|scopus)?\s*(?:yang\s+membahas|tentang|about|mengenai|terkait|seputar|on|for|discussing)?\s*",
        "", clean
    )
    clean = re.sub(
        r"^(?:kategori|category|bidang)\s+(?:keamanan\s+siber|cyber\s*security|it(?:\s*&\s*komputer)?|hukum(?:\s*&\s*kebijakan)?|kesehatan|pendidikan|[\w\s]+?)\s*(?:tentang|mengenai|seputar|terkait|about|on|for|yang\s+membahas)?\s*",
        "", clean, flags=re.IGNORECASE
    )
    clean = re.sub(
        r"\b(?:kategori|category|bidang)\s+(?:keamanan\s+siber|cyber\s*security|it|hukum|kesehatan|pendidikan)\b",
        "", clean, flags=re.IGNORECASE
    )
    # Remove filter phrases
    for phrase in [
        r"sinta\s*\d+\s*(?:sampai|to|[-–—]|hingga|s/d)\s*sinta?\s*\d+", r"sinta\s*\d+",
        r"sinta\s+(?:atau|dan|maupun|or|and)\s+scopus",
        r"scopus\s+(?:atau|dan|maupun|or|and)\s+sinta",
        r"scopus\s*(?:only|saja)?", r"sinta\s*(?:only|saja)?", r"open\s*access",
        r"(?:tahun|year)?\s*\d{4}\s*(?:sampai|hingga|to|[-–—]|s/d)\s*\d{4}",
        r"(?:tahun|year)\s*\d{4}",
        r"terbit\s+dalam\s+\d+\s+tahun\s+terakhir",
        r"last\s+\d+\s+years?",
        r"tampilkan\s+(?:doi|abstrak|skor|pdf|link|status)\s*", r",\s*(?:doi|abstrak|skor|pdf).*$",
        r"prioritaskan.*$", r"dan\s+tampilkan.*$",
    ]:
        clean = re.sub(phrase, "", clean)

    clean = re.sub(r"\s+", " ", clean).strip(" ,.")
    # Clean leftover connector words from beginning of topic
    clean = re.sub(r"^(?:jurnal|journal|artikel|article|paper)\s+", "", clean)
    clean = re.sub(r"^(?:sinta\s+atau\s+scopus|scopus\s+atau\s+sinta|sinta|scopus)\s+", "", clean)
    clean = re.sub(r"^(?:yang\s+membahas|seputar|tentang|about|mengenai|terkait|discussing)\s+", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip(" ,.")

    # The clean text is our topic
    topic = clean if clean else command[:100]

    # Extract keywords: split on common connectors
    kw_text = re.sub(r"\b(dan|and|atau|or|untuk|for|tentang|about|mengenai|terkait|on|the|a|an)\b", " ", clean)
    kw_text = re.sub(r"[,;]", " ", kw_text)

    # Try to extract quoted phrases first
    quoted = re.findall(r'"([^"]+)"', command)

    # Then split remaining by common separators
    rest = re.sub(r'"[^"]+"', "", kw_text)
    words = [w.strip() for w in re.split(r"\s{2,}|,|;", rest) if w.strip() and len(w.strip()) > 2]

    keywords = quoted + words
    keywords = list(dict.fromkeys(keywords))[:10]  # deduplicate, keep order

    if not keywords:
        keywords = [topic]

    # Prioritize gambling core domain keywords if present
    if any(g in command.lower() for g in ["judi", "gambling", "judol", "perjudian"]):
        gambling_kws = ["judi online", "pemblokiran", "online gambling"]
        if "dns" in command.lower():
            gambling_kws.append("DNS")
        if "ai" in command.lower():
            gambling_kws.append("AI")
        for gk in reversed(gambling_kws):
            if gk not in keywords:
                keywords.insert(0, gk)

    return topic, keywords


async def interpret_command_async(
    command: str,
    preset: Optional[str] = None,
    presets: Optional[List[str]] = None
) -> InterpretedCommand:
    """Async interpretation using Gemini AI first, fallback to regex rules."""
    from .ai_service import ai_service
    active_presets = presets or ([preset] if preset else [])
    ai_data = await ai_service.interpret_search_command(command, preset, active_presets)
    if ai_data and isinstance(ai_data, dict) and ai_data.get("topic"):
        target = None
        if "scopus_sinta" in active_presets or ("scopus_only" in active_presets and "sinta_only" in active_presets):
            target = "both"
        elif "scopus_only" in active_presets:
            target = "scopus"
        elif "sinta_only" in active_presets:
            target = "sinta"
        else:
            target = ai_data.get("indexing_target")

        cmd_lower = command.lower().replace("scoupus", "scopus")
        if "sinta" in cmd_lower and "scopus" in cmd_lower:
            target = "both"
        elif "sinta" in cmd_lower and not target:
            target = "sinta"
        elif "scopus" in cmd_lower and not target:
            target = "scopus"

        oa_only = bool(ai_data.get("open_access_only") or "open_access" in active_presets)

        return InterpretedCommand(
            topic=ai_data.get("topic") or command[:100],
            keywords=ai_data.get("keywords") or [ai_data.get("topic") or command[:100]],
            synonyms=ai_data.get("synonyms") or [],
            language=ai_data.get("language"),
            year_from=ai_data.get("year_from"),
            year_to=ai_data.get("year_to"),
            max_results=min(ai_data.get("max_results") or 50, settings.max_results_per_search),
            indexing_target=target,
            sinta_rank_min=ai_data.get("sinta_rank_min"),
            sinta_rank_max=ai_data.get("sinta_rank_max"),
            publication_type=ai_data.get("publication_type") or "journal",
            open_access_only=oa_only,
            require_doi=bool(ai_data.get("require_doi")),
            require_pdf=bool(ai_data.get("require_pdf")),
            sources=ai_data.get("sources") or ["crossref", "openalex", "semantic_scholar", "doaj"],
            interpretation_notes=ai_data.get("interpretation_notes") or f"Diinterpretasikan dengan AI (Target: {target or 'Semua'}, Presets: {', '.join(active_presets) if active_presets else 'None'})",
        )
    return interpret_command(command, preset, active_presets)


def _get_synonyms(keywords: List[str]) -> List[str]:
    """Return synonyms for known keywords."""
    synonyms = []
    for kw in keywords:
        kw_l = kw.lower()
        for key, syns in SYNONYM_MAP.items():
            if key in kw_l or kw_l in key:
                synonyms.extend(syns)
                break
            for syn in syns:
                if syn in kw_l:
                    synonyms.append(key)
                    break
    return list(dict.fromkeys(synonyms))
