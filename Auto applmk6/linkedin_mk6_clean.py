#!/usr/bin/env python3
"""
LinkedIn İş İlanı Analiz Botu MK6 - Temiz Mimari
Amaç: LinkedIn ilanlarını tarayıp CV'me göre uygunluk skoru hesaplamak
Önemli: KEsİNLİKLE otomatik başvuru yapmaz, sadece analiz eder
"""

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

# Gerekli paketler: pip install selenium python-dotenv webdriver-manager beautifulsoup4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException,
    StaleElementReferenceException, ElementNotInteractableException
)
from dotenv import load_dotenv
from bs4 import BeautifulSoup


# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

def log(msg: str) -> None:
    """Zaman damgalı log mesajı yazdır"""
    print(time.strftime("[%H:%M:%S]"), msg, flush=True)

def human_pause(min_sec: float = 0.8, max_sec: float = 1.8) -> None:
    """İnsan benzeri rastgele bekleme"""
    time.sleep(random.uniform(min_sec, max_sec))

def debug_current_page(driver: webdriver.Chrome) -> None:
    """Mevcut sayfanın bilgilerini debug için göster"""
    try:
        current_url = driver.current_url
        page_title = driver.title
        log(f"🔍 Debug - URL: {current_url}")
        log(f"🔍 Debug - Başlık: {page_title}")
        
        # Sayfa yüklenmiş mi kontrol et
        ready_state = driver.execute_script("return document.readyState")
        log(f"🔍 Debug - Sayfa durumu: {ready_state}")
        
    except Exception as e:
        log(f"🔍 Debug hatası: {e}")

def safe_retry(func, max_attempts: int = 3, delay: float = 1.0, *args, **kwargs):
    """Fonksiyonu güvenli şekilde yeniden dene"""
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            log(f"Hata (deneme {attempt + 1}/{max_attempts}): {e}")
            time.sleep(delay * (attempt + 1))
    return None


# ============================================================================
# TARAYICI YÖNETİMİ
# ============================================================================

def launch_browser(user_data_dir: Optional[str] = None, headless: bool = False) -> webdriver.Chrome:
    """Chrome tarayıcısını başlat ve yapılandır"""
    log("Chrome başlatılıyor...")
    
    opts = webdriver.ChromeOptions()
    
    # Temel ayarlar - GÜNCELLE: Ayrı profil kullan (conflict engellemek için)
    if user_data_dir and user_data_dir.strip():
        opts.add_argument(f"--user-data-dir={user_data_dir}")
        log(f"Chrome profil: {user_data_dir}")
    else:
        # Selenium için ayrı profil klasörü oluştur
        import tempfile
        temp_profile = os.path.join(tempfile.gettempdir(), "linkedin_mk6_chrome_profile")
        opts.add_argument(f"--user-data-dir={temp_profile}")
        log(f"Selenium profil kullanılıyor: {temp_profile}")
    
    # Profil çakışması engelleyici ayarlar
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--disable-extensions-file-access-check")
    opts.add_argument("--disable-extensions-http-throttling")
    
    # Anti-detection ve stabilite ayarları
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")  # Headless için gerekli
    opts.add_argument("--disable-extensions")
    opts.add_argument("--no-first-run")
    opts.add_argument("--disable-default-apps")
    opts.add_argument("--disable-background-timer-throttling")
    opts.add_argument("--disable-backgrounding-occluded-windows")
    opts.add_argument("--disable-features=TranslateUI")
    opts.add_argument("--disable-ipc-flooding-protection")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-search-engine-choice-screen")
    
    if not headless:
        opts.add_argument("--start-maximized")
    else:
        # Headless modda pencere boyutu ayarla
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--headless=new")
        log("Headless mod aktif")
    
    # Performans ve güvenlik ayarları
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,  # Resimleri aç (LinkedIn için gerekli)
        "profile.default_content_setting_values.geolocation": 2,
        "profile.default_content_setting_values.media_stream": 2,
        "profile.default_content_settings.media_stream": 2,
        "profile.default_content_setting_values.cookies": 1,
        "profile.default_content_setting_values.javascript": 1,
        "profile.managed_default_content_settings.cookies": 1
    }
    opts.add_experimental_option("prefs", prefs)
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option('useAutomationExtension', False)
    
    # Network ve DNS ayarları
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    opts.add_argument("--remote-debugging-port=0")  # Rastgele port
    
    # Kullanıcı ajanı ayarla
    opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        # Driver'ı başlat
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        
        # WebDriver özelliğini gizle
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        
        log("✅ Chrome başarıyla başlatıldı")
        return driver
        
    except Exception as e:
        log(f"❌ Chrome başlatma hatası: {e}")
        raise

