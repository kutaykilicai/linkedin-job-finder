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
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
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

def dismiss_all_overlays(driver):
    """Tüm overlay'leri ve pop-up'ları kapat"""
    overlay_selectors = [
        "button[aria-label='Kapat']",
        "button[aria-label='Close']", 
        "button[aria-label='Dismiss']",
        "button[aria-label='Skip']",
        "button[data-testid='cookie-banner-accept']",
        ".artdeco-modal__dismiss",
        ".msg-overlay-bubble-header__control",
        "button.msg-overlay-bubble-header__control"
    ]
    
    for selector in overlay_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    try:
                        driver.execute_script("arguments[0].click();", elem)
                        human_pause(0.2, 0.4)
                    except:
                        pass
        except:
            continue

def wait_and_find_easy_apply_button(driver, timeout=15):
    """Easy Apply butonunu bulana kadar bekle ve döndür - LinkedIn'in mavi buton için özelleştirilmiş"""
    # Önce sayfanın yüklenmesini bekle
    human_pause(2, 3)
    # Overlay'leri temizle
    dismiss_all_overlays(driver)
    # LinkedIn'in mavi "Kolay Başvuru" butonu için özel selector'lar
    selectors = [
        # Ana mavi buton selector'ları
        "button.jobs-apply-button--top-card",
        "button.jobs-apply-button",
        "button[data-control-name='jobdetails_topcard_inapply']",
        "button[data-control-name='jobdetails_topcard_inapply_simple']",
        # Mavi buton class'ları
        "button.artdeco-button--primary",
        "button[class*='artdeco-button--primary'][class*='jobs-apply-button']",
        "button[class*='jobs-apply-button'][class*='primary']",
        # XPath ile daha spesifik arama
        "//button[contains(@class, 'jobs-apply-button') and contains(@class, 'artdeco-button--primary')]",
        "//button[contains(@class, 'jobs-apply-button') and (contains(text(), 'Kolay Başvuru') or contains(text(), 'Easy Apply'))]",
        "//button[contains(text(), 'Kolay Başvuru')]",
        "//button[contains(text(), 'Easy Apply')]",
        # Aria-label ile arama
        "//button[contains(@aria-label, 'Kolay Başvuru')]",
        "//button[contains(@aria-label, 'Easy Apply')]",
        # Data attribute ile arama
        "//button[@data-control-name='jobdetails_topcard_inapply' or @data-control-name='jobdetails_topcard_inapply_simple']",
        # Genel class araması
        ".jobs-apply-button",
        "[class*='jobs-apply-button']",
    ]
    end_time = time.time() + timeout
    attempt = 0
    while time.time() < end_time:
        attempt += 1
        log(f"Easy Apply butonu arama denemesi: {attempt}")
        # Her deneme arasında overlay'leri temizle
        dismiss_all_overlays(driver)
        # Sayfayı hafifçe kaydır (bazen buton görünür hale gelir)
        if attempt % 3 == 0:
            driver.execute_script("window.scrollBy(0, 200);")
            human_pause(0.5, 1)
            driver.execute_script("window.scrollBy(0, -200);")
        for selector in selectors:
            try:
                elements = (
                    driver.find_elements(By.XPATH, selector)
                    if selector.startswith("//")
                    else driver.find_elements(By.CSS_SELECTOR, selector)
                )
                for elem in elements:
                    try:
                        if elem and elem.is_displayed():
                            text = elem.text.strip()
                            aria_label = elem.get_attribute("aria-label") or ""
                            class_attr = elem.get_attribute("class") or ""
                            data_control = elem.get_attribute("data-control-name") or ""
                            log(f"Bulunan element - Text: '{text}', Class: '{class_attr[:50]}', Data-control: '{data_control}'")
                            is_easy_apply = (
                                "Kolay Başvuru" in text
                                or "Easy Apply" in text
                                or "Kolay Başvuru" in aria_label
                                or "Easy Apply" in aria_label
                                or "jobs-apply-button" in class_attr
                                or "jobdetails_topcard_inapply" in data_control
                            )
                            if is_easy_apply:
                                log(f"✅ Easy Apply butonu bulundu! Selector: {selector}")
                                log(f"   Text: '{text}'")
                                log(f"   Class: '{class_attr}'")
                                try:
                                    is_clickable = driver.execute_script(
                                        """
                                        var elem = arguments[0];
                                        var rect = elem.getBoundingClientRect();
                                        var centerX = rect.left + rect.width / 2;
                                        var centerY = rect.top + rect.height / 2;
                                        var elementAtPoint = document.elementFromPoint(centerX, centerY);
                                        return elementAtPoint === elem || elem.contains(elementAtPoint);
                                        """,
                                        elem,
                                    )
                                    if is_clickable:
                                        return elem
                                    else:
                                        log("   ⚠️ Element bulundu ama tıklanamaz durumda")
                                except Exception:
                                    return elem
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        log(f"   Element kontrol hatası: {str(e)[:50]}")
                        continue
            except Exception as e:
                log(f"Selector hatası {selector}: {str(e)[:50]}")
                continue
        human_pause(1, 1.5)
    log("❌ Easy Apply butonu bulunamadı")
    return None

