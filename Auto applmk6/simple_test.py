#!/usr/bin/env python3
"""
Basit LinkedIn Test - En temel ayarlarla
"""

import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def simple_test():
    print("🚀 Basit LinkedIn Testi...")
    
    # En basit Chrome ayarları
    opts = webdriver.ChromeOptions()
    
    # Sadece gerekli ayarlar
    temp_dir = os.path.join(tempfile.gettempdir(), "linkedin_simple_test")
    opts.add_argument(f"--user-data-dir={temp_dir}")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    
    # Anti-detection
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    
    try:
        print("Chrome başlatılıyor...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        
        # WebDriver gizle
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome başladı")
        print(f"Başlangıç URL: {driver.current_url}")
        
        # LinkedIn'e git
        print("\n🔗 LinkedIn'e gidiliyor...")
        driver.get("https://www.linkedin.com/")
        time.sleep(10)  # 10 saniye bekle
        
        print(f"Sonuç URL: {driver.current_url}")
        print(f"Sayfa başlığı: {driver.title}")
        
        if "linkedin" in driver.current_url.lower():
            print("✅ LinkedIn'e başarıyla gidildi!")
        else:
            print("❌ LinkedIn'e gidilemedi")
            print("Sayfayı manuel kontrol edin...")
        
        input("\nDevam etmek için Enter'a basın...")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    simple_test()
