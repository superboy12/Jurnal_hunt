"""Export service: CSV, XLSX, BibTeX, RIS, APA 7."""
from __future__ import annotations
import csv
import io
import re
from typing import List, Optional
from ..models.models import Article, ArticleAuthor, SearchArticle


def _get_author_string(authors: List[ArticleAuthor]) -> str:
    return "; ".join(a.name for a in sorted(authors, key=lambda x: x.order))


def _format_apa_authors(authors: List[ArticleAuthor]) -> str:
    """Format authors for APA 7 citation."""
    if not authors:
        return "[No author]"
    sorted_auths = sorted(authors, key=lambda x: x.order)
    if len(sorted_auths) > 20:
        parts = [_format_single_apa_author(a) for a in sorted_auths[:19]]
        parts.append("...")
        parts.append(_format_single_apa_author(sorted_auths[-1]))
        return ", ".join(parts)
    return ", ".join(_format_single_apa_author(a) for a in sorted_auths)


def _format_single_apa_author(author: ArticleAuthor) -> str:
    """Format 'Last, F. M.' from full name."""
    name = author.name.strip()
    # Handle "LastName, FirstName" format
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip()
        first = parts[1].strip()
    else:
        parts = name.split()
        if len(parts) >= 2:
            last = parts[-1]
            first = " ".join(parts[:-1])
        else:
            return name

    # Create initials
    initials = ". ".join(p[0].upper() for p in first.split() if p) + "."
    return f"{last}, {initials}"