def cleanup_overlays(driver: webdriver.Chrome) -> None:
    """Popup, overlay ve mesajlaşma balonlarını temizle"""
    overlay_selectors = [
        # Mesajlaşma overlayları
        "button.msg-overlay-bubble-header__control",
        ".msg-overlay-bubble-header__controls button",
        "button[data-control-name='overlay.close_overlay']",
        "button[aria-label*='Mesaj']", "button[aria-label*='messaging']",
        
        # Cookie ve genel popuplar
        "button[data-testid='cookie-banner-accept']",
        "button[aria-label*='Accept']", "button[aria-label*='Kabul']",
        "button[aria-label*='Kapat']", "button[aria-label*='Close']",
        "button[aria-label*='Dismiss']", "button[aria-label*='Skip']",
        
        # Modal kapatma butonları
        ".artdeco-modal__dismiss", ".artdeco-modal__dismiss-btn",
        "button[data-dismiss='modal']",
        ".global-alert__dismiss", ".notification-banner__dismiss"
    ]
    
    closed_count = 0
    for selector in overlay_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    try:
                        driver.execute_script("arguments[0].click();", elem)
                        closed_count += 1
                        human_pause(0.1, 0.3)
                    except:
                        pass
        except:
            pass
    
    # JavaScript ile kapsamlı temizleme
    try:
        js_removed = driver.execute_script("""
            let removed = 0;
            
            // Mesajlaşma elementlerini kaldır
            const msgElements = document.querySelectorAll('.msg-overlay-list-bubble, .msg-overlay-bubble-header, .messaging-tab-button');
            msgElements.forEach(el => {
                el.style.display = 'none';
                el.remove();
                removed++;
            });
            
            // Yüksek z-index'li fixed elementleri gizle
            document.querySelectorAll('[style*="position: fixed"]').forEach(el => {
                const zIndex = parseInt(window.getComputedStyle(el).zIndex || '0');
                if (zIndex > 100) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 50) {
                        el.style.display = 'none';
                        removed++;
                    }
                }
            });
            
            return removed;
        """)
        closed_count += js_removed
    except:
        pass
    
    if closed_count > 0:
        log(f"🧹 {closed_count} popup/overlay temizlendi")


# ============================================================================
# GİRİŞ YÖNETİMİ
# ============================================================================

