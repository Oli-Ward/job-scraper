import sqlite3
from pathlib import Path

DB_PATH = Path("jobs.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            is_remote BOOLEAN,
            job_url TEXT NOT NULL UNIQUE,
            date_posted TEXT,
            description TEXT,
            first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

def insert_jobs(df):
    if df.empty:
        return 0

    # Convert is_remote to integer for SQLite compatibility
    df = df.copy()
    if 'is_remote' in df.columns:
        df['is_remote'] = df['is_remote'].astype(int)

    rows = df[[
        "site", "title", "company", "location",
        "is_remote", "job_url", "date_posted", "description"
    ]].to_records(index=False)

    inserted = 0
    with get_connection() as conn:
        cur = conn.cursor()
        for r in rows:
            try:
                cur.execute("""
                INSERT INTO jobs (
                    site, title, company, location,
                    is_remote, job_url, date_posted, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, r)
                inserted += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()

    return inserted
