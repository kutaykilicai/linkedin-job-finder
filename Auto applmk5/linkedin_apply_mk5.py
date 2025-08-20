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

def aggressive_popup_cleanup(driver):
    """Agresif popup/overlay temizleme"""
    cleanup_selectors = [
        # Cookie consent
        "button[data-testid='cookie-banner-accept']",
        "button[aria-label*='Accept']", "button[aria-label*='Kabul']",
        "button[aria-label*='Kapat']", "button[aria-label*='Close']",
        "button[aria-label*='Dismiss']", "button[aria-label*='Skip']",
        
        # Messaging overlay
        "button.msg-overlay-bubble-header__control",
        ".msg-overlay-bubble-header__controls button",
        
        # Modal/overlay close buttons
        ".artdeco-modal__dismiss", ".artdeco-modal__dismiss-btn",
        "button[data-dismiss='modal']",
        
        # Generic overlay elements
        ".global-alert__dismiss", ".notification-banner__dismiss",
        
        # LinkedIn specific popups
        "button[data-control-name='overlay.close_overlay']",
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
    
    # JavaScript ile overlay temizleme
    try:
        removed_js = driver.execute_script("""
            let removed = 0;
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

def wait_for_right_panel_loaded(driver, timeout=15):
    """Sağ panel tam yüklenene kadar bekle"""
    try:
        # İş detay paneli yüklenene kadar bekle
        WebDriverWait(driver, timeout).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__job-details")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id]")),
            )
        )
        human_pause(0.5, 1.0)  # DOM stabilizasyonu için ekstra bekleme
        
        # Easy Apply buton varlığını kontrol et
        WebDriverWait(driver, 5).until(
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Kolay Başvuru') or contains(., 'Easy Apply')]")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.jobs-apply-button")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-control-name*='apply']")),
            )
        )
        return True
    except TimeoutException:
        log("Sağ panel yüklenemedi veya Easy Apply buton bulunamadı")
        return False

def is_easy_apply_available(driver):
    """Easy Apply butonunun varlığını kontrol et"""
    selectors = [
        "button.jobs-apply-button",
        "button[data-control-name='jobdetails_topcard_inapply']",
        "button[data-control-name='jobdetails_topcard_inapply_simple']",
        "button[aria-label*='Easy Apply']",
        "button[aria-label*='Kolay Başvuru']",
    ]
    
    xpaths = [
        "//button[contains(., 'Kolay Başvuru')]",
        "//button[contains(., 'Easy Apply')]",
        "//button[contains(@class, 'jobs-apply-button')]",
        "//button[contains(@aria-label, 'Easy Apply')]",
        "//button[contains(@aria-label, 'Kolay Başvuru')]",
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    text = elem.get_attribute('textContent') or ''
                    if 'Easy Apply' in text or 'Kolay Başvuru' in text:
                        return True
        except:
            pass
    
    for xpath in xpaths:
        try:
            element = driver.find_element(By.XPATH, xpath)
            if element.is_displayed():
                return True
        except:
            pass
    
    return False

def force_click_easy_apply(driver, max_attempts=5):
    """Gelişmiş Easy Apply buton tıklama stratejisi"""
    
    # Önce sağ panelin tam yüklenmesini bekle
    if not wait_for_right_panel_loaded(driver):
        log("Sağ panel yüklenemedi")
        return False
    
    # Popup'ları temizle
    aggressive_popup_cleanup(driver)
    
    button_locators = [
        # CSS Selectors
        ("css", "button.jobs-apply-button"),
        ("css", "button[data-control-name='jobdetails_topcard_inapply']"),
        ("css", "button[data-control-name='jobdetails_topcard_inapply_simple']"),
        ("css", "button[aria-label*='Easy Apply']:not([disabled])"),
        ("css", "button[aria-label*='Kolay Başvuru']:not([disabled])"),
        
        # XPath Selectors
        ("xpath", "//button[contains(., 'Easy Apply') and not(@disabled)]"),
        ("xpath", "//button[contains(., 'Kolay Başvuru') and not(@disabled)]"),
        ("xpath", "//button[contains(@class, 'jobs-apply-button') and not(@disabled)]"),
        ("xpath", "//button[contains(@aria-label, 'Easy Apply') and not(@disabled)]"),
        ("xpath", "//button[contains(@aria-label, 'Kolay Başvuru') and not(@disabled)]"),
    ]
    
    for attempt in range(max_attempts):
        log(f"Easy Apply tıklama denemesi {attempt + 1}/{max_attempts}")
        
        # Her denemede popup'ları temizle
        aggressive_popup_cleanup(driver)
        
        for locator_type, locator in button_locators:
            try:
                if locator_type == "css":
                    elements = driver.find_elements(By.CSS_SELECTOR, locator)
                else:
                    elements = driver.find_elements(By.XPATH, locator)
                
                for element in elements:
                    if not element.is_displayed() or not element.is_enabled():
                        continue
                    
                    # Butonu ekran ortasına getir
                    try:
                        driver.execute_script("""
                            arguments[0].scrollIntoView({
                                behavior: 'smooth',
                                block: 'center',
                                inline: 'center'
                            });
                        """, element)
                        human_pause(0.3, 0.6)
                        
                        # Sayfayı biraz yukarı kaydır (sticky header için)
                        driver.execute_script("window.scrollBy(0, -100);")
                        human_pause(0.2, 0.4)
                    except:
                        pass
                    
                    # Butonu vurgula (debug için)
                    try:
                        driver.execute_script("""
                            arguments[0].style.border = '3px solid #ff0000';
                            arguments[0].style.backgroundColor = '#ffff00';
                        """, element)
                    except:
                        pass
                    
                    # Çoklu tıklama stratejisi
                    click_success = False
                    
                    # 1. ActionChains ile tıklama
                    try:
                        ActionChains(driver).move_to_element(element).pause(0.2).click().perform()
                        click_success = True
                        log("ActionChains ile tıklandı")
                    except Exception as e:
                        log(f"ActionChains hatası: {e}")
                    
                    # 2. Normal click
                    if not click_success:
                        try:
                            element.click()
                            click_success = True
                            log("Normal click ile tıklandı")
                        except Exception as e:
                            log(f"Normal click hatası: {e}")
                    
                    # 3. JavaScript click
                    if not click_success:
                        try:
                            driver.execute_script("arguments[0].click();", element)
                            click_success = True
                            log("JavaScript click ile tıklandı")
                        except Exception as e:
                            log(f"JavaScript click hatası: {e}")
                    
                    # 4. Event dispatch
                    if not click_success:
                        try:
                            driver.execute_script("""
                                var element = arguments[0];
                                var event = new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                });
                                element.dispatchEvent(event);
                            """, element)
                            click_success = True
                            log("Event dispatch ile tıklandı")
                        except Exception as e:
                            log(f"Event dispatch hatası: {e}")
                    
                    if click_success:
                        # Modal/form açılmasını bekle
                        human_pause(1.0, 2.0)
                        
                        # Easy Apply modalının açıldığını kontrol et
                        modal_selectors = [
                            ".jobs-easy-apply-modal",
                            ".jobs-apply-form-modal", 
                            ".artdeco-modal",
                            "[data-test-modal]",
                            "[role='dialog']"
                        ]
                        
                        modal_opened = False
                        for modal_sel in modal_selectors:
                            try:
                                modal = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, modal_sel))
                                )
                                if modal.is_displayed():
                                    modal_opened = True
                                    break
                            except TimeoutException:
                                continue
                        
                        # Alternatif: Next/Submit button varlığını kontrol et
                        if not modal_opened:
                            try:
                                WebDriverWait(driver, 3).until(
                                    EC.any_of(
                                        EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'İleri')] or .//span[contains(text(),'Next')]]")),
                                        EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Başvuruyu gönder')] or .//span[contains(text(),'Submit application')]]"))
                                    )
                                )
                                modal_opened = True
                            except TimeoutException:
                                pass
                        
                        if modal_opened:
                            log("✅ Easy Apply formu açıldı!")
                            return True
                        else:
                            log("❌ Modal açılmadı, sonraki butonu deneniyor")
            
            except Exception as e:
                log(f"Locator hatası ({locator}): {e}")
                continue
        
        # Deneme arasında bekleme
        human_pause(0.5, 1.0)
        
        # Son çare: Sayfayı yenile ve tekrar dene
        if attempt == max_attempts - 2:
            log("Sayfa yenileniyor...")
            driver.refresh()
            if not wait_for_right_panel_loaded(driver):
                break
    
    log("❌ Easy Apply butonu tıklanamadı")
    return False

def simple_easy_apply(driver, resume_path):
    """Basitleştirilmiş Easy Apply süreci"""
    if not force_click_easy_apply(driver):
        return False
    
    human_pause(1, 2)
    
    # CV yükleme
    try:
        upload_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if upload_inputs:
            for upload_input in upload_inputs:
                if upload_input.is_displayed():
                    upload_input.send_keys(resume_path)
                    log("CV yüklendi.")
                    human_pause(1.2, 2.0)
                    break
    except Exception as e:
        log(f"CV yükleme hatası: {e}")
    
    # Form doldurma döngüsü
    max_steps = 10
    step_count = 0
    
    while step_count < max_steps:
        step_count += 1
        human_pause(0.7, 1.2)
        aggressive_popup_cleanup(driver)
        
        # Submit button kontrolü
        try:
            submit_selectors = [
                "//button[.//span[contains(text(),'Başvuruyu gönder')]]",
                "//button[.//span[contains(text(),'Submit application')]]",
                "//button[contains(@aria-label,'Submit application')]",
                "//button[contains(@aria-label,'Başvuruyu gönder')]"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.XPATH, selector)
                    if submit_button.is_displayed() and submit_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if submit_button and submit_button.is_displayed() and submit_button.is_enabled():
                driver.execute_script("arguments[0].click();", submit_button)
                human_pause(0.8, 1.5)
                log("✅ Başvuru gönderildi!")
                
                # Kapama butonunu bekle ve tıkla
                try:
                    close_selectors = [
                        "button[aria-label='Kapat']",
                        "button[aria-label='Close']", 
                        ".artdeco-modal__dismiss",
                        "button[data-control-name='overlay.close_overlay']"
                    ]
                    
                    for close_sel in close_selectors:
                        try:
                            close_btn = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, close_sel))
                            )
                            driver.execute_script("arguments[0].click();", close_btn)
                            break
                        except TimeoutException:
                            continue
                except:
                    pass
                
                return True
                
        except NoSuchElementException:
            pass
        
        # Next button kontrolü
        try:
            next_selectors = [
                "//button[.//span[contains(text(),'İleri')]]",
                "//button[.//span[contains(text(),'Next')]]",
                "//button[contains(@aria-label,'Continue to next step')]",
                "//button[contains(@aria-label,'İlerle')]"
            ]
            
            next_button = None
            for selector in next_selectors:
                try:
                    next_button = driver.find_element(By.XPATH, selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if next_button and next_button.is_displayed() and next_button.is_enabled():
                driver.execute_script("arguments[0].click();", next_button)
                log(f"İleri düğmesine tıklandı (adım {step_count})")
                continue
            else:
                # Next butonu bulunamadı veya disabled
                log("Form çok karmaşık veya tamamlanamıyor, iptal ediliyor.")
                break
                
        except NoSuchElementException:
            log("Form çok karmaşık, iptal ediliyor.")
            break
    
    # Form iptal etme
    try:
        cancel_selectors = [
            "button[aria-label='Kapat']",
            "button[aria-label='Close']",
            ".artdeco-modal__dismiss"
        ]
        
        for cancel_sel in cancel_selectors:
            try:
                cancel_btn = driver.find_element(By.CSS_SELECTOR, cancel_sel)
                if cancel_btn.is_displayed():
                    cancel_btn.click()
                    human_pause(0.4, 0.8)
                    break
            except:
                continue
        
        # Discard confirmation
        try:
            discard_btn = driver.find_element(By.XPATH, "//button[.//span[contains(text(),'Başvuruyu iptal et')] or .//span[contains(text(),'Discard')]]")
            if discard_btn.is_displayed():
                discard_btn.click()
        except:
            pass
            
    except Exception as e:
        log(f"Form iptal etme hatası: {e}")
    
    return False

def run():
    load_dotenv()
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    resume_path = os.getenv("RESUME_PATH")
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    
    if not all([email, password, resume_path]):
        print("❌ Lütfen .env dosyasında LINKEDIN_EMAIL, LINKEDIN_PASSWORD ve RESUME_PATH'i doldurun.")
        sys.exit(1)
    
    if not Path(resume_path).exists():
        print(f"❌ CV dosyası bulunamadı: {resume_path}")
        sys.exit(1)
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print("❌ config.json dosyası bulunamadı.")
        sys.exit(1)
    
    driver = launch_browser(user_data_dir, headless=headless)
    
    try:
        ensure_login(driver, email, password)
        
        queries = cfg.get("queries", ["Siber Güvenlik Uzmanı"])
        locations = cfg.get("locations", ["İstanbul, Türkiye"])
        filters = cfg.get("filters", {})
        max_pages = int(cfg.get("max_pages", 3))
        per_session_limit = int(cfg.get("per_session_limit", 10))
        
        applied_count = 0
        total_jobs_found = 0
        
        for query in queries:
            for location in locations:
                if applied_count >= per_session_limit:
                    log(f"✅ Günlük limit ({per_session_limit}) doldu.")
                    break
                    
                url = build_search_url(query, location, filters)
                log(f"🔍 Arama: '{query}' @ '{location}'")
                driver.get(url)
                
                # Cookie/popup temizleme
                aggressive_popup_cleanup(driver)
                
                # İş ilanları listesi yüklenmesini bekle
                try:
                    WebDriverWait(driver, 30).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-search-results"))
                        )
                    )
                except TimeoutException:
                    log("❌ İş ilanları listesi yüklenemedi, sonraki sorguya geçiliyor.")
                    continue
                
                human_pause(1.0, 2.0)
                job_links = collect_job_links(driver, max_pages=max_pages)
                total_jobs_found += len(job_links)
                log(f"📋 Bulunan ilan sayısı: {len(job_links)}")
                
                for i, job_link in enumerate(job_links, 1):
                    if applied_count >= per_session_limit:
                        log(f"✅ Session limit ({per_session_limit}) reached.")
                        break
                    
                    log(f"📄 İlan {i}/{len(job_links)}: {job_link}")
                    driver.get(job_link)
                    human_pause(1.0, 2.5)
                    
                    # Easy Apply kontrolü
                    if not is_easy_apply_available(driver):
                        log("⏭️  Easy Apply mevcut değil, sonrakine geçiliyor.")
                        continue
                    
                    # Başvuru yapma
                    success = simple_easy_apply(driver, resume_path)
                    if success:
                        applied_count += 1
                        log(f"✅ Başarılı başvuru! Toplam: {applied_count}/{per_session_limit}")
                    else:
                        log("❌ Başvuru başarısız.")
                    
                    human_pause(1.2, 2.5)
        
        log(f"🎯 Özet: {applied_count} başarılı başvuru / {total_jobs_found} ilan")
        
    except KeyboardInterrupt:
        log("⏹️  İşlem kullanıcı tarafından durduruldu.")
    except Exception as e:
        log(f"❌ Beklenmeyen hata: {e}")
    finally:
        if headless:
            driver.quit()
        else:
            log("Tarayıcı açık bırakılıyor. Manuel olarak kapatabilirsiniz.")

if __name__ == "__main__":
    run()