def login_and_nav(driver: webdriver.Chrome, email: str, password: str) -> bool:
    """LinkedIn'e giriş yap - iyileştirilmiş versiyon"""
    try:
        log("LinkedIn giriş kontrolü başlıyor...")
        
        # Debug: Başlangıç durumu
        debug_current_page(driver)
        
        # Önce ana sayfayı kontrol et - URL yönlendirmesini zorla
        log("LinkedIn ana sayfasına gidiliyor...")
        try:
            driver.get("https://www.linkedin.com/")
            human_pause(3, 5)
            
            # Debug: LinkedIn sayfası sonrası
            debug_current_page(driver)
            
            # Sayfanın yüklendiğini doğrula
            current_url = driver.current_url
            log(f"Mevcut URL: {current_url}")
            
            if "google.com" in current_url or current_url == "about:blank":
                log("⚠️ LinkedIn'e yönlendirme başarısız, tekrar deneniyor...")
                driver.execute_script("window.location.href = 'https://www.linkedin.com/';")
                human_pause(3, 5)
                
                # Debug: İkinci deneme sonrası
                debug_current_page(driver)
                current_url = driver.current_url
                log(f"İkinci deneme URL: {current_url}")
                
        except Exception as e:
            log(f"❌ LinkedIn navigasyon hatası: {e}")
        
        # Overlay'leri temizle
        cleanup_overlays(driver)
        
        # Zaten giriş yapılmış mı kontrol et
        login_indicators = [
            "nav[aria-label='Ana LinkedIn menüsü']",
            "#global-nav",
            ".global-nav",
            "[data-test-id='nav-top-navs']",
            ".top-card-layout"
        ]
        
        for indicator in login_indicators:
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                )
                log("✅ Zaten oturum açık")
                return True
            except TimeoutException:
                continue
        
        # Giriş sayfasına git
        log("LinkedIn giriş sayfasına yönlendiriliyor...")
        try:
            driver.get("https://www.linkedin.com/login")
            human_pause(3, 5)
            
            # Login sayfasının yüklendiğini doğrula
            current_url = driver.current_url
            log(f"Login sayfası URL: {current_url}")
            
            if "google.com" in current_url or "login" not in current_url:
                log("⚠️ Login sayfasına yönlendirme başarısız, JavaScript ile deneniyor...")
                driver.execute_script("window.location.href = 'https://www.linkedin.com/login';")
                human_pause(3, 5)
                current_url = driver.current_url
                log(f"JavaScript sonrası URL: {current_url}")
                
                if "login" not in current_url:
                    log("❌ Login sayfasına erişim sağlanamadı")
                    return False
                    
        except Exception as e:
            log(f"❌ Login sayfası navigasyon hatası: {e}")
            return False
        
        # Giriş formunu bekle ve doldur
        try:
            username_selectors = ["#username", "input[name='session_key']", "input[autocomplete='username']"]
            password_selectors = ["#password", "input[name='session_password']", "input[autocomplete='current-password']"]
            
            username_elem = None
            for selector in username_selectors:
                try:
                    username_elem = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not username_elem:
                log("❌ Email input bulunamadı")
                return False
            
            # Email gir
            username_elem.clear()
            username_elem.send_keys(email)
            human_pause(0.5, 1)
            log("📧 Email girildi")
            
            # Şifre input'unu bul
            password_elem = None
            for selector in password_selectors:
                try:
                    password_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not password_elem:
                log("❌ Şifre input bulunamadı")
                return False
            
            # Şifre gir
            password_elem.clear()
            password_elem.send_keys(password)
            human_pause(0.5, 1)
            log("🔑 Şifre girildi")
            
            # Giriş butonunu bul ve tıkla
            login_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".btn__primary--large",
                "button[data-id='sign-in-form__submit-btn']"
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].click();", btn)
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                # Fallback: Enter tuşu
                password_elem.submit()
            
            log("🚀 Giriş butonu tıklandı, sonuç bekleniyor...")
            
        except Exception as e:
            log(f"❌ Form doldurma hatası: {e}")
            return False
        
        # Giriş sonucunu bekle (2FA dahil)
        for attempt in range(12):  # 60 saniye toplam (5*12)
            human_pause(5, 5)
            
            # Başarılı giriş kontrolü
            current_url = driver.current_url
            log(f"Mevcut URL: {current_url}")
            
            # LinkedIn ana sayfasındayız mı?
            if any(indicator in current_url.lower() for indicator in ['/feed', '/in/', '/mynetwork', '/jobs']):
                log("✅ LinkedIn'e başarıyla giriş yapıldı!")
                return True
            
            # Ana navigasyon var mı?
            for indicator in login_indicators:
                try:
                    driver.find_element(By.CSS_SELECTOR, indicator)
                    log("✅ LinkedIn'e başarıyla giriş yapıldı!")
                    return True
                except:
                    continue
            
            # Hala giriş sayfasındayız mı?
            if '/login' in current_url:
                if attempt < 8:  # İlk 40 saniye
                    log(f"⏳ Giriş bekleniyor... ({attempt + 1}/12) - 2FA gerekebilir")
                else:
                    log("❌ Giriş zaman aşımı - lütfen 2FA'yı manuel tamamlayın")
            else:
                log(f"🔄 Beklenmeyen sayfa: {current_url}")
        
        log("❌ Giriş zaman aşımı")
        return False
        
    except Exception as e:
        log(f"❌ Giriş hatası: {e}")
        return False


