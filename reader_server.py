import html
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from db import get_chapter, get_all_chapter_numbers, get_novels, init_db

app = FastAPI(title="Novel Reader & Library")

init_db()

def load_template(filename: str) -> str:
    """Helper function to read HTML templates from the templates directory."""
    filepath = os.path.join("templates", filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def clean_and_normalize_body(raw_body: str) -> str:
    if not raw_body:
        return ""

    clean_text = raw_body.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = [line.strip() for line in clean_text.split("\n")]
    paragraphs = [p for p in raw_lines if p]

    dialogue_symbols = ('"', '“', '”', '«', '»', '—', '-', '>')

    formatted_html = []
    for line in paragraphs:
        escaped_line = html.escape(line)
        if any(escaped_line.startswith(sym) for sym in dialogue_symbols):
            formatted_html.append(f'<p class="dialogue">{escaped_line}</p>')
        else:
            formatted_html.append(f'<p>{escaped_line}</p>')

    return "\n".join(formatted_html)

@app.get("/", response_class=HTMLResponse)
def library_index():
    novels = get_novels()
    template = load_template("library.html")
    
    if not novels:
        empty_markup = '<div class="empty-shelf">لا توجد روايات مسجلة في قاعدة البيانات بعد.</div>'
        return template.replace("{{ novel_cards }}", empty_markup)

    cards = []
    for n in novels:
        n_id = n["id"]
        title = html.escape(n["title"])
        all_ch = get_all_chapter_numbers(n_id)
        count = len(all_ch)
        
        first_ch = all_ch[0] if all_ch else 1
        link = f"/novel/{n_id}/chapter/{first_ch}" if count > 0 else "#"

        card_html = f"""
        <a href="{link}" class="novel-card" data-novel-id="{n_id}">
            <div class="novel-info">
                <span class="novel-title">{title}</span>
                <div class="novel-meta">
                    <span class="chapter-badge">{count} فصل محفوظ</span>
                    <span>المعرف: {n_id}</span>
                </div>
            </div>
            <div class="arrow-icon">←</div>
        </a>
        """
        cards.append(card_html)

    return template.replace("{{ novel_cards }}", "\n".join(cards))

@app.get("/novel/{novel_id}", response_class=RedirectResponse)
def redirect_to_first_chapter(novel_id: str):
    all_nums = get_all_chapter_numbers(novel_id)
    if not all_nums:
        raise HTTPException(status_code=404, detail="لا توجد فصول محفوظة لهذه الرواية بعد.")
    return RedirectResponse(url=f"/novel/{novel_id}/chapter/{all_nums[0]}")

@app.get("/novel/{novel_id}/chapter/{num}", response_class=HTMLResponse)
def read_chapter(novel_id: str, num: int):
    chapter = get_chapter(num, novel_id=novel_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found in database.")

    novels = {n["id"]: n["title"] for n in get_novels()}
    novel_title = novels.get(novel_id, "رواية غير معروفة")

    all_chapters = get_all_chapter_numbers(novel_id)
    curr_idx = all_chapters.index(num) if num in all_chapters else -1

    prev_ch = all_chapters[curr_idx - 1] if curr_idx > 0 else None
    next_ch = all_chapters[curr_idx + 1] if curr_idx >= 0 and curr_idx < len(all_chapters) - 1 else None

    body_paragraphs_html = clean_and_normalize_body(chapter["body"])

    dropdown_markup = "".join(
        f'<option value="{n}" {"selected" if n == num else ""}>الفصل {n}</option>'
        for n in all_chapters
    )

    template = load_template("reader.html")
    page = template.replace("{{ novel_id }}", novel_id)
    page = page.replace("{{ chapter_num }}", str(num))
    page = page.replace("{{ novel_title }}", html.escape(novel_title))
    page = page.replace("{{ title }}", html.escape(chapter["title"]))
    page = page.replace("{{ body_paragraphs }}", body_paragraphs_html)
    page = page.replace("{{ prev_ch }}", str(prev_ch) if prev_ch else "")
    page = page.replace("{{ next_ch }}", str(next_ch) if next_ch else "")
    page = page.replace("{{ dropdown_options }}", dropdown_markup)
    page = page.replace("{{ 'disabled' if not prev_ch else '' }}", "" if prev_ch else "disabled")
    page = page.replace("{{ 'disabled' if not next_ch else '' }}", "" if next_ch else "disabled")

    return page