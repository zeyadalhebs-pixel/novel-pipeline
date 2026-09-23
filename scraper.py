import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

MIN_ACCEPTABLE_PARAGRAPHS = 3

BOT_INDICATORS = [
    "security check",
    "فحص الأمان",
    "cloudflare",
    "verify you are human",
    "just a moment",
    "turnstile",
    "challenge-running"
]

def init_driver(headless: bool = True):
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = uc.Chrome(options=options, version_main=153)
    except Exception:
        driver = uc.Chrome(options=options)
        
    driver.set_page_load_timeout(45)
    return driver

def extract_chapter_payload(driver):
    """Extracts title and content paragraphs from the current page."""
    title = ""
    # Broadened Title Selectors
    for sel in ["h1", "h2", ".chapter-title", ".title", ".entry-title"]:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, sel)
            t = elem.text.strip()
            if t:
                title = t
                break
        except Exception:
            continue

    paragraphs = []
    # Broadened Container Selectors
    container_selectors = [
        ".chapter-body",
        ".reading-content",
        ".content-story",
        "#chapter-content",
        ".chapter-content",
        "article",
        ".txtnav",
        ".read-container",
        ".entry-content",
        "main"
    ]

    for sel in container_selectors:
        try:
            container = driver.find_element(By.CSS_SELECTOR, sel)
            p_elems = container.find_elements(By.TAG_NAME, "p")
            if p_elems and len(p_elems) >= MIN_ACCEPTABLE_PARAGRAPHS:
                paragraphs = [p.text.strip() for p in p_elems if p.text.strip()]
                if len(paragraphs) >= MIN_ACCEPTABLE_PARAGRAPHS:
                    break
            
            # Fallback if no <p> tags are used inside the container
            raw_text = container.text.strip()
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            if len(lines) >= MIN_ACCEPTABLE_PARAGRAPHS:
                paragraphs = lines
                break
        except Exception:
            continue

    # Absolute fallback: search the whole body for <p> tags
    if len(paragraphs) < MIN_ACCEPTABLE_PARAGRAPHS:
        try:
            all_p = driver.find_elements(By.TAG_NAME, "p")
            extracted = [p.text.strip() for p in all_p if len(p.text.strip()) > 15]
            if len(extracted) >= MIN_ACCEPTABLE_PARAGRAPHS:
                paragraphs = extracted
        except Exception:
            pass

    if paragraphs and title and paragraphs[0].strip() == title.strip():
        paragraphs = paragraphs[1:]

    return title, paragraphs

def has_bot_challenge(driver, title: str, paragraphs: list) -> bool:
    """Checks whether the page is a Cloudflare verification page."""
    try:
        # The most reliable indicator is the page title itself
        page_title = driver.title.lower()
        if any(bot in page_title for bot in ["just a moment", "cloudflare", "attention required"]):
            return True
    except Exception:
        pass

    # Only check the first 3 paragraphs. This prevents false positives 
    # if the actual website footer says "Protected by Cloudflare".
    joined = (title + " " + " ".join(paragraphs[:3])).lower()
    return any(indicator in joined for indicator in BOT_INDICATORS)

def solve_with_visible_window(url: str, chapter_num: int):
    """Spawns a visible Chrome window to pass Turnstile/Cloudflare."""
    print(f"\n⚡ Cloudflare challenge detected! Popping visible Chrome window for Ch. {chapter_num}...")
    driver = None
    try:
        driver = init_driver(headless=False)
        driver.get(url)

        print("⏳ Waiting for Turnstile to clear (solve checkbox if prompted)...")
        for elapsed in range(45):
            time.sleep(1)
            try:
                title, paragraphs = extract_chapter_payload(driver)
                
                # Verify we have enough paragraphs AND it's not the challenge page
                if len(paragraphs) >= MIN_ACCEPTABLE_PARAGRAPHS and not has_bot_challenge(driver, title, paragraphs):
                    print("🔓 Cloudflare cleared successfully!")
                    time.sleep(1.5) # Buffer to ensure full DOM render
                    return {
                        "title": title or f"Chapter {chapter_num}",
                        "paragraphs": paragraphs
                    }
            except Exception:
                # Catch DOM detachment errors during the redirect
                continue

        print("❌ Cloudflare challenge timeout. Content could not be verified.")
        return None
    except Exception as e:
        print(f"Error during interactive bypass: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def scrape_chapter_wtr(url: str, chapter_num: int):
    """Attempts fast headless scrape first, falling back to visible browser on challenge."""
    driver = None
    try:
        print(f"🔗 Loading URL: {url}")
        driver = init_driver(headless=True)
        try:
            driver.get(url)
        except Exception:
            driver.execute_script("window.stop();")

        time.sleep(3)
        title, paragraphs = extract_chapter_payload(driver)

        if len(paragraphs) >= MIN_ACCEPTABLE_PARAGRAPHS and not has_bot_challenge(driver, title, paragraphs):
            return {
                "title": title or f"Chapter {chapter_num}",
                "paragraphs": paragraphs
            }

        try:
            driver.quit()
        except Exception:
            pass
        driver = None

        return solve_with_visible_window(url, chapter_num)

    except Exception as e:
        print(f"Scraper error on chapter {chapter_num}: {e}")
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        return solve_with_visible_window(url, chapter_num)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

scrape_chapter = scrape_chapter_wtr