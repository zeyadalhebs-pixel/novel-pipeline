import time
from db import get_all_chapter_numbers
from config import NOVEL_ID, BASE_URL, COOLDOWN_SECONDS
from pipeline import process_single_chapter

def get_missing_chapters(novel_id: str) -> list[int]:
    existing = set(get_all_chapter_numbers(novel_id))
    if not existing:
        return []
    
    start_ch = min(existing)
    end_ch = max(existing)
    
    full_range = set(range(start_ch, end_ch + 1))
    missing = sorted(list(full_range - existing))
    return missing

def main():
    missing = get_missing_chapters(NOVEL_ID)
    total = len(missing)

    if not total:
        print(f"✅ No gaps found for novel '{NOVEL_ID}'. All chapters are contiguous!")
        return

    print("=" * 60)
    print(f"🔍 Found {total} missing/purged chapters to backfill.")
    print(f"📖 Chapters to recover: {missing}")
    print("=" * 60)

    for idx, ch_num in enumerate(missing, 1):
        print(f"\n[{idx}/{total}] 🚀 Recovering Chapter {ch_num}...")
        
        success = process_single_chapter(ch_num, NOVEL_ID, BASE_URL)
        
        if success:
            print(f"💾 Chapter {ch_num} successfully recovered and saved!")
        else:
            print(f"⚠️ Chapter {ch_num} could not be recovered on this pass. Skipping to next...")

        print(f"⏳ Cooldown ({COOLDOWN_SECONDS}s)...")
        time.sleep(COOLDOWN_SECONDS)

    print("\n🎉 Backfill process completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Backfill paused by user. Progress safely saved.")