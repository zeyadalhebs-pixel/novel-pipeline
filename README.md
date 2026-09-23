# Autonomous Web Novel Translation Pipeline & Local Reader

An end-to-end automated pipeline that scrapes web novel chapters, translates them from English/Chinese to Arabic using Groq's LLM API, and serves them locally through a decoupled FastAPI interface.

## System Architecture

*   **Scraper Engine:** Built with `undetected_chromedriver` and Selenium. Defaults to headless execution but features dynamic Cloudflare Turnstile detection, automatically spawning an interactive browser to clear security challenges before resuming.
*   **Translation Layer:** Utilizes Groq's high-speed API (defaulting to `qwen3.8-27b` and `allam-2-7b`) with fallback routing to ensure uninterrupted batch processing.
*   **Persistence:** A lightweight, robust SQLite database (`novel.db`) manages state. The runner dynamically queries the database for the last processed chapter, eliminating fragile state files and ensuring zero data loss during crashes.
*   **Frontend Reader:** A local web interface served via FastAPI, featuring OLED/Dark/Light themes, Arabic typography selection, swipe navigation, and `localStorage` reading progress tracking. 

## Tech Stack
*   **Backend:** Python 3.14, FastAPI, Uvicorn
*   **Database:** SQLite
*   **Browser Automation:** Selenium, undetected-chromedriver
*   **AI/Translation:** Groq API

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/zeyadalhebs-pixel/novel-pipeline.git](https://github.com/zeyadalhebs-pixel/novel-pipeline.git)
   cd novel-pipeline