def export_csv(search_articles: List[SearchArticle]) -> str:
    """Export to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "Rank", "Title", "Authors", "Year", "Journal", "Publisher",
        "DOI", "Volume", "Issue", "Pages", "Language",
        "Open Access", "PDF URL", "Article URL", "Keywords",
        "Citation Count", "Relevance Score", "Verification Status",
        "Sources", "Abstract"
    ]
    writer.writerow(headers)

    for sa in search_articles:
        art = sa.article
        if not art:
            continue
        authors_str = _get_author_string(art.authors)
        row = [
            sa.rank or "",
            art.title or "",
            authors_str,
            art.year or "",
            art.journal_name or "",
            art.publisher or "",
            art.doi or "",
            art.volume or "",
            art.issue or "",
            art.pages or "",
            art.language or "",
            "Yes" if art.is_open_access else ("No" if art.is_open_access is False else "Unknown"),
            art.pdf_url or "",
            art.article_url or "",
            "; ".join(art.keywords or []),
            art.citation_count or "",
            sa.relevance_score,
            art.verification_status.value if art.verification_status else "",
            "; ".join(art.sources or []),
            art.abstract or "",
        ]
        writer.writerow(row)

    return output.getvalue()


def export_bibtex(search_articles: List[SearchArticle]) -> str:
    """Export to BibTeX format."""
    lines = []
    for sa in search_articles:
        art = sa.article
        if not art:
            continue
        authors = sorted(art.authors, key=lambda x: x.order)
        author_str = " and ".join(a.name for a in authors) or "[No author]"

        # Generate citation key: LastnameYear
        key = "article"
        if authors:
            last = authors[0].name.split()[-1].lower()
            last = re.sub(r"[^\w]", "", last)
            key = f"{last}{art.year or 'nd'}"

        doi_line = f"  doi = {{{art.doi}}}," if art.doi else ""
        url_line = f"  url = {{{art.article_url}}}," if art.article_url else ""
        abstract_line = f"  abstract = {{{art.abstract}}}," if art.abstract else ""

        bib = f"""@article{{{key},
  title = {{{art.title or '[No title]'}}},
  author = {{{author_str}}},
  year = {{{art.year or 'n.d.'}}},
  journal = {{{art.journal_name or '[Journal unknown]'}}},
  volume = {{{art.volume or ''}}},
  number = {{{art.issue or ''}}},
  pages = {{{art.pages or ''}}},
  publisher = {{{art.publisher or ''}}},
{doi_line}
{url_line}
{abstract_line}
}}"""
        lines.append(bib.strip())

    return "\n\n".join(lines)


def export_ris(search_articles: List[SearchArticle]) -> str:
    """Export to RIS format for reference managers."""
    lines = []
    for sa in search_articles:
        art = sa.article
        if not art:
            continue
        entry = ["TY  - JOUR"]
        entry.append(f"TI  - {art.title or '[No title]'}")

        for auth in sorted(art.authors, key=lambda x: x.order):
            entry.append(f"AU  - {auth.name}")

        if art.year:
            entry.append(f"PY  - {art.year}")
        if art.journal_name:
            entry.append(f"JO  - {art.journal_name}")
        if art.volume:
            entry.append(f"VL  - {art.volume}")
        if art.issue:
            entry.append(f"IS  - {art.issue}")
        if art.pages:
            parts = art.pages.split("-")
            entry.append(f"SP  - {parts[0].strip()}")
            if len(parts) > 1:
                entry.append(f"EP  - {parts[1].strip()}")
        if art.publisher:
            entry.append(f"PB  - {art.publisher}")
        if art.doi:
            entry.append(f"DO  - {art.doi}")
        if art.abstract:
            entry.append(f"AB  - {art.abstract}")
        if art.article_url:
            entry.append(f"UR  - {art.article_url}")
        for kw in (art.keywords or []):
            entry.append(f"KW  - {kw}")
        entry.append("ER  - ")
        lines.append("\n".join(entry))

    return "\n\n".join(lines)


def export_apa7(search_articles: List[SearchArticle]) -> str:
    """Export formatted APA 7 reference list."""
    refs = []
    for i, sa in enumerate(search_articles, 1):
        art = sa.article
        if not art:
            continue
        authors_str = _format_apa_authors(art.authors)
        year = f"({art.year})." if art.year else "(n.d.)."
        title = f"{art.title}." if art.title else "[No title]."
        journal = art.journal_name or "[Journal unknown]"

        vol_issue = ""
        if art.volume and art.issue:
            vol_issue = f", *{art.volume}*({art.issue})"
        elif art.volume:
            vol_issue = f", *{art.volume}*"

        pages = f", {art.pages}" if art.pages else ""
        doi = f" https://doi.org/{art.doi}" if art.doi else (f" {art.article_url}" if art.article_url else "")

        ref = f"{i}. {authors_str} {year} {title} *{journal}*{vol_issue}{pages}.{doi}"
        refs.append(ref)

    return "\n\n".join(refs)


def export_xlsx(search_articles: List[SearchArticle]) -> bytes:
    """Export to Excel XLSX format."""
    try:
        import xlsxwriter
    except ImportError:
        raise ImportError("xlsxwriter is required for XLSX export")

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet("Articles")

    # Formats
    header_fmt = workbook.add_format({
        "bold": True, "bg_color": "#1e3a5f", "font_color": "white",
        "border": 1, "text_wrap": True, "align": "center"
    })
    cell_fmt = workbook.add_format({"text_wrap": True, "valign": "top", "border": 1})
    score_fmt = workbook.add_format({
        "num_format": "0.0", "bg_color": "#e8f4f8", "border": 1
    })

    headers = [
        "Rank", "Title", "Authors", "Year", "Journal", "Publisher",
        "DOI", "Volume", "Issue", "Pages", "Open Access",
        "PDF URL", "Article URL", "Keywords", "Citations",
        "Relevance Score", "Verification Status", "Sources", "Abstract"
    ]

    col_widths = [6, 50, 30, 8, 35, 25, 30, 8, 8, 12, 12, 40, 40, 40, 10, 16, 18, 20, 80]

    for col, (header, width) in enumerate(zip(headers, col_widths)):
        worksheet.write(0, col, header, header_fmt)
        worksheet.set_column(col, col, width)

    worksheet.freeze_panes(1, 0)

    for row_num, sa in enumerate(search_articles, 1):
        art = sa.article
        if not art:
            continue
        authors_str = _get_author_string(art.authors)
        row_data = [
            sa.rank or row_num,
            art.title or "",
            authors_str,
            art.year or "",
            art.journal_name or "",
            art.publisher or "",
            art.doi or "",
            art.volume or "",
            art.issue or "",
            art.pages or "",
            "Yes" if art.is_open_access else ("No" if art.is_open_access is False else ""),
            art.pdf_url or "",
            art.article_url or "",
            "; ".join(art.keywords or []),
            art.citation_count or "",
            sa.relevance_score,
            art.verification_status.value if art.verification_status else "",
            "; ".join(art.sources or []),
            art.abstract or "",
        ]
        for col, val in enumerate(row_data):
            if col == 15:  # Relevance score
                worksheet.write(row_num, col, val, score_fmt)
            else:
                worksheet.write(row_num, col, val, cell_fmt)

    workbook.close()
    return output.getvalue()
