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

class LinkedInBot:
    def __init__(self, config):
        self.cfg = config
        self.driver = _build_driver(config.get("headless", False))
        self.applied = []

    def login(self):
        d = self.driver
        d.get("https://www.linkedin.com/")
        time.sleep(2)
        if "feed" not in d.current_url:
            input("Lütfen bu pencerede LinkedIn'e giriş yapın, sonra burada Enter'a basın...")

    def search_and_apply(self):
        d = self.driver
        d.get("https://www.linkedin.com/jobs/search/?keywords=Yapay%20Zeka&location=Türkiye")
        time.sleep(4)
        cards = d.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")
        for card in cards:
            try:
                d.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(random.uniform(0.5,1.2))
                card.click(); time.sleep(2.0)

                title = d.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title").text
                company = d.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name a").text
                city = d.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__primary-description").text

                is_big = any(b.lower() in company.lower() for b in self.cfg["big_companies"])
                if not (city_ok(city, self.cfg["city_whitelist"]) or (self.cfg["allow_big_companies_outside_city"] and is_big)):
                    continue

                try:
                    easy = d.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
                except NoSuchElementException:
                    continue
                easy.click(); time.sleep(2)

                try:
                    textarea = d.find_element(By.TAG_NAME, "textarea")
                    cover = render_cover_letter("templates/cover_linkedin.txt", "cv_profile.yaml", company, title, city, max_len=1800)
                    textarea.clear(); textarea.send_keys(cover)
                except Exception:
                    pass

                submitted = False
                while True:
                    try:
                        submit = d.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                        submit.click(); submitted=True; time.sleep(2)
                        break
                    except NoSuchElementException:
                        try:
                            nxt = d.find_element(By.CSS_SELECTOR, "button[aria-label^='Next']")
                            nxt.click(); time.sleep(1.5)
                        except NoSuchElementException:
                            break

                if submitted:
                    self.applied.append({"platform":"LinkedIn","title":title,"company":company,"city":city})
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
