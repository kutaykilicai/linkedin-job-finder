#!/usr/bin/env python3
"""
LinkedIn Navigasyon Test Aracı
Chrome'un LinkedIn'e gidip gitmediğini test eder
"""

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_navigation():
    """Chrome navigasyon testini yap"""
    print("🧪 LinkedIn Navigasyon Testi Başlıyor...")
    
    # .env dosyasını yükle
    load_dotenv()
    
    # Chrome ayarları
    opts = webdriver.ChromeOptions()
    
    # Temel ayarlar - Ayrı profil kullan
    import tempfile
    temp_profile = os.path.join(tempfile.gettempdir(), "linkedin_test_chrome_profile")
    opts.add_argument(f"--user-data-dir={temp_profile}")
    print(f"🔧 Temp profil: {temp_profile}")
    
    # Profil ayarları
    opts.add_argument("--profile-directory=Default")
    
    # Anti-automation ayarları
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--no-first-run")
    opts.add_argument("--disable-default-apps")
    opts.add_argument("--start-maximized")
    
    # User agent
    opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        # Chrome'u başlat
        print("🚀 Chrome başlatılıyor...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        
        # WebDriver özelliğini gizle
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome başlatıldı!")
        
        # 1. Başlangıç durumu
        print(f"🔍 Başlangıç URL: {driver.current_url}")
        print(f"🔍 Başlangıç başlık: {driver.title}")
        
        # 2. LinkedIn'e git
        print("\n📍 LinkedIn'e gidiliyor...")
        driver.get("https://www.linkedin.com/")
        time.sleep(5)
        
        print(f"🔍 LinkedIn sonrası URL: {driver.current_url}")
        print(f"🔍 LinkedIn sonrası başlık: {driver.title}")
        
        # 3. Başarı kontrolü
        if "linkedin.com" in driver.current_url:
            print("✅ LinkedIn'e başarıyla gidildi!")
        else:
            print("❌ LinkedIn'e gidilemedi!")
            print("🔧 JavaScript ile deneniyor...")
            driver.execute_script("window.location.href = 'https://www.linkedin.com/';")
            time.sleep(5)
            print(f"🔍 JavaScript sonrası URL: {driver.current_url}")
        
        # 4. Login sayfası testi
        print("\n🔐 Login sayfasına gidiliyor...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(5)
        
        print(f"🔍 Login URL: {driver.current_url}")
        print(f"🔍 Login başlık: {driver.title}")
        
        if "login" in driver.current_url:
            print("✅ Login sayfasına başarıyla gidildi!")
        else:
            print("❌ Login sayfasına gidilemedi!")
        
        print("\n⏸️  Test tamamlandı. Chrome penceresi açık kalacak.")
        print("Chrome'u manuel olarak kapatabilirsiniz.")
        
        # Sonuç
        input("Devam etmek için Enter'a basın...")
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_navigation()