def scroll_to_element_and_click(driver, element):
    """LinkedIn'in mavi Kolay Başvuru butonu için özelleştirilmiş tıklama fonksiyonu"""
    try:
        # Element bilgilerini al
        text = element.text.strip()
        class_attr = element.get_attribute("class") or ""
        log(f"Tıklanacak element: '{text}' - Class: '{class_attr[:50]}'")
        # 1. Sayfayı element'e kaydır
        driver.execute_script(
            """
            var element = arguments[0];
            element.scrollIntoView({
                behavior: 'smooth', 
                block: 'center', 
                inline: 'center'
            });
            window.scrollBy(0, -100);
            """,
            element,
        )
        human_pause(2, 3)
        # 2. Tüm overlay'leri agresif şekilde temizle
        dismiss_all_overlays(driver)
        # 3. JavaScript ile overlay'lerin element'i kaplamadığından emin ol
        driver.execute_script(
            """
            // Tüm fixed ve absolute position elementleri kontrol et
            var allElements = document.querySelectorAll('*');
            for (var i = 0; i < allElements.length; i++) {
                var elem = allElements[i];
                var style = window.getComputedStyle(elem);
                // Overlay olabilecek elementleri gizle
                if (style.position === 'fixed' || 
                    (style.position === 'absolute' && parseInt(style.zIndex || 0) > 100) ||
                    elem.className.includes('overlay') ||
                    elem.className.includes('modal') ||
                    elem.className.includes('popup')) {
                    // Apply butonunu gizleme!
                    if (!elem.className.includes('jobs-apply-button')) {
                        elem.style.display = 'none';
                    }
                }
            }
            """
        )
        human_pause(1, 2)
        # 4. Element'i highlight et (debug için)
        driver.execute_script(
            """
            arguments[0].style.border = '4px solid lime';
            arguments[0].style.backgroundColor = 'yellow';
            arguments[0].style.zIndex = '9999';
            """,
            element,
        )
        human_pause(1, 1.5)
        # 5. Çoklu tıklama stratejisi - LinkedIn için optimize edilmiş
        click_strategies = [
            {"name": "Direct Click", "action": lambda: element.click()},
            {"name": "ActionChains Click", "action": lambda: ActionChains(driver).move_to_element(element).pause(0.2).click().perform()},
            {"name": "JavaScript Click", "action": lambda: driver.execute_script("arguments[0].click();", element)},
            {
                "name": "JavaScript Mouse Event",
                "action": lambda: driver.execute_script(
                    """
                    var elem = arguments[0];
                    var event = new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: elem.getBoundingClientRect().left + elem.getBoundingClientRect().width / 2,
                        clientY: elem.getBoundingClientRect().top + elem.getBoundingClientRect().height / 2
                    });
                    elem.dispatchEvent(event);
                    """,
                    element,
                ),
            },
            {"name": "Force Click with Focus", "action": lambda: driver.execute_script("""arguments[0].focus(); arguments[0].click();""", element)},
            {"name": "ActionChains with Offset", "action": lambda: ActionChains(driver).move_to_element_with_offset(element, 5, 5).click().perform()},
            {"name": "Enter Key", "action": lambda: element.send_keys(Keys.ENTER)},
            {"name": "Space Key", "action": lambda: element.send_keys(Keys.SPACE)},
        ]
        for i, strategy in enumerate(click_strategies):
            try:
                log(f"Tıklama stratejisi {i+1}: {strategy['name']}")
                strategy["action"]()
                human_pause(1, 2)
                # Modal veya form açıldı mı kontrol et
                modal_indicators = [
                    # Easy Apply modal selectors
                    ".jobs-easy-apply-modal",
                    ".jobs-apply-form-modal",
                    ".artdeco-modal",
                    "div[role='dialog']",
                    # Form element selectors
                    "//div[contains(@class, 'jobs-easy-apply')]",
                    "//button[contains(text(), 'Next') or contains(text(), 'İleri')]",
                    "//button[contains(text(), 'Submit') or contains(text(), 'Gönder') or contains(text(), 'Başvuruyu gönder')]",
                    "//input[@type='file']",
                    # Modal header selectors
                    "//h3[contains(text(), 'Easy Apply') or contains(text(), 'Kolay Başvuru')]",
                    ".jobs-easy-apply-modal__title",
                ]
                modal_found = False
                for indicator in modal_indicators:
                    try:
                        elements = (
                            driver.find_elements(By.XPATH, indicator)
                            if indicator.startswith("//")
                            else driver.find_elements(By.CSS_SELECTOR, indicator)
                        )
                        for elem in elements:
                            if elem.is_displayed():
                                log(f"✅ Modal/Form tespit edildi: {indicator}")
                                modal_found = True
                                break
                        if modal_found:
                            break
                    except Exception:
                        continue
                if modal_found:
                    log("🎉 Easy Apply başarıyla tıklandı - Modal açıldı!")
                    return True
                # URL değişimi kontrolü (bazen sayfa yönlendirmesi olur)
                current_url = driver.current_url
                if "easy-apply" in current_url.lower() or "apply" in current_url.lower():
                    log("✅ URL değişimi tespit edildi - Easy Apply tıklandı!")
                    return True
            except Exception as e:
                log(f"   Strateji {i+1} başarısız: {str(e)[:80]}")
                continue
        # Son deneme: Element'i tamamen odağa al ve force tıkla
        log("🔄 Son deneme: Force click...")
        try:
            driver.execute_script(
                """
                var elem = arguments[0];
                elem.scrollIntoView({block: 'center'});
                elem.focus();
                setTimeout(function() { elem.click(); }, 100);
                """,
                element,
            )
            human_pause(2, 3)
            # Son kontrol
            for indicator in [".jobs-easy-apply-modal", ".artdeco-modal", "div[role='dialog']"]:
                elements = driver.find_elements(By.CSS_SELECTOR, indicator)
                if any(elem.is_displayed() for elem in elements):
                    log("✅ Son deneme başarılı!")
                    return True
        except Exception:
            pass
        log("❌ Tüm tıklama stratejileri başarısız!")
        return False
    except Exception as e:
        log(f"❌ Tıklama fonksiyonu genel hatası: {str(e)[:100]}")
        return False

