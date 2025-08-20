
import os
import time
import json
import random
import sys
from pathlib import Path
from urllib.parse import quote_plus

# pip install selenium python-dotenv webdriver-manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    ElementNotInteractableException,
)
from dotenv import load_dotenv

def log(msg):
    print(time.strftime("[%H:%M:%S]"), msg, flush=True)

def human_pause(a=0.8, b=1.8):
    time.sleep(random.uniform(a, b))

def launch_browser(user_data_dir=None, headless=False):
    log("Chrome başlatılıyor...")
    opts = webdriver.ChromeOptions()
    if user_data_dir:
        opts.add_argument(f"--user-data-dir={user_data_dir}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    if headless:
        opts.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    return driver

def ensure_login(driver, email, password):
    driver.get("https://www.linkedin.com/")
    human_pause()
    try:
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.ID, "global-nav")))
        log("Zaten oturum açık.")
        return
    except TimeoutException:
        pass
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "password").submit()
    log("Giriş yapıldı. 2FA varsa tamamlayın.")
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "global-nav")))
    except TimeoutException:
        log("2FA bekleniyor veya giriş kontrolü var.")

def build_search_url(query, location, filters):
    base = "https://www.linkedin.com/jobs/search/"
    params = {
        "keywords": query,
        "location": location,
        "f_AL": "true" if filters.get("easy_apply_only", True) else None,
        "f_WT": filters.get("work_type"),
        "f_E": filters.get("experience_levels"),
        "f_TPR": filters.get("date_posted"),
        "f_C": filters.get("company_ids"),
        "position": "1",
        "pageNum": "0",
    }
    parts = [f"{k}={quote_plus(str(v))}" for k, v in params.items() if v]
    return base + "?" + "&".join(parts)

def collect_job_links(driver, max_pages=3):
    links = set()
    for page in range(1, max_pages+1):
        human_pause(1, 2)
        cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li a[href*='/jobs/view/']")
        for a in cards:
            url = a.get_attribute("href")
            if url:
                links.add(url.split("?")[0])
        try:
            next_btn = driver.find_element(By.XPATH, "//button[@aria-label='Sonraki' or @aria-label='Next']")
            if next_btn.is_enabled():
                driver.execute_script("arguments[0].click();", next_btn)
                log(f"Sonraki sayfa {page+1}...")
                WebDriverWait(driver, 15).until(EC.staleness_of(cards[0]))
            else:
                break
        except Exception:
            break
    return list(links)

def is_easy_apply(driver):
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
        return "Easy Apply" in btn.text or "Kolay Başvuru" in btn.text
    except NoSuchElementException:
        return False

