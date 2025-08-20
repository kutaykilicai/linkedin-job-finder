import os, time, yaml, pandas as pd, random, pathlib
from dotenv import load_dotenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    
    # KariyerNet için çerez butonları
    cookie_selectors = [
        "button[data-testid='accept-cookies']",
        "button:contains('Kabul Et')",
        "button:contains('Accept')",
        "button:contains('Accept all')",
        "button:contains('Allow')",
        "button:contains('Allow all')",
        "#accept-cookies",
        ".accept-cookies",
        ".cookie-accept",
        "[data-testid='cookie-accept']"
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
        "button[aria-label*='Kapat']",
        "button[aria-label*='Close']",
        ".close",
        ".popup-close",
        "[data-testid='close']",
        "button:contains('×')",
        "button:contains('Close')",
        "button:contains('Kapat')"
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

class KariyerNetBot:
    def __init__(self, config):
        self.cfg = config
        load_dotenv()
        self.email = os.getenv("KARIYERNET_EMAIL")
        self.password = os.getenv("KARIYERNET_PASSWORD")
        self.resume_path = os.getenv("RESUME_PATH")
        self.driver = _build_driver(self.cfg.get("headless", False))
        self.applied = []

    def login(self):
        d = self.driver
        d.get("https://www.kariyer.net/")
        time.sleep(random.uniform(1.2, 2.8))
        
        # Çerez/izin pop-up'larını kapat
        handle_cookies_popups(d)
        
        # Giriş kontrolü - KariyerNet için farklı kontrol
        if "giris" in d.current_url or "login" in d.current_url:
            input("Lütfen bu pencerede elle giriş yapın ve Enter'a basın...")
            time.sleep(random.uniform(1.2, 2.8))

    def search_and_apply(self):
        d = self.driver
        wait = WebDriverWait(d, 10)
        
        d.get("https://www.kariyer.net/is-ilanlari/#kw=yapay%20zeka&loc=istanbul")
        time.sleep(random.uniform(2.0, 4.0))

        # Çerez/popup'ları tekrar kontrol et
        handle_cookies_popups(d)
        
        # İş ilanlarını bekle ve bul
        jobs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article")))
        
        for j in jobs:
            try:
                j.click()
                time.sleep(random.uniform(1.2, 2.8))
                title = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))).text
                company = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='company-name']"))).text
                city = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-location']"))).text

                if not city_ok(city, self.cfg["city_whitelist"]):
                    is_big = any(b.lower() in company.lower() for b in self.cfg["big_companies"])
                    if not (self.cfg["allow_big_companies_outside_city"] and is_big):
                        continue

                try:
                    apply_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='apply-button']")))
                except TimeoutException:
                    continue

                apply_btn.click()
                time.sleep(random.uniform(1.5, 3.0))

                try:
                    textarea = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
                    cover = render_cover_letter("templates/cover_kariyernet.txt", "cv_profile.yaml", company, title, city)
                    textarea.clear()
                    textarea.send_keys(cover[:1200])
                    time.sleep(random.uniform(0.8, 1.5))
                except TimeoutException:
                    pass

                try:
                    submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
                    submit.click()
                    time.sleep(random.uniform(2.0, 3.5))
                except TimeoutException:
                    pass

                self.applied.append({"platform":"Kariyer.net","title":title,"company":company,"city":city})
                if len(self.applied) >= self.cfg["max_daily_applications"]:
                    break
            except Exception:
                continue

    def save_log(self):
        import json, os
        df = pd.DataFrame(self.applied)
        mode = "a" if os.path.exists("data/applied_log.csv") else "w"
        header = not os.path.exists("data/applied_log.csv")
        df.to_csv("data/applied_log.csv", index=False, encoding="utf-8", mode=mode, header=header)
        try:
            existing = []
            if os.path.exists("data/applied_log.json"):
                import json as _json
                existing = _json.loads(open("data/applied_log.json","r",encoding="utf-8").read())
            existing.extend(self.applied)
            open("data/applied_log.json","w",encoding="utf-8").write(_json.dumps(existing, ensure_ascii=False, indent=2))
        except Exception:
            pass

    def close(self):
        self.driver.quit()