# ============================================================================
# İLAN TOPLAMA VE ÇIKARMA
# ============================================================================

def build_search_url(query: str, location: str, filters: Dict) -> str:
    """LinkedIn iş arama URL'si oluştur"""
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
    
    # Sadece değeri olan parametreleri ekle
    param_list = [f"{k}={quote_plus(str(v))}" for k, v in params.items() if v is not None]
    return base + "?" + "&".join(param_list)

def collect_job_cards(driver: webdriver.Chrome, max_pages: int = 3) -> List[Dict]:
    """İş ilanı kartlarını topla ve temel bilgileri çıkar"""
    all_jobs = []
    
    for page in range(1, max_pages + 1):
        log(f"📄 Sayfa {page} taranıyor...")
        human_pause(2, 3)
        
        # Overlay'leri temizle
        cleanup_overlays(driver)
        
        # İş kartlarını bul
        job_card_selectors = [
            "ul.jobs-search__results-list li",
            ".jobs-search-results-list li", 
            ".scaffold-layout__list-container li",
            "li[data-occludable-job-id]"
        ]
        
        cards = []
        for selector in job_card_selectors:
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    break
            except:
                continue
        
        if not cards:
            log("❌ Bu sayfada iş kartı bulunamadı")
            break
        
        log(f"✅ {len(cards)} iş kartı bulundu")
        
        # Her kartı işle
        page_jobs = 0
        for i, card in enumerate(cards):
            try:
                # Kart linkini bul
                link_elem = card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                job_url = link_elem.get_attribute("href").split("?")[0]
                
                # Karttan temel bilgileri çıkar
                job_basic = extract_basic_from_card(card)
                if job_basic:
                    job_basic["link"] = job_url
                    
                    # Kartı tıklayıp detayları al
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", link_elem)
                        human_pause(0.5, 1)
                        driver.execute_script("arguments[0].click();", link_elem)
                        human_pause(2, 3)
                        
                        # Detaylı açıklama çıkar
                        description = extract_job_description(driver)
                        job_basic["description"] = description
                        
                        all_jobs.append(job_basic)
                        page_jobs += 1
                        
                        log(f"✅ {i+1}/{len(cards)}: {job_basic.get('job_title', 'Başlık yok')[:40]}...")
                        
                    except Exception as e:
                        log(f"⚠️ Kart {i+1} detay hatası: {e}")
                        
            except Exception as e:
                log(f"⚠️ Kart {i+1} işleme hatası: {e}")
                continue
        
        log(f"📊 Sayfa {page}: {page_jobs} ilan işlendi")
        
        # Sonraki sayfaya geç
        if page < max_pages:
            if not navigate_to_next_page(driver):
                log("❌ Sonraki sayfaya geçilemedi")
                break
    
    return all_jobs

