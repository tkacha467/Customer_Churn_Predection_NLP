import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = r"d:\Review\Review AI\Customer_Churn_Predection_NLP"
OUTPUT_DIR = os.path.join(BASE_DIR, "PRODUCT_A_UI_INSPECTION", "screenshots")
DESKTOP_DIR = os.path.join(OUTPUT_DIR, "desktop")
MOBILE_DIR = os.path.join(OUTPUT_DIR, "mobile")
RESPONSIVE_DIR = os.path.join(OUTPUT_DIR, "responsive")

os.makedirs(DESKTOP_DIR, exist_ok=True)
os.makedirs(MOBILE_DIR, exist_ok=True)
os.makedirs(RESPONSIVE_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://127.0.0.1:5173/review?table=Table+4&business_id=default_business"

def capture_desktop(browser):
    print("\n--- Capturing Desktop (1440x900) ---")
    context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.0)
    page = context.new_page()

    # Clear sessionStorage to ensure clean initial state
    page.goto(URL, wait_until="networkidle")
    page.wait_for_selector(".ng-card", timeout=8000)
    page.evaluate("sessionStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".ng-card", timeout=8000)
    time.sleep(1)

    # 01 - Initial Customer Review Page
    page.screenshot(path=os.path.join(DESKTOP_DIR, "01-initial-page.png"))
    print(" -> 01-initial-page.png")

    # 02 - Business Header & Welcome Section
    world_el = page.locator(".ng-world")
    header_el = page.locator(".ng-header")
    if world_el.count() > 0 and header_el.count() > 0:
        box1 = world_el.bounding_box()
        box2 = header_el.bounding_box()
        clip_y = min(box1["y"], box2["y"])
        clip_h = (box2["y"] + box2["height"]) - clip_y + 15
        page.screenshot(
            path=os.path.join(DESKTOP_DIR, "02-business-header.png"),
            clip={"x": max(0, box2["x"] - 50), "y": clip_y, "width": box2["width"] + 100, "height": clip_h}
        )
    print(" -> 02-business-header.png")

    # 03 - Rating Selection (Click 4 stars)
    page.locator(".ng-star").nth(3).click()
    time.sleep(0.4)
    page.screenshot(path=os.path.join(DESKTOP_DIR, "03-rating-selection.png"))
    print(" -> 03-rating-selection.png")

    # Dismiss cookie banner
    cookie_btn = page.locator(".ng-cookie-btn")
    if cookie_btn.count() > 0:
        cookie_btn.click()
        time.sleep(0.3)

    # Reset to 5 stars & click Continue to expand card
    page.locator(".ng-star").nth(4).click()
    time.sleep(0.2)
    page.locator(".ng-btn-continue-initial").click()
    time.sleep(0.6)
    page.wait_for_selector(".ng-expanded-card", timeout=5000)

    # 04 - Review Topic Selection
    topic_sec = page.locator("section[aria-label='Visit highlights']")
    topic_sec.scroll_into_view_if_needed()
    time.sleep(0.3)
    page.locator(".ng-chip").filter(has_text="Snacks").click()
    page.fill("#ng-note", "The poha and masala chai were hot and delicious! 😋")
    time.sleep(0.4)
    page.screenshot(path=os.path.join(DESKTOP_DIR, "04-topic-selection.png"))
    print(" -> 04-topic-selection.png")

    # 05 - Language Selection
    lang_sec = page.locator("section[aria-label='Language selection']")
    lang_sec.scroll_into_view_if_needed()
    time.sleep(0.3)
    page.locator(".ng-lang-btn").filter(has_text="Gujarati").click()
    time.sleep(0.4)
    page.screenshot(path=os.path.join(DESKTOP_DIR, "05-language-selection.png"))
    print(" -> 05-language-selection.png")

    # Switch back to English
    page.locator(".ng-lang-btn").filter(has_text="English").click()
    time.sleep(0.6)

    # 06 - AI Review Suggestions
    ideas_sec = page.locator("section[aria-label='Review suggestions']")
    ideas_sec.scroll_into_view_if_needed()
    time.sleep(0.5)
    page.screenshot(path=os.path.join(DESKTOP_DIR, "06-ai-review-suggestions.png"))
    print(" -> 06-ai-review-suggestions.png")

    # 08 - Private Feedback Form (do before reloading session)
    priv_btn = page.locator(".ng-private-prompt .ng-link-btn")
    priv_btn.scroll_into_view_if_needed()
    time.sleep(0.3)
    priv_btn.click()
    time.sleep(0.6)
    page.wait_for_selector(".ng-private-form", timeout=5000)
    page.fill(".ng-private-form textarea", "The morning breakfast was great, but table cleaning took a little extra time during peak hours.")
    page.fill(".ng-private-form input", "Kaushik Ajani (+91 98765 43210)")
    time.sleep(0.4)
    page.screenshot(path=os.path.join(DESKTOP_DIR, "08-private-feedback.png"))
    print(" -> 08-private-feedback.png")

    # Close private modal
    page.locator(".ng-private-form .ng-btn-secondary").click()
    time.sleep(0.4)

    # 09 - Complete Customer Review Page
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.5)
    page.screenshot(path=os.path.join(DESKTOP_DIR, "09-complete-page.png"), full_page=True)
    print(" -> 09-complete-page.png")

    # 07 - Selected Review & Handoff Modal (via stored review session restore)
    page.evaluate("""() => {
        sessionStorage.setItem('nastaGharSelectedReview', 'Amazing breakfast and best chai in town! The poha and masala chai were hot and fresh. Loved it 🍳☕');
        sessionStorage.setItem('nastaGharSelectedReviewId', 'opt1');
        sessionStorage.setItem('nastaGharSelectedRating', '5');
        sessionStorage.setItem('nastaGharClipboardCopied', 'true');
        sessionStorage.setItem('nastaGharBusinessId', 'default_business');
        window.location.reload();
    }""")
    page.wait_for_selector(".ng-modal-backdrop", timeout=8000)
    time.sleep(0.8)
    page.screenshot(path=os.path.join(DESKTOP_DIR, "07-review-selected.png"))
    print(" -> 07-review-selected.png")

    context.close()

