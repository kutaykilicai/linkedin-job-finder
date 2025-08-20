import os
import time
import json
import random
import sys
import re
from pathlib import Path
from urllib.parse import quote_plus
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import html

# pip install selenium python-dotenv webdriver-manager beautifulsoup4
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
from bs4 import BeautifulSoup

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
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    if headless:
        opts.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
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
        "f_AL": "true" if filters.get("easy_apply_only", False) else None,
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
        human_pause(2, 3)
        
        # Popup temizle
        aggressive_popup_cleanup(driver)
        
        # Farklı seçiciler dene
        job_selectors = [
            "ul.jobs-search__results-list li a[href*='/jobs/view/']",
            ".jobs-search-results-list li a[href*='/jobs/view/']", 
            ".scaffold-layout__list-container li a[href*='/jobs/view/']",
            ".jobs-search-results-list .job-card-container a[href*='/jobs/view/']",
            "li[data-occludable-job-id] a[href*='/jobs/view/']",
            ".jobs-search-results li a[href*='/jobs/view/']"
        ]
        
        cards = []
        for selector in job_selectors:
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    log(f"İş ilanları bulundu: {len(cards)} adet (seçici: {selector})")
                    break
            except Exception as e:
                continue
                
        if not cards:
            log("❌ İş ilanı kartları bulunamadı, alternatif yöntem deneniyor...")
            # Alternatif yöntem - tüm linkleri tara
            try:
                all_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "/jobs/view/" in href:
                        cards.append(link)
                log(f"Alternatif yöntemle bulunan linkler: {len(cards)}")
            except:
                pass
        
        if not cards:
            log("❌ Bu sayfada iş ilanı bulunamadı")
            break
            
        # Linkleri topla
        page_links = 0
        for a in cards:
            try:
                url = a.get_attribute("href")
                if url and "/jobs/view/" in url:
                    clean_url = url.split("?")[0]
                    if clean_url not in links:
                        links.add(clean_url)
                        page_links += 1
            except Exception:
                continue
                
        log(f"Sayfa {page}: {page_links} yeni ilan bulundu, toplam: {len(links)}")
        
        # Sonraki sayfaya geç
        if page < max_pages:
            try:
                # Farklı next button seçicileri dene
                next_selectors = [
                    "//button[@aria-label='Sonraki' or @aria-label='Next']",
                    "//button[contains(., 'Sonraki') or contains(., 'Next')]",
                    ".artdeco-pagination__button--next",
                    "button[aria-label*='Next']",
                    ".jobs-search-pagination button:last-child"
                ]
                
                next_clicked = False
                for selector in next_selectors:
                    try:
                        if selector.startswith("//"):
                            next_btn = driver.find_element(By.XPATH, selector)
                        else:
                            next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                            
                        if next_btn.is_enabled() and next_btn.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                            human_pause(0.5, 1)
                            driver.execute_script("arguments[0].click();", next_btn)
                            log(f"Sayfa {page+1}'e geçiliyor...")
                            next_clicked = True
                            break
                    except Exception:
                        continue
                
                if next_clicked:
                    # Sayfanın yüklenmesini bekle
                    human_pause(3, 5)
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
                        )
                    except TimeoutException:
                        log("❌ Sonraki sayfa yüklenemedi")
                        break
                else:
                    log("❌ Sonraki sayfa butonu bulunamadı veya tıklanamadı")
                    break
                    
            except Exception as e:
                log(f"❌ Sayfa geçiş hatası: {e}")
                break
    
    return list(links)

