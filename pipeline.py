import time
import re
from typing import List, Optional
from groq import Groq

from config import GROQ_API_KEY
from db import save_chapter
from scraper import scrape_chapter_wtr

GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "allam-2-7b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b"
]

groq_client = Groq(api_key=GROQ_API_KEY)

# Phrases that indicate Cloudflare / Turnstile challenge leakage
CLOUDFLARE_KEYWORDS = [
    "cloudflare",
    "turnstile",
    "verify you are human",
    "needs to review the security",
    "ray id",
    "checking if the site connection is secure",
    "enable javascript",
    "ddos protection"
]

SYSTEM_PROMPT = """You are a professional literary translator specializing in Chinese and English web novels into modern, expressive, and fluent Arabic.
Guidelines:
1. Translate accurately while ensuring natural-sounding narrative Arabic flow.
2. Keep dialogue punchy, realistic, and formatted with Arabic quotation dashes/marks.
3. Maintain character names, system terms, and honorifics consistently.
4. Output ONLY the translated Arabic title on the very first line prefixed by 'TITLE: '.
5. Follow immediately with the translated body text. Do not add conversational disclaimers or side notes.
6. The entire body MUST be written in Arabic script. Do NOT leave untranslated paragraphs."""

def is_cloudflare_leak(paragraphs: List[str]) -> bool:
    """Checks if the extracted paragraphs are Cloudflare challenge text."""
    combined = " ".join(paragraphs).lower()
    return any(keyword in combined for keyword in CLOUDFLARE_KEYWORDS)

def is_valid_novel_content(paragraphs: List[str]) -> bool:
    """Ensures content has real novel density, not repeated loops or empty stubs."""
    if len(paragraphs) < 5:
        return False

    combined = " ".join(paragraphs)
    words = combined.split()
    
    # Standard chapter should have at least 120 words
    if len(words) < 120:
        return False

    # Check for repetitive garbage (e.g. 3 lines repeating 20 times)
    unique_lines = set(p.strip().lower() for p in paragraphs if len(p.strip()) > 5)
    if len(paragraphs) >= 10 and len(unique_lines) <= 3:
        return False

    return True

def is_predominantly_arabic(text: str, min_ratio: float = 0.35) -> bool:
    """Validates that the output text is actually Arabic script, not raw English."""
    if not text:
        return False
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', text))
    if total_alpha == 0:
        return False
    return (arabic_chars / total_alpha) >= min_ratio

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

            # Enforce that the output is genuinely Arabic
            if not is_predominantly_arabic(arabic_body):
                print(f"⚠️ Model '{model_name}' returned non-Arabic text. Retrying with next model...")
                continue

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
        print(f"❌ Failed to extract content for Chapter {chapter_num}.")
        return False

    paragraphs = scraped_data["paragraphs"]

    # 1. Cloudflare text leak check
    if is_cloudflare_leak(paragraphs):
        print(f"🛡️ Extracted text contains Cloudflare Turnstile prompt. Scrape invalid for Chapter {chapter_num}.")
        return False

    # 2. Novel text density & repetitive loop check
    if not is_valid_novel_content(paragraphs):
        print(f"⚠️ Insufficient or repetitive content extracted ({len(paragraphs)} paragraphs). Skipping save.")
        return False

    raw_title = scraped_data.get("title", f"Chapter {chapter_num}")
    print(f"✅ Extracted {len(paragraphs)} clean paragraphs. Translating...")

    translated = translate_chapter(raw_title, paragraphs)

    # 3. Translation success & language check
    if not translated or not translated.get("body"):
        print(f"❌ Translation failed or output was invalid for Chapter {chapter_num}.")
        return False

    try:
        save_chapter(
            chapter_num=chapter_num,
            title=translated["title"],
            body=translated["body"],
            novel_id=novel_id
        )
        print(f"🎉 Chapter {chapter_num} successfully validated and saved to novel.db!")
        return True
    except Exception as e:
        print(f"❌ Database error on Chapter {chapter_num}: {e}")
        return False

def run_batch(start_chapter: int, batch_size: int, novel_id: str, base_url: str) -> bool:
    for ch in range(start_chapter, start_chapter + batch_size):
        success = process_single_chapter(ch, novel_id, base_url)
        if not success:
            return False
    return True