def capture_mobile(browser):
    print("\n--- Capturing Mobile (390x844) ---")
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2.0,
        is_mobile=True,
        has_touch=True,
    )
    page = context.new_page()

    page.goto(URL, wait_until="networkidle")
    page.wait_for_selector(".ng-card", timeout=8000)
    page.evaluate("sessionStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".ng-card", timeout=8000)
    time.sleep(1)

    # M01 - Initial Mobile Review Page
    page.screenshot(path=os.path.join(MOBILE_DIR, "01-initial-page.png"))
    print(" -> mobile/01-initial-page.png")

    # M02 - Mobile Rating Selection
    page.locator(".ng-star").nth(3).click()
    time.sleep(0.4)
    page.screenshot(path=os.path.join(MOBILE_DIR, "02-rating-selection.png"))
    print(" -> mobile/02-rating-selection.png")

    # Dismiss cookie banner
    cookie_btn = page.locator(".ng-cookie-btn")
    if cookie_btn.count() > 0:
        cookie_btn.click()
        time.sleep(0.3)

    # Reset to 5 stars & continue
    page.locator(".ng-star").nth(4).click()
    time.sleep(0.2)
    page.locator(".ng-btn-continue-initial").click()
    time.sleep(0.6)
    page.wait_for_selector(".ng-expanded-card", timeout=5000)

    # M03 - Mobile Topic Selection
    m_topic_sec = page.locator("section[aria-label='Visit highlights']")
    m_topic_sec.scroll_into_view_if_needed()
    time.sleep(0.3)
    page.locator(".ng-chip").filter(has_text="Snacks").click()
    page.fill("#ng-note", "Super fast service & amazing tea!")
    time.sleep(0.4)
    page.screenshot(path=os.path.join(MOBILE_DIR, "03-topic-selection.png"))
    print(" -> mobile/03-topic-selection.png")

    # M04 - Mobile Language Selection
    m_lang_sec = page.locator("section[aria-label='Language selection']")
    m_lang_sec.scroll_into_view_if_needed()
    time.sleep(0.3)
    page.locator(".ng-lang-btn").filter(has_text="Hindi").click()
    time.sleep(0.4)
    page.screenshot(path=os.path.join(MOBILE_DIR, "04-language-selection.png"))
    print(" -> mobile/04-language-selection.png")

    # Switch back to English
    page.locator(".ng-lang-btn").filter(has_text="English").click()
    time.sleep(0.6)

    # M05 - Mobile AI Review Cards
    m_ideas = page.locator("section[aria-label='Review suggestions']")
    m_ideas.scroll_into_view_if_needed()
    time.sleep(0.5)
    page.screenshot(path=os.path.join(MOBILE_DIR, "05-ai-review-suggestions.png"))
    print(" -> mobile/05-ai-review-suggestions.png")

    # M07 - Mobile Private Feedback Form
    priv_btn = page.locator(".ng-private-prompt .ng-link-btn")
    priv_btn.scroll_into_view_if_needed()
    time.sleep(0.3)
    priv_btn.click()
    time.sleep(0.6)
    page.wait_for_selector(".ng-private-form", timeout=5000)
    page.fill(".ng-private-form textarea", "The seating was a bit crowded during morning peak hours.")
    page.fill(".ng-private-form input", "Kaushik (Table 4)")
    time.sleep(0.4)
    page.screenshot(path=os.path.join(MOBILE_DIR, "07-private-feedback.png"))
    print(" -> mobile/07-private-feedback.png")

    # Close modal
    page.locator(".ng-private-form .ng-btn-secondary").click()
    time.sleep(0.4)

    # M06 - Mobile Review Selection & Handoff Modal
    page.evaluate("""() => {
        sessionStorage.setItem('nastaGharSelectedReview', 'Amazing breakfast and best chai in town! Loved it 🍳☕');
        sessionStorage.setItem('nastaGharSelectedReviewId', 'opt1');
        sessionStorage.setItem('nastaGharSelectedRating', '5');
        sessionStorage.setItem('nastaGharClipboardCopied', 'true');
        sessionStorage.setItem('nastaGharBusinessId', 'default_business');
        window.location.reload();
    }""")
    page.wait_for_selector(".ng-modal-backdrop", timeout=8000)
    time.sleep(0.8)
    page.screenshot(path=os.path.join(MOBILE_DIR, "06-review-selected.png"))
    print(" -> mobile/06-review-selected.png")

    context.close()

def capture_responsive(browser):
    print("\n--- Capturing Responsive Viewports ---")
    viewports = [
        ("laptop-1366.png", 1366, 768, False),
        ("tablet-768.png", 768, 1024, True),
        ("mobile-390.png", 390, 844, True),
        ("small-mobile-360.png", 360, 800, True),
    ]

    for fname, w, h, is_mob in viewports:
        r_context = browser.new_context(
            viewport={"width": w, "height": h},
            device_scale_factor=1.0 if not is_mob else 2.0,
            is_mobile=is_mob,
            has_touch=is_mob,
        )
        r_page = r_context.new_page()
        r_page.goto(URL, wait_until="networkidle")
        r_page.wait_for_selector(".ng-card", timeout=8000)
        time.sleep(0.5)

        # Dismiss cookie banner
        c_btn = r_page.locator(".ng-cookie-btn")
        if c_btn.count() > 0:
            c_btn.click()
            time.sleep(0.2)

        # Expand card
        r_page.locator(".ng-btn-continue-initial").click()
        time.sleep(0.6)
        r_page.wait_for_selector(".ng-expanded-card", timeout=5000)
        r_page.screenshot(path=os.path.join(RESPONSIVE_DIR, fname))
        print(f" -> responsive/{fname} ({w}x{h})")
        r_context.close()

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
        capture_desktop(browser)
        capture_mobile(browser)
        capture_responsive(browser)
        browser.close()
        print("\nALL SCREENSHOTS CAPTURED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
