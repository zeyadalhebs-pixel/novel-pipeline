import sqlite3

conn = sqlite3.connect("novel.db")
cur = conn.cursor()

# 1. Create novels table if missing
cur.execute("""
    CREATE TABLE IF NOT EXISTS novels (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL
    )
""")

# 2. Insert default novel entry
cur.execute("""
    INSERT OR IGNORE INTO novels (id, title)
    VALUES ('doubao', 'الولادة من جديد في 2008، دو باو أصبح شفرة الغش')
""")

# 3. Check if novel_id column exists in chapters table
cur.execute("PRAGMA table_info(chapters)")
columns = [col[1] for col in cur.fetchall()]

if "novel_id" not in columns:
    print("Adding 'novel_id' column to existing chapters table...")
    cur.execute("ALTER TABLE chapters ADD COLUMN novel_id TEXT NOT NULL DEFAULT 'doubao'")
    conn.commit()
    print("✅ Successfully patched chapters table!")
else:
    print("Column 'novel_id' already exists.")

conn.commit()
conn.close()
print("🎉 Migration complete. novel.db is ready.")