def extract_basic_from_card(card_element) -> Optional[Dict]:
    """İş kartından temel bilgileri çıkar"""
    try:
        # Başlık
        title_selectors = [
            "h3.base-search-card__title a",
            ".job-card-list__title a",
            "a[data-control-name='job_search_job_result_title']"
        ]
        job_title = ""
        for selector in title_selectors:
            try:
                elem = card_element.find_element(By.CSS_SELECTOR, selector)
                job_title = elem.text.strip()
                break
            except:
                continue
        
        # Şirket
        company_selectors = [
            "h4.base-search-card__subtitle a",
            ".job-card-container__company-name",
            "a[data-control-name='job_search_job_result_company_name']"
        ]
        company = ""
        for selector in company_selectors:
            try:
                elem = card_element.find_element(By.CSS_SELECTOR, selector)
                company = elem.text.strip()
                break
            except:
                continue
        
        # Lokasyon
        location_selectors = [
            ".job-search-card__location",
            ".base-search-card__metadata .job-search-card__location"
        ]
        location = ""
        for selector in location_selectors:
            try:
                elem = card_element.find_element(By.CSS_SELECTOR, selector)
                location = elem.text.strip()
                break
            except:
                continue
        
        return {
            "job_title": job_title,
            "company": company,
            "location": location,
            "description": ""
        }
        
    except Exception as e:
        return None

def extract_job_description(driver: webdriver.Chrome) -> str:
    """İş açıklamasını mevcut sayfadan çıkar"""
    # "Daha fazla göster" butonunu tıkla
    show_more_selectors = [
        "button[data-control-name='job_details_show_more']",
        ".jobs-box__show-more-btn",
        "button.jobs-description-details__show-more-button"
    ]
    
    for selector in show_more_selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, selector)
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                human_pause(0.5, 1)
                break
        except:
            continue
    
    # Açıklama metnini çıkar
    description_selectors = [
        ".jobs-search__job-details--container .jobs-box__html-content",
        ".jobs-description-content__text",
        ".jobs-description__content",
        ".jobs-box__html-content",
        ".scaffold-layout__detail .jobs-box__html-content"
    ]
    
    for selector in description_selectors:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            html_content = elem.get_attribute('innerHTML')
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup.get_text(separator=' ', strip=True)
        except:
            continue
    
    return ""

def navigate_to_next_page(driver: webdriver.Chrome) -> bool:
    """Sonraki sayfaya git"""
    next_selectors = [
        "//button[@aria-label='Sonraki' or @aria-label='Next']",
        ".artdeco-pagination__button--next",
        "button[aria-label*='Next']"
    ]
    
    for selector in next_selectors:
        try:
            if selector.startswith("//"):
                btn = driver.find_element(By.XPATH, selector)
            else:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
            
            if btn.is_enabled() and btn.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                human_pause(0.5, 1)
                driver.execute_script("arguments[0].click();", btn)
                
                # Sayfa yüklenmesini bekle
                human_pause(3, 5)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
                    )
                    return True
                except:
                    return False
        except:
            continue
    
    return False


# ============================================================================
# DENEYİM ANALİZİ VE SKORLAMA
# ============================================================================