def aggressive_popup_cleanup(driver):
    """Agresif popup/overlay temizleme"""
    cleanup_selectors = [
        # Cookie consent
        "button[data-testid='cookie-banner-accept']",
        "button[aria-label*='Accept']", "button[aria-label*='Kabul']",
        "button[aria-label*='Kapat']", "button[aria-label*='Close']",
        "button[aria-label*='Dismiss']", "button[aria-label*='Skip']",
        
        # Messaging overlay - mesajlaşma bölümünü kapatmak için
        "button.msg-overlay-bubble-header__control",
        ".msg-overlay-bubble-header__controls button",
        ".msg-overlay-bubble-header__control--new-convo-btn",
        "button[data-control-name='overlay.close_overlay']",
        
        # Modal/overlay close buttons
        ".artdeco-modal__dismiss", ".artdeco-modal__dismiss-btn",
        "button[data-dismiss='modal']",
        
        # Generic overlay elements
        ".global-alert__dismiss", ".notification-banner__dismiss",
        
        # LinkedIn specific popups
        "button[data-control-name='dismiss']",
    ]
    
    removed_count = 0
    for selector in cleanup_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    try:
                        driver.execute_script("arguments[0].click();", elem)
                        removed_count += 1
                        human_pause(0.1, 0.3)
                    except:
                        pass
        except:
            pass
    
    # JavaScript ile overlay temizleme ve mesajlaşma kapatma
    try:
        removed_js = driver.execute_script("""
            let removed = 0;
            
            // Mesajlaşma bölümünü kapat
            const msgElements = document.querySelectorAll('.msg-overlay-list-bubble, .msg-overlay-bubble-header, .msg-overlay-list-bubble__content');
            msgElements.forEach(el => {
                el.style.display = 'none';
                removed++;
            });
            
            // Fixed position overlays
            document.querySelectorAll('[style*="position: fixed"], [style*="position:fixed"]').forEach(el => {
                const zIndex = parseInt(window.getComputedStyle(el).zIndex || '0');
                if (zIndex > 100) {
                    el.style.display = 'none';
                    removed++;
                }
            });
            
            // High z-index elements
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                const zIndex = parseInt(style.zIndex || '0');
                if (zIndex >= 1000 && (style.position === 'fixed' || style.position === 'absolute')) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 100 && rect.height > 100) {
                        el.style.display = 'none';
                        removed++;
                    }
                }
            });
            
            return removed;
        """)
        removed_count += removed_js
    except:
        pass
    
    if removed_count > 0:
        log(f"Temizlenen popup/overlay: {removed_count}")
        human_pause(0.2, 0.5)