def dismiss_popups(driver):
    for sel in ["button[aria-label='Kapat']", "button[aria-label='Dismiss']", "button[aria-label='Close']", "button[aria-label='Skip']"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                if e.is_displayed():
                    driver.execute_script("arguments[0].click();", e)
                    human_pause(0.3, 0.6)
        except Exception:
            pass

def close_known_overlays(driver):
    selectors = [
        # Cookie consent / generic dismiss
        "button[data-testid='cookie-banner-accept']",
        "button[aria-label*='Accept']",
        "button[aria-label*='Kabul']",
        "button[aria-label*='Kapat']",
        "button[aria-label*='Dismiss']",
        "button[aria-label*='Close']",
        "button[aria-label*='Skip']",
        # Messaging bubbles
        "button.msg-overlay-bubble-header__control[aria-label*='Minimize']",
        "button.msg-overlay-bubble-header__control[aria-label*='Küçült']",
        "button.msg-overlay-bubble-header__control[aria-label*='Dismiss']",
        "button.msg-overlay-bubble-header__control[aria-label*='Close']",
        # Modal close
        ".artdeco-modal__dismiss",
    ]
    for sel in selectors:
        try:
            for e in driver.find_elements(By.CSS_SELECTOR, sel):
                if e.is_displayed():
                    driver.execute_script("arguments[0].click();", e)
                    human_pause(0.2, 0.4)
        except Exception:
            continue

def highlight_element(driver, element, color="#00ff00"):
    try:
        driver.execute_script(
            "arguments[0].style.outline='3px solid %s'; arguments[0].style.transition='outline 0.2s ease-in-out';" % color,
            element,
        )
    except Exception:
        pass

def save_debug_screenshot(driver, name_prefix="debug"):
    try:
        Path("screenshots").mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = Path("screenshots") / f"{name_prefix}_{ts}.png"
        driver.save_screenshot(str(path))
        log(f"Ekran görüntüsü kaydedildi: {path}")
    except Exception:
        pass

def is_clickable_via_point(driver, element):
    try:
        return driver.execute_script(
            """
            const el = arguments[0];
            if (!el) return false;
            const r = el.getBoundingClientRect();
            const x = Math.floor(r.left + r.width/2);
            const y = Math.floor(r.top + Math.min(r.height/2, 10));
            const topEl = document.elementFromPoint(x, y);
            return topEl === el || (el.contains(topEl));
            """,
            element,
        )
    except Exception:
        return False

def try_remove_obstruction_at_point(driver, element):
    try:
        return driver.execute_script(
            """
            const el = arguments[0];
            const r = el.getBoundingClientRect();
            const x = Math.floor(r.left + r.width/2);
            const y = Math.floor(r.top + Math.min(r.height/2, 10));
            const topEl = document.elementFromPoint(x, y);
            if (!topEl || topEl === el || el.contains(topEl)) return false;
            const cs = window.getComputedStyle(topEl);
            const isOverlay = cs.position === 'fixed' || parseInt(cs.zIndex||'0',10) >= 1000 || topEl.className.includes('overlay') || topEl.className.includes('msg-overlay');
            if (isOverlay) {
                topEl.setAttribute('data-hidden-by-bot','1');
                topEl.style.display = 'none';
                return true;
            }
            return false;
            """,
            element,
        )
    except Exception:
        return False

def robust_click(driver, element, max_attempts=3):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            # Keep away from sticky headers/footers
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
            driver.execute_script("window.scrollBy(0, -120);")
            human_pause(0.2, 0.4)

            highlight_element(driver, element)

            if not is_clickable_via_point(driver, element):
                close_known_overlays(driver)
                human_pause(0.2, 0.4)
                if not is_clickable_via_point(driver, element):
                    try_remove_obstruction_at_point(driver, element)
                    human_pause(0.1, 0.2)

            try:
                ActionChains(driver).move_to_element(element).pause(0.1).click().perform()
            except Exception:
                element.click()

            # As a safety net, if nothing happened, try ENTER/SPACE
            try:
                element.send_keys(Keys.ENTER)
            except Exception:
                pass
            try:
                element.send_keys(Keys.SPACE)
            except Exception:
                pass

            return True
        except (ElementClickInterceptedException, ElementNotInteractableException) as e:
            last_error = e
            close_known_overlays(driver)
            human_pause(0.2, 0.4)
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception as je:
                last_error = je
                # Try dispatching full click sequence
                try:
                    driver.execute_script(
                        "var el=arguments[0]; ['mousedown','mouseup','click'].forEach(ev=>el.dispatchEvent(new MouseEvent(ev,{bubbles:true,cancelable:true,view:window})));",
                        element,
                    )
                    return True
                except Exception as je2:
                    last_error = je2
        except StaleElementReferenceException as e:
            last_error = e
        except Exception as e:
            last_error = e
    if last_error:
        log(f"Tıklama başarısız: {type(last_error).__name__}: {str(last_error)[:120]}")
        save_debug_screenshot(driver, "easy_apply_click_fail")
    return False

def click_easy_apply(driver):
    locators = [
        (By.XPATH, "//button[contains(., 'Kolay Başvuru') or contains(., 'Easy Apply') or contains(@aria-label,'Kolay Başvuru') or contains(@aria-label,'Easy Apply') or contains(@class,'jobs-apply-button')]") ,
        (By.CSS_SELECTOR, "button.jobs-apply-button"),
        (By.CSS_SELECTOR, "button[data-control-name='jobdetails_topcard_inapply'], button[data-control-name='jobdetails_topcard_inapply_simple']"),
    ]

    # Try directly a few times
    for _ in range(2):
        for how, what in locators:
            try:
                btn = WebDriverWait(driver, 8).until(EC.visibility_of_element_located((how, what)))
            except TimeoutException:
                continue
            if robust_click(driver, btn):
                # Verify modal is opened
                try:
                    WebDriverWait(driver, 8).until(EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-easy-apply-modal, div.jobs-apply-form-modal, div.artdeco-modal")),
                        EC.presence_of_element_located((By.XPATH, "//button[.//span[contains(text(),'İleri') or contains(text(),'Next')]] | //button[.//span[contains(text(),'Başvuruyu gönder') or contains(text(),'Submit application')]]")),
                    ))
                    log("Kolay Başvuru butonuna tıklandı.")
                    return True
                except TimeoutException:
                    # Maybe click did not register; try next attempt
                    pass

    # If not found/clicked, click a left job card to force right panel render, then retry once
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li a[href*='/jobs/view/']")
        if cards:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", cards[0])
            human_pause(0.2, 0.4)
            driver.execute_script("arguments[0].click();", cards[0])
            human_pause(0.6, 1.0)
            close_known_overlays(driver)
            for how, what in locators:
                try:
                    btn = WebDriverWait(driver, 8).until(EC.visibility_of_element_located((how, what)))
                except TimeoutException:
                    continue
                if robust_click(driver, btn):
                    try:
                        WebDriverWait(driver, 8).until(EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-easy-apply-modal, div.jobs-apply-form-modal, div.artdeco-modal")),
                            EC.presence_of_element_located((By.XPATH, "//button[.//span[contains(text(),'İleri') or contains(text(),'Next')]] | //button[.//span[contains(text(),'Başvuruyu gönder') or contains(text(),'Submit application')]]")),
                        ))
                        log("Kolay Başvuru butonuna tıklandı.")
                        return True
                    except TimeoutException:
                        pass
    except Exception:
        pass

    log("Kolay Başvuru butonu bulunamadı.")
    return False