def click_easy_apply(driver):
    """Geliştirilmiş Easy Apply tıklama fonksiyonu"""
    log("Easy Apply butonu aranıyor...")
    
    # Sayfanın tamamen yüklenmesini bekle
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__job-details"))
        )
    except TimeoutException:
        log("İş detay paneli yüklenemedi")
    
    # Easy Apply butonunu bul
    easy_apply_btn = wait_and_find_easy_apply_button(driver, timeout=15)
    
    if easy_apply_btn:
        log("Easy Apply butonu bulundu, tıklanıyor...")
        success = scroll_to_element_and_click(driver, easy_apply_btn)
        
        if success:
            return True
        else:
            # Son deneme: Sayfayı yenile ve tekrar dene
            log("Son deneme: Sayfa yenileniyor...")
            driver.refresh()
            human_pause(3, 5)
            
            easy_apply_btn = wait_and_find_easy_apply_button(driver, timeout=10)
            if easy_apply_btn:
                return scroll_to_element_and_click(driver, easy_apply_btn)
    
    log("❌ Easy Apply butonu bulunamadı veya tıklanamadı")
    return False

def is_easy_apply(driver):
    """Easy Apply mevcut mu kontrol et"""
    easy_apply_btn = wait_and_find_easy_apply_button(driver, timeout=5)
    return easy_apply_btn is not None