def extract_job_details(driver, job_url: str) -> Optional[Dict]:
    """İş ilanı detaylarını çıkar"""
    try:
        log(f"📄 İlan detayları alınıyor: {job_url}")
        driver.get(job_url)
        human_pause(2, 3)
        
        # Popup temizle (mesajlaşma dahil)
        aggressive_popup_cleanup(driver)
        
        # Sayfa yüklemesini bekle - daha geniş seçiciler
        try:
            WebDriverWait(driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__job-details")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-unified-top-card")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-view-layout")),
                )
            )
        except TimeoutException:
            log("❌ Sayfa yüklenemedi, alternatif bekleme...")
            human_pause(5, 7)  # Fazladan bekleme
        
        # İş başlığı - güncellenmiş seçiciler
        job_title = ""
        title_selectors = [
            "h1.top-card-layout__title",
            "h1.t-24", 
            ".job-details-jobs-unified-top-card__job-title h1",
            "h1[data-test-id='job-title']",
            ".jobs-unified-top-card__job-title h1",
            ".jobs-unified-top-card__job-title",
            ".job-details-jobs-unified-top-card__job-title",
            "h1.jobs-unified-top-card__job-title",
            ".artdeco-entity-lockup__title",
            "h1",  # fallback
        ]
        
        for selector in title_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                job_title = element.text.strip()
                if job_title:
                    break
            except NoSuchElementException:
                continue
        
        # Şirket adı - güncellenmiş seçiciler
        company = ""
        company_selectors = [
            ".top-card-layout__card .top-card-layout__entity-info a",
            ".job-details-jobs-unified-top-card__company-name a",
            ".jobs-unified-top-card__company-name a",
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__primary-description a",
            ".job-details-jobs-unified-top-card__primary-description a",
            ".artdeco-entity-lockup__subtitle",
            "a[data-control-name='job_details_topcard_company_link']",
            ".jobs-unified-top-card .artdeco-entity-lockup__subtitle a"
        ]
        
        for selector in company_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                company = element.text.strip()
                if company:
                    break
            except NoSuchElementException:
                continue
        
        # Lokasyon
        location = ""
        location_selectors = [
            ".top-card-layout__card .top-card-layout__entity-info-container .top-card-layout__second-subline",
            ".job-details-jobs-unified-top-card__primary-description-container .tvm__text--low-emphasis",
            ".jobs-unified-top-card__bullet",
            ".job-details-jobs-unified-top-card__primary-description"
        ]
        
        for selector in location_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    # Basit lokasyon tespiti (şehir/ülke içeriyorsa)
                    if any(keyword in text.lower() for keyword in ['istanbul', 'ankara', 'izmir', 'turkey', 'türkiye', 'remote', 'uzaktan']):
                        location = text
                        break
                if location:
                    break
            except NoSuchElementException:
                continue
        
        # İş açıklaması - Güncellenmiş ve genişletilmiş seçiciler
        description = ""
        description_selectors = [
            ".jobs-search__job-details--container .jobs-box__html-content",
            ".jobs-description-content__text",
            ".jobs-description__content",
            ".job-details-jobs-unified-top-card__job-description",
            ".jobs-box__html-content",
            "[data-job-id] .jobs-description",
            ".jobs-description",
            ".jobs-box--fadeable .jobs-box__html-content",
            ".jobs-description-content",
            ".job-details-jobs-unified-top-card .jobs-box__html-content",
            ".scaffold-layout__detail .jobs-box__html-content",
            ".job-details .jobs-description-content__text",
            "div[data-job-id] .jobs-box__html-content"
        ]
        
        for selector in description_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                description_html = element.get_attribute('innerHTML')
                if description_html:
                    # HTML'den düz metne dönüştür
                    soup = BeautifulSoup(description_html, 'html.parser')
                    description = soup.get_text(separator=' ', strip=True)
                    break
            except NoSuchElementException:
                continue
        
        # Eğer description boşsa, alternatif yöntem dene
        if not description:
            try:
                # Tüm metin içeriğini al
                page_text = driver.find_element(By.TAG_NAME, "body").text
                # İş açıklaması bölümünü bulmaya çalış
                lines = page_text.split('\n')
                desc_start = -1
                for i, line in enumerate(lines):
                    if any(keyword in line.lower() for keyword in ['iş tanımı', 'job description', 'açıklama', 'description', 'about the role', 'responsibilities']):
                        desc_start = i
                        break
                
                if desc_start > -1:
                    # Sonraki 50 satırı al (maksimum)
                    desc_lines = lines[desc_start:desc_start+50]
                    description = ' '.join(desc_lines).strip()
            except:
                pass
        
        return {
            "job_title": job_title,
            "company": company,
            "location": location,
            "link": job_url,
            "description": description
        }
        
    except Exception as e:
        log(f"İlan detayları çıkarılamadı ({job_url}): {e}")
        return None