def extract_experience(description: str) -> Tuple[str, str]:
    """Açıklamadan deneyim gereksinimini çıkar ve yorumla"""
    if not description:
        return "belirtilmemiş", "deneyim gereksinimi belirsiz"
    
    # Regex kalıpları (Türkçe ve İngilizce)
    patterns = [
        r'(\d+)\s*-\s*(\d+)\s*(?:yıl|yil|years?)',  # 3-5 yıl, 3-5 years
        r'(\d+)\s*\+\s*(?:yıl|yil|years?)',         # 4+ yıl, 4+ years
        r'(\d+)\s*(?:yıl|yil|years?)',              # 3 yıl, 3 years
        r'minimum\s*(\d+)\s*(?:yıl|yil|years?)',     # minimum 3 yıl
        r'en\s*az\s*(\d+)\s*(?:yıl|yil|years?)',    # en az 3 yıl
        r'at\s*least\s*(\d+)\s*years?',             # at least 3 years
        r'(\d+)\s*(?:yıl|yil|years?)\s*(?:dan|den)?\s*(?:fazla|üstü|above|over)'  # 3 yıldan fazla
    ]
    
    text_lower = description.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            match = matches[0]
            
            if isinstance(match, tuple):
                # Aralık (3-5 yıl)
                min_exp, max_exp = int(match[0]), int(match[1])
                exp_text = f"{min_exp}-{max_exp} yıl"
                
                if max_exp <= 3:
                    interpretation = "tam uyumlu (ben ~3 yıl)"
                elif min_exp <= 3 <= max_exp:
                    interpretation = "tam uyumlu (ben ~3 yıl)"
                elif min_exp == 4 and max_exp <= 5:
                    interpretation = "deneyim yakın (ben ~3 yıl)"
                elif max_exp <= 5:
                    interpretation = "deneyim yakın (ben ~3 yıl)"
                else:
                    interpretation = "deneyim fazla (ben ~3 yıl)"
                    
            else:
                # Tek sayı
                exp_num = int(match)
                
                if '+' in pattern or 'fazla' in pattern or 'minimum' in pattern or 'en az' in pattern or 'least' in pattern:
                    exp_text = f"{exp_num}+ yıl"
                else:
                    exp_text = f"{exp_num} yıl"
                
                if exp_num <= 3:
                    interpretation = "tam uyumlu (ben ~3 yıl)"
                elif exp_num <= 5:
                    interpretation = "deneyim yakın (ben ~3 yıl)"
                else:
                    interpretation = "deneyim fazla (ben ~3 yıl)"
            
            return exp_text, interpretation
    
    return "belirtilmemiş", "deneyim gereksinimi belirsiz"

def score_job(job: Dict) -> Dict:
    """İş ilanını skorla ve detaylı analiz yap"""
    description = job.get("description", "").lower()
    job_title = job.get("job_title", "").lower()
    full_text = f"{job_title} {description}"
    
    # Skor hesaplama
    score = 0
    matched_keywords = []
    negative_points = []
    
    # Yüksek öncelikli anahtar kelimeler (+12 ~ +20)
    high_priority = {
        "it audit": 20, "information security": 18, "siber güvenlik": 18,
        "bilgi güvenliği": 18, "iso 27001": 15, "cobit": 15, "nist": 12,
        "grc": 15, "sox": 12, "cloud security": 15, "aws": 10, "azure": 10,
        "penetration testing": 15, "pentest": 15, "vulnerability": 12,
        "risk management": 15, "compliance": 12, "uyumluluk": 12,
        "risk yönetimi": 15, "denetim": 15
    }
    
    # Orta öncelikli anahtar kelimeler (+5 ~ +10)
    medium_priority = {
        "python": 8, "automation": 6, "otomasyon": 6, "wireshark": 6,
        "nessus": 8, "burp suite": 8, "policy": 6, "standard": 5,
        "access management": 8, "identity": 6, "incident": 8,
        "banking": 10, "financial audit": 8, "control testing": 8,
        "erişim yönetimi": 8, "olay yönetimi": 8
    }
    
    # Mühendislik bonusu (+4 ~ +12)
    engineering_bonus = {
        "elektrik mühendisi": 12, "elektronik mühendisi": 12,
        "electrical engineer": 12, "electronic engineer": 12,
        "güç elektroniği": 8, "power electronics": 8,
        "devre tasarımı": 6, "circuit design": 6,
        "endüstriyel otomasyon": 8, "industrial automation": 8,
        "spwm": 4, "igbt": 4, "mosfet": 4, "pwm": 4
    }
    
    # Negatif sinyaller (-8 ~ -35)
    negative_signals = {
        "helpdesk": -10, "level 2 support": -8, "l2 support": -8,
        "vardiya": -15, "shift work": -12, "7/24": -12, "24/7": -12,
        "backend development": -15, "backend geliştirici": -15,
        "software development": -10, "yazılım geliştirici": -10,
        "coding": -8, "6+ yıl": -20, "7+ yıl": -25, "8+ yıl": -30,
        "10+ yıl": -35, "operasyon": -8
    }
    
    # Skorları hesapla
    for keyword, points in high_priority.items():
        if keyword in full_text:
            score += points
            matched_keywords.append(f"{keyword} (+{points})")
    
    for keyword, points in medium_priority.items():
        if keyword in full_text:
            score += points
            matched_keywords.append(f"{keyword} (+{points})")
    
    for keyword, points in engineering_bonus.items():
        if keyword in full_text:
            score += points
            matched_keywords.append(f"{keyword} (+{points})")
    
    for keyword, points in negative_signals.items():
        if keyword in full_text:
            score += points
            negative_points.append(f"{keyword} ({points})")
    
    # Deneyim cezası/bonusu
    exp_text, exp_interpretation = extract_experience(job.get("description", ""))
    exp_penalty = 0
    
    if "deneyim fazla" in exp_interpretation:
        if any(pattern in exp_text for pattern in ["6+", "7+", "8+", "9+", "10+"]):
            exp_penalty = -20
        elif any(pattern in exp_text for pattern in ["6-", "7-"]):
            exp_penalty = -15
        else:
            exp_penalty = -5
    elif "deneyim yakın" in exp_interpretation:
        exp_penalty = -2
    
    score += exp_penalty
    if exp_penalty < 0:
        negative_points.append(f"deneyim gereksinimi ({exp_penalty})")
    
    # Skoru 0-100 arasında tut
    final_score = max(0, min(100, score))
    
    # Gerekçeleri oluştur
    top_reasons = [reason for reason in matched_keywords[:3]]
    risks_gaps = [risk for risk in negative_points[:2]]
    
    return {
        "match_score": final_score,
        "experience_required_text": exp_text,
        "experience_interpretation": exp_interpretation,
        "top_reasons": top_reasons,
        "risks_or_gaps": risks_gaps
    }


