import os
from dotenv import load_dotenv

load_dotenv()

# Groq LLM API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Current Target Novel
# Change these to scrape and translate any new novel
NOVEL_ID = "doubao"
NOVEL_TITLE = "الولادة من جديد في 2008، دو باو أصبح شفرة الغش"
BASE_URL = "https://wtr-lab.com/en/novel/40698/reborn-in-2008-doubao-became-my-cheat-code/chapter-"

# Pipeline Runtime Settings
BATCH_SIZE = 1
COOLDOWN_SECONDS = 40