
import os
import time
import json
import random
import sys
from pathlib import Path
from urllib.parse import quote_plus

# pip install undetected-chromedriver selenium python-dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from dotenv import load_dotenv

def log(msg):
    print(time.strftime("[%H:%M:%S]"), msg, flush=True)

def human_pause(a=0.8, b=1.8):
    time.sleep(random.uniform(a, b))

def launch_browser(user_data_dir, headless=False):
    log("Chrome başlatılıyor... (profil: %s)" % user_data_dir)
    opts = uc.ChromeOptions()
    if user_data_dir:
        opts.add_argument(f"--user-data-dir={user_data_dir}")
        # LinkedIn 2FA'yı azaltmak için sabit profil kullanıyoruz
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    if headless:
        opts.add_argument("--headless=new")
    driver = uc.Chrome(options=opts)
    return driver

def ensure_login(driver, email, password):
    driver.get("https://www.linkedin.com/")
    human_pause()
    # If already logged in, home feed appears with "Me" nav
    try:
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.ID, "global-nav")))
        log("Zaten oturum açık görünüyor.")
        return
    except TimeoutException:
        pass

    log("Giriş sayfası yükleniyor...")
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "username")))

    u = driver.find_element(By.ID, "username")
    p = driver.find_element(By.ID, "password")
    u.clear(); u.send_keys(email); human_pause(0.4, 0.9)
    p.clear(); p.send_keys(password); human_pause(0.4, 0.9)
    p.submit()

    # 2FA olabilir: kullanıcıya bırakıyoruz
    log("Giriş yapıldı. 2FA istenirse tamamlayın. 60 sn bekliyorum...")
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "global-nav")))
    except TimeoutException:
        log("Uyarı: 2FA veya güvenlik doğrulaması gerekebilir. Devam etmeyi deneyeceğim.")

def build_search_url(query, location, filters):
    base = "https://www.linkedin.com/jobs/search/"
    params = {
        "keywords": query,
        "location": location,
        "f_AL": "true" if filters.get("easy_apply_only", True) else None,
        "f_WT": filters.get("work_type"),         # 1=On-site, 2=Remote, 3=Hybrid
        "f_E": filters.get("experience_levels"),  # e.g. "2,3" for Associate/Mid
        "f_TPR": filters.get("date_posted"),      # r86400=24h, r604800=Past Week, r2592000=Past Month
        "f_C": filters.get("company_ids"),        # comma company ids (optional)
        "position": "1",
        "pageNum": "0",
    }
    # build query string, ignore None
    parts = []
    for k,v in params.items():
        if v is None or v == "":
            continue
        parts.append(f"{k}={quote_plus(str(v))}")
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
        # try next page
        try:
            next_btn = driver.find_element(By.XPATH, "//button[@aria-label='Sonraki' or @aria-label='Next']")
            if next_btn.is_enabled():
                driver.execute_script("arguments[0].click();", next_btn)
                log(f"Sonraki sayfaya geçiliyor (sayfa {page+1})...")
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
    # generic popups
    for sel in [
        "button[aria-label='Kapat']",
        "button[aria-label='Dismiss']",
        "button[aria-label='Close']",
        "button[aria-label='Skip']",
    ]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                if e.is_displayed():
                    driver.execute_script("arguments[0].click();", e)
                    human_pause(0.3, 0.6)
        except Exception:
            pass

def simple_easy_apply(driver, resume_path):
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
        driver.execute_script("arguments[0].click();", btn)
        human_pause(1, 2)
    except Exception:
        log("Easy Apply butonu tıklanamadı.")
        return False

    # try upload resume if a file input is present on first step
    try:
        upload_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if upload_inputs:
            f = upload_inputs[0]
            f.send_keys(resume_path)
            log("Özgeçmiş yüklendi.")
            human_pause(1.2, 2.0)
    except Exception:
        pass

    # Iterate steps until "Review" or "Submit application"
    while True:
        human_pause(0.7, 1.2)
        dismiss_popups(driver)
        # If "Submit" exists, click and exit
        submit = None
        for sel in [
            "//button[.//span[contains(text(),'Başvuruyu gönder')]]",
            "//button[.//span[contains(text(),'Submit application')]]",
            "//button[contains(@aria-label,'Başvuruyu gönder')]",
            "//button[contains(@aria-label,'Submit application')]",
        ]:
            try:
                submit = driver.find_element(By.XPATH, sel)
                if submit:
                    driver.execute_script("arguments[0].click();", submit)
                    human_pause(0.8, 1.3)
                    log("Başvuru gönderildi ✅")
                    # Close dialog
                    try:
                        close_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Kapat']"))
                        )
                        driver.execute_script("arguments[0].click();", close_btn)
                    except Exception:
                        pass
                    return True
            except NoSuchElementException:
                pass

        # Else click "Next"
        next_btn = None
        for sel in [
            "//button[.//span[contains(text(),'İleri')]]",
            "//button[.//span[contains(text(),'Next')]]",
        ]:
            try:
                next_btn = driver.find_element(By.XPATH, sel)
                if next_btn and next_btn.is_enabled():
                    driver.execute_script("arguments[0].click();", next_btn)
                    break
            except NoSuchElementException:
                pass

        if not next_btn:
            # if we reach a complex application (asks many fields) -> discard
            log("Form çok adımlı/karmaşık görünüyor, iptal ediliyor.")
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
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR")  # örn: C:\Users\Kullanıcı\AppData\Local\Google\Chrome\User Data\kutay-bot
    headless = os.getenv("HEADLESS", "false").lower() == "true"

    if not all([email, password, resume_path]):
        print("Lütfen .env dosyasını doldurun (LINKEDIN_EMAIL, LINKEDIN_PASSWORD, RESUME_PATH).")
        sys.exit(1)

    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    driver = launch_browser(user_data_dir, headless=headless)
    try:
        ensure_login(driver, email, password)

        queries = cfg.get("queries", ["Siber Güvenlik Uzmanı"])
        locations = cfg.get("locations", ["İstanbul, Türkiye"])
        filters = cfg.get("filters", {
            "easy_apply_only": True,
            "date_posted": "r604800",  # Past Week
            "experience_levels": None, # "2,3"
            "work_type": None,         # 1 onsite,2 remote,3 hybrid
        })
        max_pages = int(cfg.get("max_pages", 3))
        per_session_limit = int(cfg.get("per_session_limit", 10))

        applied = 0
        for q in queries:
            for loc in locations:
                url = build_search_url(q, loc, filters)
                log(f"Arama: {q} @ {loc}")
                driver.get(url)
                WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list")))
                human_pause(1.0, 2.0)

                job_links = collect_job_links(driver, max_pages=max_pages)
                log(f"Bulunan ilan: {len(job_links)}")

                for link in job_links:
                    if applied >= per_session_limit:
                        log("Günlük limit doldu, çıkılıyor.")
                        return
                    driver.get(link)
                    human_pause(1.0, 2.0)
                    if not is_easy_apply(driver):
                        log("Easy Apply yok, geçiliyor.")
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