# ============================================================================
# FİLTRELEME VE SIRALAMA
# ============================================================================

def filter_and_rank(jobs: List[Dict], min_score: int = 65, max_results: int = 20) -> List[Dict]:
    """İşleri skorla, filtrele ve sırala"""
    log(f"📊 {len(jobs)} ilan skorlanıyor...")
    
    # Her ilan için skor hesapla
    for job in jobs:
        score_data = score_job(job)
        job.update(score_data)
    
    # Minimum skora sahip olanları filtrele
    filtered = [job for job in jobs if job.get("match_score", 0) >= min_score]
    log(f"✅ Min skor {min_score} üstü: {len(filtered)} ilan")
    
    # Skora göre azalan sırada sırala
    filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Aynı şirketli duplikatları temizle
    seen_companies = set()
    unique_jobs = []
    
    for job in filtered:
        company = job.get("company", "").lower().strip()
        if company and company not in seen_companies:
            seen_companies.add(company)
            unique_jobs.append(job)
        elif not company:
            unique_jobs.append(job)
    
    log(f"🔄 Duplikat temizleme sonrası: {len(unique_jobs)} ilan")
    
    # Sonuç sayısını sınırla
    return unique_jobs[:max_results]


# ============================================================================
# SONUÇ KAYDETME VE GÖSTERME
# ============================================================================

def save_results(jobs: List[Dict], filename: str = "matches.json") -> None:
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
    
    log(f"💾 {len(output_data)} sonuç {filename} dosyasına kaydedildi")

def print_results(jobs: List[Dict]) -> None:
    """Sonuçları konsola yazdır"""
    if not jobs:
        log("❌ Kriterlere uygun ilan bulunamadı")
        return
    
    print(f"\n🎯 UYGUN İŞ İLANLARI ({len(jobs)} adet):")
    print("=" * 80)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}) {job.get('job_title', 'Başlık yok')} — {job.get('company', 'Şirket yok')}")
        print(f"   {job.get('link', '')}")
        print(f"   Skor: {job.get('match_score', 0)}% | Deneyim: {job.get('experience_required_text', 'belirtilmemiş')} → {job.get('experience_interpretation', '')}")
        
        if job.get('top_reasons'):
            reasons = " + ".join([r.split(' (+')[0] for r in job.get('top_reasons', [])])
            print(f"   Gerekçe: {reasons}")
        
        if job.get('risks_or_gaps'):
            risks = ", ".join([r.split(' (')[0] for r in job.get('risks_or_gaps', [])])
            print(f"   ⚠️  Riskler: {risks}")
        
        print("-" * 80)


