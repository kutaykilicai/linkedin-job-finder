#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Job Finder MK7 (ANALYZE-ONLY)
- LinkedIn ilanlarını tarar, açıklama metnini çeker
- CV profiline göre 0–100 skorlar
- Başvuru yapmaz, sadece listeler
- matches.json ve matches.csv üretir
"""

import os, sys, time, json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
from urllib.parse import quote_plus

from scoring_mk7 import score_job
from utils_mk7 import log, human_pause, cleanup_overlays, uniq_by, to_csv

def launch_browser(user_data_dir: Optional[str], headless: bool):
    opts = webdriver.ChromeOptions()
    if user_data_dir:
        opts.add_argument(f"--user-data-dir={user_data_dir}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def ensure_login(driver, email, password):
    driver.get("https://www.linkedin.com/")
    human_pause()
    try:
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.ID,"global-nav")))
        log("✅ Oturum açık.")
        return
    except TimeoutException: pass
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID,"username")))
    driver.find_element(By.ID,"username").send_keys(email)
    driver.find_element(By.ID,"password").send_keys(password)
    driver.find_element(By.ID,"password").submit()
    log("🔐 Giriş yapıldı, 2FA varsa tamamlayın.")
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID,"global-nav")))

def build_search_url(query, location, filters):
    base="https://www.linkedin.com/jobs/search/"
    params={"keywords":query,"location":location,
            "f_TPR":filters.get("date_posted"),
            "position":"1","pageNum":"0"}
    q="&".join([f"{k}={quote_plus(str(v))}" for k,v in params.items() if v])
    return f"{base}?{q}"

def extract_job(driver, card):
    try:
        url = card.find_element(By.CSS_SELECTOR,"a[href*='/jobs/view/']").get_attribute("href").split("?")[0]
    except: return None
    driver.execute_script("arguments[0].click();", card)
    human_pause(1,2)
    cleanup_overlays(driver)
    try:
        title = driver.find_element(By.CSS_SELECTOR,"h1").text.strip()
    except: title=""
    try:
        company = driver.find_element(By.CSS_SELECTOR,".jobs-unified-top-card__company-name").text.strip()
    except: company=""
    try:
        loc = driver.find_element(By.CSS_SELECTOR,".jobs-unified-top-card__primary-description").text.strip()
    except: loc=""
    desc_html=""
    for sel in [".jobs-description-content__text",".jobs-box__html-content"]:
        try:
            desc_html=driver.find_element(By.CSS_SELECTOR,sel).get_attribute("innerHTML")
            break
        except: continue
    desc = BeautifulSoup(desc_html,"html.parser").get_text(" ",strip=True) if desc_html else ""
    return {"job_title":title,"company":company,"location":loc,"link":url,"description":desc}

def run():
    load_dotenv()
    email=os.getenv("LINKEDIN_EMAIL"); password=os.getenv("LINKEDIN_PASSWORD")
    user_data_dir=os.getenv("CHROME_USER_DATA_DIR","")
    headless=os.getenv("HEADLESS","false").lower()=="true"
    cfg=json.load(open("config.json","r",encoding="utf-8"))
    queries=cfg.get("queries",[]); locations=cfg.get("locations",[])
    min_score=int(cfg.get("min_score",65)); max_results=int(cfg.get("max_results",20))
    driver=launch_browser(user_data_dir,headless)
    try:
        ensure_login(driver,email,password)
        harvested=[]
        for q in queries:
            for loc in locations:
                driver.get(build_search_url(q,loc,{})); human_pause(2,3)
                cards=driver.find_elements(By.CSS_SELECTOR,"ul.jobs-search__results-list li")
                for card in cards:
                    job=extract_job(driver,card)
                    if job: harvested.append(job)
        uniq={j["link"]:j for j in harvested if j.get("link")}
        results=[]
        for job in uniq.values():
            job.update(score_job(job)); results.append(job)
        results=[j for j in results if j["match_score"]>=min_score]
        results.sort(key=lambda x:x["match_score"],reverse=True)
        final=results[:max_results]
        Path("matches.json").write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding="utf-8")
        to_csv(final,"matches.csv")
        for i,j in enumerate(final,1):
            print(f"{i}) {j['job_title']} — {j['company']} ({j['match_score']}%)")
            print("   ",j['link'])
    finally:
        if headless: driver.quit()

if __name__=="__main__": run()