def simple_easy_apply(driver, resume_path):
    """Easy Apply sürecini tamamla"""
    if not click_easy_apply(driver):
        log("Easy Apply butonuna tıklanamadı")
        return False
    
    log("Easy Apply modalı açıldı, form doldurma başlıyor...")
    human_pause(2, 3)
    
    # CV yükleme
    try:
        upload_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if upload_inputs:
            upload_inputs[0].send_keys(resume_path)
            log("CV yüklendi.")
            human_pause(1.5, 2.5)
    except Exception as e:
        log(f"CV yükleme hatası: {e}")
    
    # Form adımlarını geç
    max_steps = 10
    current_step = 0
    
    while current_step < max_steps:
        human_pause(1, 2)
        dismiss_all_overlays(driver)
        
        # Submit butonunu ara
        submit_selectors = [
            "//button[.//span[contains(text(),'Başvuruyu gönder')]]",
            "//button[.//span[contains(text(),'Submit application')]]",
            "//button[contains(text(),'Başvuruyu gönder')]",
            "//button[contains(text(),'Submit application')]",
            "button[data-control-name='continue_unify']"
        ]
        
        submit_found = False
        for selector in submit_selectors:
            try:
                if selector.startswith("//"):
                    submit_btns = driver.find_elements(By.XPATH, selector)
                else:
                    submit_btns = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for btn in submit_btns:
                    if btn.is_displayed() and btn.is_enabled():
                        log("Submit butonu bulundu, başvuru gönderiliyor...")
                        driver.execute_script("arguments[0].click();", btn)
                        human_pause(2, 3)
                        
                        # Başvuru başarılı mesajını kontrol et
                        success_indicators = [
                            "//div[contains(text(), 'başvurunuz gönderildi')]",
                            "//div[contains(text(), 'Application sent')]",
                            ".jobs-post-apply-success"
                        ]
                        
                        for indicator in success_indicators:
                            try:
                                if indicator.startswith("//"):
                                    success_elems = driver.find_elements(By.XPATH, indicator)
                                else:
                                    success_elems = driver.find_elements(By.CSS_SELECTOR, indicator)
                                
                                if success_elems:
                                    log("✅ Başvuru başarıyla gönderildi!")
                                    
                                    # Modal'ı kapat
                                    try:
                                        close_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Kapat'], .artdeco-modal__dismiss")
                                        for close_btn in close_btns:
                                            if close_btn.is_displayed():
                                                driver.execute_script("arguments[0].click();", close_btn)
                                                break
                                    except:
                                        pass
                                    
                                    return True
                            except:
                                continue
                        
                        submit_found = True
                        break
                        
                if submit_found:
                    break
            except:
                continue
        
        if submit_found:
            continue
            
        # Next butonunu ara
        next_selectors = [
            "//button[.//span[contains(text(),'İleri')]]",
            "//button[.//span[contains(text(),'Next')]]",
            "//button[contains(text(),'İleri')]",
            "//button[contains(text(),'Next')]",
            "button[data-control-name='continue_unify']"
        ]
        
        next_found = False
        for selector in next_selectors:
            try:
                if selector.startswith("//"):
                    next_btns = driver.find_elements(By.XPATH, selector)
                else:
                    next_btns = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for btn in next_btns:
                    if btn.is_displayed() and btn.is_enabled():
                        log(f"Next butonu bulundu, adım {current_step + 1}")
                        driver.execute_script("arguments[0].click();", btn)
                        human_pause(1.5, 2.5)
                        next_found = True
                        break
                        
                if next_found:
                    break
            except:
                continue
        
        if not next_found:
            log("❌ Form çok karmaşık veya tamamlanamadı, iptal ediliyor...")
            try:
                # Modal'ı kapat
                close_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Kapat'], .artdeco-modal__dismiss")
                for close_btn in close_btns:
                    if close_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", close_btn)
                        human_pause(0.5, 1)
                        break
                
                # Discard butonunu ara
                discard_btns = driver.find_elements(By.XPATH, "//button[contains(text(),'Başvuruyu iptal et') or contains(text(),'Discard')]")
                for btn in discard_btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        break
            except:
                pass
            return False
        
        current_step += 1
    
    log("❌ Maximum adım sayısına ulaşıldı, başvuru tamamlanamadı")
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
                if applied >= per_session_limit:
                    log("Oturum limiti doldu.")
                    break
                    
                url = build_search_url(q, loc, filters)
                log(f"Arama: {q} @ {loc}")
                driver.get(url)
                
                # Cookie consent ve popup'ları kapat
                human_pause(2, 3)
                dismiss_all_overlays(driver)
                
                # İş listesinin yüklenmesini bekle
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
                    )
                except TimeoutException:
                    log("İş ilanları listesi yüklenemedi.")
                    continue
                
                human_pause(2, 3)
                job_links = collect_job_links(driver, max_pages=max_pages)
                log(f"Bulunan ilan: {len(job_links)}")
                
                for i, link in enumerate(job_links):
                    if applied >= per_session_limit:
                        log("Limit doldu.")
                        break
                    
                    log(f"İlan {i+1}/{len(job_links)} işleniyor...")
                    driver.get(link)
                    human_pause(2, 4)
                    
                    if not is_easy_apply(driver):
                        log("❌ Easy Apply bulunamadı, sonraki ilana geçiliyor.")
                        continue
                    
                    log("✅ Easy Apply mevcut, başvuru yapılıyor...")
                    success = simple_easy_apply(driver, resume_path)
                    
                    if success:
                        applied += 1
                        log(f"✅ Başvuru başarılı! Toplam: {applied}")
                    else:
                        log("❌ Başvuru başarısız!")
                    
                    human_pause(2, 4)
        
        log(f"🎉 Toplam gönderilen başvuru: {applied}")
        
    except KeyboardInterrupt:
        log("Program kullanıcı tarafından durduruldu.")
    except Exception as e:
        log(f"Beklenmedik hata: {e}")
    finally:
        if headless:
            driver.quit()
        else:
            log("Tarayıcı açık bırakıldı. Manuel olarak kapatabilirsiniz.")

if __name__ == "__main__":
    run()