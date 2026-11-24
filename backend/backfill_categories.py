"""Backfill existing articles with subject category."""
import re
from app.core.database import SessionLocal
from app.models.models import Article
from app.services.search_pipeline import _classify_subject_heuristic

db = SessionLocal()
articles = db.query(Article).filter((Article.subject_category == None) | (Article.subject_category == "")).all()
print(f"Found {len(articles)} articles needing category backfill...")
updated = 0
for art in articles:
    cat = _classify_subject_heuristic(art.title or "", art.abstract or "", art.journal_name or "")
    art.subject_category = cat
    updated += 1

db.commit()
print(f"Successfully backfilled {updated} articles with categories.")
db.close()
