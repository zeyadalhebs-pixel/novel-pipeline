import sqlite3
import re

DB_PATH = "novel.db"
CLOUDFLARE_KEYWORDS = ["cloudflare", "turnstile", "verify you are human", "checking if the site"]

def is_corrupted(body: str) -> bool:
    if not body or len(body.strip()) < 100:
        return True
    
    # Check for Cloudflare leaks
    lower = body.lower()
    if any(k in lower for k in CLOUDFLARE_KEYWORDS):
        return True

    # Check for non-Arabic (English text remaining)
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', body))
    total_alpha = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', body))
    if total_alpha > 0 and (arabic_chars / total_alpha) < 0.35:
        return True

    return False

def purge_bad_chapters():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT novel_id, num, title, body FROM chapters")
        rows = cur.fetchall()
        
        purged = 0
        for novel_id, num, title, body in rows:
            if is_corrupted(body):
                print(f"🗑️ Deleting corrupted: Novel '{novel_id}' - Chapter {num} ({title[:30]})")
                cur.execute("DELETE FROM chapters WHERE novel_id = ? AND num = ?", (novel_id, num))
                purged += 1
        
        conn.commit()
        print(f"\nCleanup complete. Removed {purged} bad chapters.")

if __name__ == "__main__":
    purge_bad_chapters()