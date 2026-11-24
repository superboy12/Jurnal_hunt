"""Add subject_category column to articles table."""
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if column exists
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='articles' AND column_name='subject_category'
    """))
    exists = result.fetchone()
    if not exists:
        conn.execute(text("ALTER TABLE articles ADD COLUMN subject_category VARCHAR(100) DEFAULT NULL"))
        conn.commit()
        print("Column subject_category added.")
    else:
        print("Column subject_category already exists.")