# ============================================================================
# ANA FONKSİYON
# ============================================================================

def main():
    """Ana program akışı"""
    log("🚀 LinkedIn İş İlanı Analiz Botu MK6 başlatılıyor...")
    
    # Ortam değişkenlerini yükle
    load_dotenv()
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    
    if not email or not password:
        log("❌ .env dosyasında LINKEDIN_EMAIL ve LINKEDIN_PASSWORD gerekli")
        sys.exit(1)
    
    # Konfigürasyonu yükle
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        log("❌ config.json dosyası bulunamadı")
        sys.exit(1)
    
    # Parametreler
    queries = config.get("queries", ["Siber Güvenlik Uzmanı"])
    locations = config.get("locations", ["İstanbul, Türkiye"])
    filters = config.get("filters", {})
    max_pages = config.get("max_pages", 3)
    min_score = config.get("min_score", 65)
    max_results = config.get("max_results", 20)
    
    # Tarayıcıyı başlat
    driver = launch_browser(user_data_dir, headless)
    all_jobs = []
    
    try:
        # LinkedIn'e giriş yap
        if not login_and_nav(driver, email, password):
            log("❌ LinkedIn girişi başarısız")
            return
        
        # Her sorgu × lokasyon kombinasyonunu işle
        total_processed = 0
        for query_idx, query in enumerate(queries, 1):
            for loc_idx, location in enumerate(locations, 1):
                log(f"\n🔍 Arama {query_idx}/{len(queries)}: '{query}' @ '{location}'")
                
                # Arama URL'sini oluştur ve git
                search_url = build_search_url(query, location, filters)
                driver.get(search_url)
                human_pause(2, 3)
                
                # Overlay'leri temizle
                cleanup_overlays(driver)
                
                # İş listesinin yüklenmesini bekle
                try:
                    WebDriverWait(driver, 30).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".scaffold-layout__list-container"))
                        )
                    )
                    log("✅ İş listesi yüklendi")
                except TimeoutException:
                    log("❌ İş listesi yüklenemedi, sonraki sorguya geçiliyor")
                    continue
                
                # İlanları topla
                query_jobs = collect_job_cards(driver, max_pages)
                all_jobs.extend(query_jobs)
                total_processed += len(query_jobs)
                
                log(f"📊 '{query}' @ '{location}': {len(query_jobs)} ilan toplandı")
        
        log(f"\n📈 TOPLAM: {total_processed} ilan işlendi")
        
        if not all_jobs:
            log("❌ Hiç ilan bulunamadı")
            return
        
        # İlanları skorla, filtrele ve sırala
        log(f"🔄 İlanlar analiz ediliyor (min skor: {min_score})...")
        matched_jobs = filter_and_rank(all_jobs, min_score, max_results)
        
        # Sonuçları göster ve kaydet
        print_results(matched_jobs)
        
        if matched_jobs:
            save_results(matched_jobs)
            log(f"\n🎯 SONUÇ: {len(matched_jobs)} uygun ilan bulundu!")
        else:
            log(f"\n❌ Minimum skor {min_score} üstünde ilan bulunamadı")
        
    except KeyboardInterrupt:
        log("ℹ️  İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        log(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if headless:
            driver.quit()
            log("🔚 Tarayıcı kapatıldı")
        else:
            log("🌐 Tarayıcı açık bırakıldı")


if __name__ == "__main__":
    main()
