import time
from config import BATCH_SIZE, COOLDOWN_SECONDS, NOVEL_ID, NOVEL_TITLE, BASE_URL
from pipeline import run_batch
from db import get_next_chapter_number, init_db, register_novel

MAX_CHAPTER = 1000

def get_current_chapter(novel_id: str) -> int:
    """Reads the next chapter from the database or prompts the user if empty."""
    next_num = get_next_chapter_number(novel_id)
    if next_num is not None:
        return next_num

    while True:
        user_input = input(f"📍 No chapters found for '{novel_id}'. Enter starting chapter number: ").strip()
        if user_input.isdigit():
            return int(user_input)
        print("❌ Please enter a valid numeric chapter number.")

def main():
    print(f"🤖 Autonomous Pipeline Started for: {NOVEL_TITLE}")
    print(f"⚙️  Settings: {BATCH_SIZE} chapter/cycle | {COOLDOWN_SECONDS}s cooldown\n")

    # Ensure database is ready and the target novel exists
    init_db()
    register_novel(NOVEL_ID, NOVEL_TITLE)

    while True:
        current_chapter = get_current_chapter(NOVEL_ID)

        if MAX_CHAPTER is not None and current_chapter > MAX_CHAPTER:
            print(f"🏁 Reached end target chapter ({MAX_CHAPTER}). Exiting.")
            break

        print(f"\n{'=' * 55}")
        print(f"🚀 Processing Chapter {current_chapter}")
        print(f"{'=' * 55}")

        success = run_batch(current_chapter, BATCH_SIZE, NOVEL_ID, BASE_URL)

        if success:
            print(f"💾 Saved progress! Next chapter will be {current_chapter + BATCH_SIZE}")
        else:
            print("⚠️ Issue encountered. Retrying the same chapter after cooldown...")

        print(f"⏳ Pausing for {COOLDOWN_SECONDS}s before next cycle...")
        for remaining in range(COOLDOWN_SECONDS, 0, -10):
            print(f"   Continuing in {remaining}s...", end="\r")
            time.sleep(10)
        print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Pipeline stopped by user. Progress is safely stored in the database.")