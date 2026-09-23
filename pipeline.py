import time
from typing import List, Optional
from groq import Groq

from config import GROQ_API_KEY
from db import save_chapter, get_all_chapter_numbers
from scraper import scrape_chapter_wtr

GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "allam-2-7b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b"
]

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a professional literary translator specializing in Chinese and English web novels into modern, expressive, and fluent Arabic.
Guidelines:
1. Translate accurately while ensuring natural-sounding narrative Arabic flow.
2. Keep dialogue punchy, realistic, and formatted with Arabic quotation dashes/marks.
3. Maintain character names, system terms, and honorifics consistently.
4. Output ONLY the translated Arabic title on the very first line prefixed by 'TITLE: '.
5. Follow immediately with the translated body text. Do not add conversational disclaimers or side notes."""

def translate_chapter(raw_title: str, paragraphs: List[str]) -> Optional[dict]:
    content_payload = f"Title: {raw_title}\n\n" + "\n\n".join(paragraphs)

    for model_name in GROQ_MODELS:
        try:
            response = groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Translate the following novel chapter into Arabic:\n\n{content_payload}"}
                ],
                temperature=0.3,
                max_tokens=4096
            )

            result_text = response.choices[0].message.content.strip()

            lines = result_text.splitlines()
            title = raw_title
            body_start_index = 0

            for i, line in enumerate(lines[:5]):
                if line.startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                    body_start_index = i + 1
                    break
                elif "الفصل" in line and len(line) < 100:
                    title = line.strip()
                    body_start_index = i + 1
                    break

            arabic_body = "\n".join(lines[body_start_index:]).strip() or result_text
            return {"title": title, "body": arabic_body}

        except Exception as e:
            print(f"⚠️ Model '{model_name}' failed: {e}. Trying next model...")
            time.sleep(2)
            continue

    return None

def process_single_chapter(chapter_num: int, novel_id: str, base_url: str) -> bool:
    url = f"{base_url}{chapter_num}?service=web"
    scraped_data = scrape_chapter_wtr(url, chapter_num)

    if not scraped_data or not scraped_data.get("paragraphs"):
        print(f"❌ Failed to extract readable chapter content for Chapter {chapter_num}.")
        return False

    raw_title = scraped_data.get("title", f"Chapter {chapter_num}")
    paragraphs = scraped_data["paragraphs"]

    if len(paragraphs) < 3:
        print(f"⚠️ Insufficient content extracted ({len(paragraphs)} paragraphs). Skipping save.")
        return False

    print(f"✅ Extracted {len(paragraphs)} paragraphs. Translating...")
    translated = translate_chapter(raw_title, paragraphs)

    if not translated:
        print(f"❌ Translation failed for Chapter {chapter_num}.")
        return False

    try:
        save_chapter(
            chapter_num=chapter_num,
            title=translated["title"],
            body=translated["body"],
            novel_id=novel_id
        )
        print(f"🎉 Chapter {chapter_num} successfully saved to novel.db!")
        return True
    except Exception as e:
        print(f"❌ Database error on Chapter {chapter_num}: {e}")
        return False

def run_batch(start_chapter: int, batch_size: int, novel_id: str, base_url: str) -> bool:
    """Executes a batch of chapters sequentially."""
    for ch in range(start_chapter, start_chapter + batch_size):
        success = process_single_chapter(ch, novel_id, base_url)
        if not success:
            return False
    return True