def simple_easy_apply(driver, resume_path):
    if not click_easy_apply(driver):
        return False
    human_pause(1, 2)
    try:
        upload_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if upload_inputs:
            upload_inputs[0].send_keys(resume_path)
            log("CV yüklendi.")
            human_pause(1.2, 2.0)
    except Exception:
        pass
    while True:
        human_pause(0.7, 1.2)
        dismiss_popups(driver)
        try:
            submit = driver.find_element(By.XPATH, "//button[.//span[contains(text(),'Başvuruyu gönder') or contains(text(),'Submit application')]]")
            driver.execute_script("arguments[0].click();", submit)
            human_pause(0.8, 1.3)
            log("Başvuru gönderildi ✅")
            try:
                close_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Kapat']")))
                driver.execute_script("arguments[0].click();", close_btn)
            except Exception:
                pass
            return True
        except NoSuchElementException:
            pass
        try:
            next_btn = driver.find_element(By.XPATH, "//button[.//span[contains(text(),'İleri') or contains(text(),'Next')]]")
            if next_btn.is_enabled():
                driver.execute_script("arguments[0].click();", next_btn)
            else:
                raise NoSuchElementException()
        except NoSuchElementException:
            log("Form karmaşık, iptal ediliyor.")
            try:
                driver.find_element(By.CSS_SELECTOR, "button[aria-label='Kapat']").click()
                human_pause(0.4, 0.8)
                driver.find_element(By.XPATH, "//button[.//span[contains(text(),'Başvuruyu iptal et') or contains(text(),'Discard')]]").click()
            except Exception:
                pass
            return False

def run():
    load_dotenv()
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    resume_path = os.getenv("RESUME_PATH")
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    if not all([email, password, resume_path]):
        print("Lütfen .env dosyasını doldurun.")
        sys.exit(1)
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    driver = launch_browser(user_data_dir, headless=headless)
    try:
        ensure_login(driver, email, password)
        queries = cfg.get("queries", ["Siber Güvenlik Uzmanı"])
        locations = cfg.get("locations", ["İstanbul, Türkiye"])
        filters = cfg.get("filters", {})
        max_pages = int(cfg.get("max_pages", 3))
        per_session_limit = int(cfg.get("per_session_limit", 10))
        applied = 0
        for q in queries:
            for loc in locations:
                url = build_search_url(q, loc, filters)
                log(f"Arama: {q} @ {loc}")
                driver.get(url)
                
                # Cookie/popup blocking
                try:
                    # Try to dismiss cookie consent
                    cookie_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='cookie-banner-accept'], button[aria-label='Accept'], button[aria-label='Kabul et']")
                    for btn in cookie_buttons:
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            human_pause(0.5, 1.0)
                            break
                except Exception:
                    pass
                
                # Wait for job listings with fallback selector
                try:
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
                    )
                except TimeoutException:
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-search-results"))
                        )
                    except TimeoutException:
                        log("İş ilanları listesi yüklenemedi.")
                        continue
                
                human_pause(1.0, 2.0)
                job_links = collect_job_links(driver, max_pages=max_pages)
                log(f"Bulunan ilan: {len(job_links)}")
                for link in job_links:
                    if applied >= per_session_limit:
                        log("Limit doldu.")
                        return
                    driver.get(link)
                    human_pause(1.0, 2.0)
                    if not is_easy_apply(driver):
                        log("Easy Apply yok.")
                        continue
                    ok = simple_easy_apply(driver, resume_path)
                    applied += 1 if ok else 0
                    human_pause(1.2, 2.2)
        log(f"Toplam gönderilen başvuru: {applied}")
    finally:
        if headless:
            driver.quit()

if __name__ == "__main__":
    run()
