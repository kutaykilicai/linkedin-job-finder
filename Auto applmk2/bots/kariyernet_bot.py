import time, random, pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from cover_letter import render_cover_letter

def _build_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir=C:/Users/Kutay/AppData/Local/Google/Chrome/User Data")
    options.add_argument("--profile-directory=Default")  # Varsayılan profil
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def city_ok(job_city, whitelist):
    j = (job_city or "").lower()
    return any(c in j for c in whitelist)

class KariyerNetBot:
    def __init__(self, config):
        self.cfg = config
        self.driver = _build_driver(config.get("headless", False))
        self.applied = []

    def login(self):
        d = self.driver
        d.get("https://www.kariyer.net/")
        time.sleep(3)
        if "girisyap" in d.current_url or "login" in d.current_url or "kaydol" in d.page_source.lower():
            input("Lütfen bu pencerede Kariyer.net'e giriş yapın, sonra burada Enter'a basın...")

    def search_and_apply(self):
        d = self.driver
        d.get("https://www.kariyer.net/is-ilanlari/#kw=yapay%20zeka&loc=istanbul")
        time.sleep(4)
        jobs = d.find_elements(By.CSS_SELECTOR, "article")
        for j in jobs:
            try:
                d.execute_script("arguments[0].scrollIntoView(true);", j)
                time.sleep(random.uniform(0.5,1.2))
                j.click(); time.sleep(2)

                title = d.find_element(By.CSS_SELECTOR, "h1").text
                company = d.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
                city = d.find_element(By.CSS_SELECTOR, "[data-testid='job-location']").text

                if not city_ok(city, self.cfg["city_whitelist"]):
                    is_big = any(b.lower() in company.lower() for b in self.cfg["big_companies"])
                    if not (self.cfg["allow_big_companies_outside_city"] and is_big):
                        continue

                try:
                    apply_btn = d.find_element(By.CSS_SELECTOR, "[data-testid='apply-button']")
                except NoSuchElementException:
                    continue
                apply_btn.click(); time.sleep(2)

                try:
                    textarea = d.find_element(By.TAG_NAME, "textarea")
                    cover = render_cover_letter("templates/cover_kariyernet.txt", "cv_profile.yaml", company, title, city, max_len=1200)
                    textarea.clear(); textarea.send_keys(cover)
                except Exception:
                    pass

                try:
                    submit = d.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    submit.click(); time.sleep(2)
                    self.applied.append({"platform":"Kariyer.net","title":title,"company":company,"city":city})
                except Exception:
                    pass

                if len(self.applied) >= self.cfg["max_daily_applications"]:
                    break
            except Exception:
                continue

    def save_log(self):
        df = pd.DataFrame(self.applied)
        df.to_csv("data/applied_log.csv", index=False, encoding="utf-8")
        df.to_json("data/applied_log.json", orient="records", indent=2, force_ascii=False)

    def close(self):
        self.driver.quit()