def extract_experience_requirement(description: str) -> Tuple[str, str]:
    """Deneyim gereksinimini regex ile tespit et"""
    experience_patterns = [
        r'(\d+)\s*-\s*(\d+)\s*y[ıi]l',  # 3-5 yıl
        r'(\d+)\s*\+\s*y[ıi]l',         # 4+ yıl
        r'(\d+)\s*y[ıi]l',              # 3 yıl
        r'(\d+)\s*-\s*(\d+)\s*years?',   # 3-5 years
        r'(\d+)\s*\+\s*years?',          # 4+ years
        r'(\d+)\s*years?',               # 3 years
        r'minimum\s*(\d+)\s*y[ıi]l',     # minimum 3 yıl
        r'en az\s*(\d+)\s*y[ıi]l',      # en az 3 yıl
        r'(\d+)\s*y[ıi]ldan fazla',      # 3 yıldan fazla
        r'(\d+)\s*seneden fazla',        # 3 seneden fazla
    ]
    
    description_lower = description.lower()
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, description_lower)
        if matches:
            match = matches[0]
            if isinstance(match, tuple):
                # Range pattern (3-5 yıl)
                min_exp = int(match[0])
                max_exp = int(match[1])
                text = f"{min_exp}-{max_exp} yıl"
                
                # Deneyim yorumu
                if max_exp <= 3:
                    interpretation = "tam uyumlu (ben ~3 yıl)"
                elif min_exp <= 3 <= max_exp:
                    interpretation = "tam uyumlu (ben ~3 yıl)"
                elif min_exp == 4 and max_exp <= 5:
                    interpretation = "deneyim yakın (ben ~3 yıl)"
                elif min_exp <= 5:
                    interpretation = "deneyim yakın (ben ~3 yıl)"
                else:
                    interpretation = "deneyim fazla (ben ~3 yıl)"
                    
                return text, interpretation
            else:
                # Single number pattern
                exp_num = int(match)
                if '+' in pattern or 'fazla' in pattern or 'minimum' in pattern or 'en az' in pattern:
                    text = f"{exp_num}+ yıl"
                    if exp_num <= 3:
                        interpretation = "tam uyumlu (ben ~3 yıl)"
                    elif exp_num <= 5:
                        interpretation = "deneyim yakın (ben ~3 yıl)"
                    else:
                        interpretation = "deneyim fazla (ben ~3 yıl)"
                else:
                    text = f"{exp_num} yıl"
                    if exp_num <= 3:
                        interpretation = "tam uyumlu (ben ~3 yıl)"
                    elif exp_num <= 5:
                        interpretation = "deneyim yakın (ben ~3 yıl)"
                    else:
                        interpretation = "deneyim fazla (ben ~3 yıl)"
                        
                return text, interpretation
    
    return "belirtilmemiş", "deneyim gereksinimi belirsiz"

def calculate_job_match_score(job: Dict) -> Dict:
    """İş ilanı için eşleşme skoru hesapla"""
    description = job.get("description", "").lower()
    job_title = job.get("job_title", "").lower()
    
    # Anahtar kelime grupları ve puanları
    high_priority_keywords = {
        "it audit": 20, "information security": 18, "iso 27001": 15, "cobit": 15,
        "nist": 12, "grc": 15, "sox": 12, "cloud security": 15,
        "aws": 10, "azure": 10, "penetration testing": 15,
        "vulnerability assessment": 12, "risk management": 15, "compliance": 12,
        "bilgi güvenliği": 18, "siber güvenlik": 18, "denetim": 15,
        "uyumluluk": 12, "risk yönetimi": 15
    }
    
    medium_priority_keywords = {
        "python automation": 8, "wireshark": 6, "nessus": 8, "burp suite": 8,
        "policy": 6, "access management": 8, "incident management": 8,
        "banking audit": 10, "financial audit": 8, "control testing": 8,
        "python": 5, "otomasyon": 6, "erişim yönetimi": 8, "olay yönetimi": 8
    }
    
    engineering_keywords = {
        "elektrik mühendisi": 12, "elektronik mühendisi": 12, "electrical engineer": 12,
        "electronic engineer": 12, "güç elektroniği": 8, "power electronics": 8,
        "devre tasarımı": 6, "circuit design": 6, "endüstriyel otomasyon": 8,
        "industrial automation": 8, "spwm": 4, "igbt": 4, "mosfet": 4, "pwm": 4
    }
    
    # Negatif sinyaller
    negative_signals = {
        "helpdesk": -10, "level 2 support": -8, "l2 support": -8,
        "vardiya": -15, "shift work": -12, "7/24": -12, "24/7": -12,
        "backend development": -15, "software development": -10, "coding": -8,
        "6+ yıl": -20, "7+ yıl": -25, "8+ yıl": -30, "10+ yıl": -35,
        "sadece operasyon": -15, "operations only": -15
    }
    
    score = 0
    matched_keywords = []
    negative_points = []
    
    # Başlık ve açıklama metnini birleştir
    full_text = f"{job_title} {description}"
    
    # Yüksek öncelikli anahtar kelimeler
    for keyword, points in high_priority_keywords.items():
        if keyword in full_text:
            score += points
            matched_keywords.append(f"{keyword} (+{points})")
    
    # Orta öncelikli anahtar kelimeler
    for keyword, points in medium_priority_keywords.items():
        if keyword in full_text:
            score += points
            matched_keywords.append(f"{keyword} (+{points})")
    
    # Mühendislik anahtar kelimeleri
    for keyword, points in engineering_keywords.items():
        if keyword in full_text:
            score += points
            matched_keywords.append(f"{keyword} (+{points})")
    
    # Negatif sinyaller
    for keyword, points in negative_signals.items():
        if keyword in full_text:
            score += points  # points zaten negatif
            negative_points.append(f"{keyword} ({points})")
    
    # Deneyim gereksinimi kontrolü
    exp_text, exp_interpretation = extract_experience_requirement(description)
    experience_penalty = 0
    
    if "deneyim fazla" in exp_interpretation:
        # 6+ yıl gereksinimleri için ekstra ceza
        if any(pattern in exp_text for pattern in ["6+", "7+", "8+", "9+", "10+"]):
            experience_penalty = -20
        elif "6-" in exp_text or "7-" in exp_text:
            experience_penalty = -15
        else:
            experience_penalty = -5
    elif "deneyim yakın" in exp_interpretation:
        experience_penalty = -2
    # "tam uyumlu" için ceza yok
    
    score += experience_penalty
    if experience_penalty < 0:
        negative_points.append(f"deneyim gereksinimi ({experience_penalty})")
    
    # Minimum ve maksimum skor sınırları
    score = max(0, min(100, score))
    
    return {
        "match_score": score,
        "experience_required_text": exp_text,
        "experience_interpretation": exp_interpretation,
        "matched_keywords": matched_keywords,
        "negative_points": negative_points,
        "top_reasons": matched_keywords[:4],  # En iyi 4 sebep
        "risks_or_gaps": negative_points
    }

