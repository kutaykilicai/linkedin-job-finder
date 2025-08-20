import os, time, yaml, pandas as pd, random, pathlib
from dotenv import load_dotenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from cover_letter import render_cover_letter

def _build_driver(headless=False):
    options = Options()
    # Profil yolunu otomatik bul
    userprofile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    chrome_profile = pathlib.Path(userprofile, "AppData", "Local", "Google", "Chrome", "User Data")
    options.add_argument(f"--user-data-dir={chrome_profile}")
    options.add_argument("--profile-directory=Default")  # farklıysa "Profile 1" vb.
    options.add_argument("--start-maximized")

    # Çökmeleri azaltan stabilite bayrakları
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")

    # headless kullanacaksan:
    # if headless: options.add_argument("--headless=new")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              options=options)
    return driver

def handle_cookies_popups(driver):
    """Çerez ve popup'ları kapat"""
    wait = WebDriverWait(driver, 5)
    
    # LinkedIn için çerez butonları
    cookie_selectors = [
        "button[data-control-name='accept_cookies']",
        "button[aria-label*='Accept']",
        "button[aria-label*='Accept all']",
        "button:contains('Accept')",
        "button:contains('Accept all')",
        "button:contains('Allow')",
        "button:contains('Allow all')",
        "#accept-cookies",
        ".accept-cookies",
        "[data-testid='accept-cookies']"
    ]
    
    for selector in cookie_selectors:
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            cookie_btn.click()
            time.sleep(random.uniform(0.5, 1.5))
            break
        except:
            continue
    
    # Popup kapatma butonları
    popup_selectors = [
        "button[aria-label*='Dismiss']",
        "button[aria-label*='Close']",
        ".close",
        ".popup-close",
        "[data-testid='close']",
        "button:contains('×')",
        "button:contains('Close')"
    ]
    
    for selector in popup_selectors:
        try:
            popup_btn = driver.find_element(By.CSS_SELECTOR, selector)
            popup_btn.click()
            time.sleep(random.uniform(0.5, 1.5))
        except:
            continue

def city_ok(job_city, whitelist):
    job_city_low = (job_city or "").lower()
    return any(c in job_city_low for c in whitelist)

class LinkedInBot:
    def __init__(self, config):
        self.cfg = config
        load_dotenv()
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.resume_path = os.getenv("RESUME_PATH")
        self.driver = _build_driver(self.cfg.get("headless", False))
        self.applied = []

    def login(self):
        d = self.driver
        d.get("https://www.linkedin.com/")
        time.sleep(random.uniform(1.2, 2.8))
        
        # Çerez/izin pop-up'larını kapat
        handle_cookies_popups(d)
        
        # Giriş kontrolü
        if "feed" not in d.current_url:
            input("Lütfen bu pencerede elle giriş yapın ve Enter'a basın...")
            time.sleep(random.uniform(1.2, 2.8))

    def search_and_apply(self):
        d = self.driver
        wait = WebDriverWait(d, 10)
        
        d.get("https://www.linkedin.com/jobs/search/?keywords=Yapay%20Zeka&location=Türkiye")
        time.sleep(random.uniform(2.0, 4.0))

        # Çerez/popup'ları tekrar kontrol et
        handle_cookies_popups(d)
        
        # İş kartlarını bekle ve bul
        cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.jobs-search__results-list li")))
        
        for idx, card in enumerate(cards):
            try:
                card.click()
                time.sleep(random.uniform(1.2, 2.8))
                title = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title"))).text
                company = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name a"))).text
                city = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__primary-description"))).text

                is_big = any(b.lower() in company.lower() for b in self.cfg["big_companies"])
                if not (city_ok(city, self.cfg["city_whitelist"]) or (self.cfg["allow_big_companies_outside_city"] and is_big)):
                    continue

                # Only Easy Apply
                try:
                    easy = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jobs-apply-button")))
                except TimeoutException:
                    continue

                easy.click()
                time.sleep(random.uniform(1.5, 3.0))

                # Try upload resume if uploader exists
                try:
                    upload = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=file]")))
                    upload.send_keys(self.resume_path)
                    time.sleep(random.uniform(1.5, 2.5))
                except TimeoutException:
                    pass

                # Cover letter textarea (if present)
                try:
                    textarea = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
                    cover = render_cover_letter("templates/cover_linkedin.txt", "cv_profile.yaml", company, title, city)
                    textarea.clear()
                    textarea.send_keys(cover[:1800])
                    time.sleep(random.uniform(0.8, 1.5))
                except TimeoutException:
                    pass

                # Click Next/Submit buttons until finish
                while True:
                    try:
                        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Submit application']")))
                        submit.click()
                        time.sleep(random.uniform(2.0, 3.5))
                        break
                    except TimeoutException:
                        try:
                            nbtn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label^='Next']")))
                            nbtn.click()
                            time.sleep(random.uniform(1.5, 2.5))
                        except TimeoutException:
                            break

                self.applied.append({"platform":"LinkedIn","title":title,"company":company,"city":city})
                if len(self.applied) >= self.cfg["max_daily_applications"]:
                    break
            except Exception:
                continue

    def save_log(self):
        import json, pathlib
        df = pd.DataFrame(self.applied)
        df.to_csv("data/applied_log.csv", index=False, encoding="utf-8")
        df.to_json("data/applied_log.json", force_ascii=False, orient="records", indent=2)

    def close(self):
        self.driver.quit()
