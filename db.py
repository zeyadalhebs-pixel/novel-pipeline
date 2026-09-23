import sqlite3
from typing import List, Optional, Dict

DB_PATH = "novel.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS novels (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL
            )
        """)
        cur.execute("PRAGMA table_info(chapters)")
        cols = [col[1] for col in cur.fetchall()]
        if cols and "novel_id" not in cols:
            cur.execute("ALTER TABLE chapters ADD COLUMN novel_id TEXT NOT NULL")
        conn.commit()

def register_novel(novel_id: str, title: str):
    """Ensures the novel exists in the database before saving chapters."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO novels (id, title) VALUES (?, ?)", (novel_id, title))
        conn.commit()

def get_novels() -> List[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM novels")
        rows = cur.fetchall()
        return [{"id": r[0], "title": r[1]} for r in rows]

def get_chapter(chapter_num: int, novel_id: str) -> Optional[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT num, title, body
            FROM chapters 
            WHERE novel_id = ? AND num = ?
        """, (novel_id, chapter_num))
        row = cur.fetchone()
        if row:
            return {"chapter_number": row[0], "title": row[1], "body": row[2]}
        return None

def get_all_chapter_numbers(novel_id: str) -> List[int]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT num 
            FROM chapters 
            WHERE novel_id = ? 
            ORDER BY num ASC
        """, (novel_id,))
        rows = cur.fetchall()
        return [r[0] for r in rows]

def save_chapter(chapter_num: int, title: str, body: str, novel_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chapters (novel_id, num, title, body)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(num) DO UPDATE SET
                novel_id = excluded.novel_id,
                title = excluded.title,
                body = excluded.body
        """, (novel_id, chapter_num, title, body))
        conn.commit()

def get_next_chapter_number(novel_id: str) -> Optional[int]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(num) FROM chapters WHERE novel_id = ?", (novel_id,))
        row = cur.fetchone()
        return (row[0] + 1) if row and row[0] is not None else None