def filter_and_rank_jobs(jobs: List[Dict], min_score: int = 65, max_results: int = 20) -> List[Dict]:
    """İşleri filtrele ve sırala"""
    # Skorları hesapla
    for job in jobs:
        match_data = calculate_job_match_score(job)
        job.update(match_data)
    
    # Minimum skora sahip olanları filtrele
    filtered_jobs = [job for job in jobs if job.get("match_score", 0) >= min_score]
    
    # Skora göre sırala (yüksek skordan düşüğe)
    filtered_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Aynı şirketteki tekrar eden ilanları temizle
    seen_companies = set()
    unique_jobs = []
    
    for job in filtered_jobs:
        company = job.get("company", "").lower().strip()
        if company and company not in seen_companies:
            seen_companies.add(company)
            unique_jobs.append(job)
        elif not company:  # Şirket adı yoksa ekle
            unique_jobs.append(job)
    
    # Maksimum sonuç sayısını uygula
    return unique_jobs[:max_results]

def save_results_to_json(jobs: List[Dict], filename: str = "matches.json"):
    """Sonuçları JSON dosyasına kaydet"""
    output_data = []
    
    for job in jobs:
        output_data.append({
            "job_title": job.get("job_title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "link": job.get("link", ""),
            "match_score": job.get("match_score", 0),
            "experience_required_text": job.get("experience_required_text", ""),
            "experience_interpretation": job.get("experience_interpretation", ""),
            "top_reasons": job.get("top_reasons", []),
            "risks_or_gaps": job.get("risks_or_gaps", [])
        })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    log(f"✅ Sonuçlar {filename} dosyasına kaydedildi.")

def print_results(jobs: List[Dict]):
    """Sonuçları konsola yazdır"""
    if not jobs:
        log("❌ Kriterlere uygun ilan bulunamadı.")
        return
    
    log(f"\n🎯 UYGUN İŞ İLANLARI ({len(jobs)} adet):")
    log("=" * 80)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. 📋 {job.get('job_title', 'Başlık yok')}")
        print(f"   🏢 {job.get('company', 'Şirket yok')}")
        print(f"   📍 {job.get('location', 'Lokasyon yok')}")
        print(f"   🔗 {job.get('link', '')}")
        print(f"   ⭐ Eşleşme Skoru: {job.get('match_score', 0)}/100")
        print(f"   💼 Deneyim: {job.get('experience_required_text', 'belirtilmemiş')} - {job.get('experience_interpretation', '')}")
        
        if job.get('top_reasons'):
            print(f"   ✅ Güçlü yanlar: {', '.join(job.get('top_reasons', [])[:3])}")
        
        if job.get('risks_or_gaps'):
            print(f"   ⚠️  Riskler: {', '.join(job.get('risks_or_gaps', [])[:2])}")
        
        print("-" * 80)

def run():
    load_dotenv()
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    
    if not all([email, password]):
        print("❌ Lütfen .env dosyasında LINKEDIN_EMAIL ve LINKEDIN_PASSWORD'ü doldurun.")
        sys.exit(1)
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print("❌ config.json dosyası bulunamadı.")
        sys.exit(1)
    
    driver = launch_browser(user_data_dir, headless=headless)
    all_jobs = []
    
    try:
        ensure_login(driver, email, password)
        
        queries = cfg.get("queries", ["Siber Güvenlik Uzmanı"])
        locations = cfg.get("locations", ["İstanbul, Türkiye"])
        filters = cfg.get("filters", {})
        max_pages = int(cfg.get("max_pages", 3))
        min_score = int(cfg.get("min_score", 65))
        max_results = int(cfg.get("max_results", 20))
        
        total_jobs_found = 0
        processed_jobs = 0
        
        for query in queries:
            for location in locations:
                url = build_search_url(query, location, filters)
                log(f"🔍 Arama: '{query}' @ '{location}'")
                driver.get(url)
                
                # Cookie/popup temizleme
                aggressive_popup_cleanup(driver)
                
                # İş ilanları listesi yüklenmesini bekle - daha geniş seçiciler
                try:
                    WebDriverWait(driver, 45).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-search-results")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".scaffold-layout__list-container")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
                        )
                    )
                    log("✅ İş ilanları listesi yüklendi")
                except TimeoutException:
                    log("❌ İş ilanları listesi yüklenemedi, sonraki sorguya geçiliyor.")
                    continue
                
                human_pause(1.0, 2.0)
                job_links = collect_job_links(driver, max_pages=max_pages)
                total_jobs_found += len(job_links)
                log(f"📋 Bulunan ilan sayısı: {len(job_links)}")
                
                for i, job_link in enumerate(job_links, 1):
                    log(f"📄 İlan {i}/{len(job_links)}: İşleniyor...")
                    
                    job_details = extract_job_details(driver, job_link)
                    if job_details:
                        all_jobs.append(job_details)
                        processed_jobs += 1
                        log(f"✅ İlan detayları alındı: {job_details.get('job_title', 'Başlık yok')}")
                    else:
                        log("❌ İlan detayları alınamadı.")
                    
                    human_pause(1.0, 2.0)
        
        log(f"\n📊 ÖZET: {processed_jobs} ilan işlendi, {total_jobs_found} ilan toplamda bulundu")
        
        # İlanları filtrele ve sırala
        log(f"🔄 İlanlar analiz ediliyor (min skor: {min_score})...")
        matched_jobs = filter_and_rank_jobs(all_jobs, min_score=min_score, max_results=max_results)
        
        # Sonuçları göster
        print_results(matched_jobs)
        
        # JSON'a kaydet
        save_results_to_json(matched_jobs)
        
        log(f"\n🎯 Sonuç: {len(matched_jobs)} uygun ilan bulundu (min skor: {min_score})")
        
    except KeyboardInterrupt:
        log("⏹️  İşlem kullanıcı tarafından durduruldu.")
    except Exception as e:
        log(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if headless:
            driver.quit()
        else:
            log("Tarayıcı açık bırakılıyor. Manuel olarak kapatabilirsiniz.")

if __name__ == "__main__":
    run()
