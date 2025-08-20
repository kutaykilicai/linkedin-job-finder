#!/usr/bin/env python3
"""
LinkedIn MK6 Test Dosyası
Kısa test senaryoları için kullanılır
"""

import json
import sys
from pathlib import Path

def check_requirements():
    """Gerekli paketlerin kurulu olup olmadığını kontrol et"""
    print("🔍 Gerekli paketler kontrol ediliyor...")
    
    required_packages = [
        ("selenium", "from selenium import webdriver"),
        ("python-dotenv", "from dotenv import load_dotenv"),
        ("webdriver-manager", "from webdriver_manager.chrome import ChromeDriverManager"),
        ("beautifulsoup4", "from bs4 import BeautifulSoup")
    ]
    
    missing = []
    for package_name, import_statement in required_packages:
        try:
            exec(import_statement)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name}")
            missing.append(package_name)
    
    if missing:
        print(f"\n⚠️  Eksik paketler: {', '.join(missing)}")
        print("Kurulum için:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    print("✅ Tüm paketler mevcut!")
    return True

def check_config_files():
    """Gerekli dosyaların varlığını kontrol et"""
    print("\n📁 Konfig dosyaları kontrol ediliyor...")
    
    # .env dosyası
    if Path(".env").exists():
        print("✅ .env dosyası mevcut")
        
        # İçeriğini kontrol et (güvenlik için detay gösterme)
        with open(".env", "r") as f:
            content = f.read()
            if "LINKEDIN_EMAIL" in content and "LINKEDIN_PASSWORD" in content:
                print("✅ .env içinde gerekli alanlar var")
            else:
                print("❌ .env dosyasında LINKEDIN_EMAIL veya LINKEDIN_PASSWORD eksik")
                return False
    else:
        print("❌ .env dosyası yok")
        print("Oluşturmanız gereken .env dosyası:")
        print("""
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_password
CHROME_USER_DATA_DIR=
HEADLESS=false
        """)
        return False
    
    # config.json dosyası
    if Path("config.json").exists():
        print("✅ config.json dosyası mevcut")
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                
            required_fields = ["queries", "locations", "filters", "max_pages", "min_score", "max_results"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                print(f"❌ config.json'da eksik alanlar: {missing_fields}")
                return False
            else:
                print("✅ config.json içinde gerekli alanlar var")
                print(f"   - {len(config['queries'])} arama terimi")
                print(f"   - {len(config['locations'])} lokasyon")
                print(f"   - Min skor: {config['min_score']}")
                print(f"   - Max sayfa: {config['max_pages']}")
                
        except json.JSONDecodeError:
            print("❌ config.json formatı hatalı")
            return False
    else:
        print("❌ config.json dosyası yok")
        return False
    
    return True

def create_minimal_test_config():
    """Hızlı test için minimal config oluştur"""
    minimal_config = {
        "queries": ["Siber Güvenlik"],
        "locations": ["İstanbul, Türkiye"],
        "filters": {
            "easy_apply_only": False,
            "date_posted": "r86400",  # Son 1 gün
            "experience_levels": None,
            "work_type": None
        },
        "max_pages": 1,  # Sadece ilk sayfa
        "min_score": 50,  # Düşük eşik
        "max_results": 5   # Az sonuç
    }
    
    with open("config_test.json", "w", encoding="utf-8") as f:
        json.dump(minimal_config, f, ensure_ascii=False, indent=2)
    
    print("✅ config_test.json oluşturuldu (hızlı test için)")

def main():
    print("🧪 LinkedIn MK6 Test Araçları\n")
    
    # Paket kontrolü
    if not check_requirements():
        print("\n❌ Eksik paketleri kurdan sonra tekrar deneyin")
        sys.exit(1)
    
    # Dosya kontrolü
    if not check_config_files():
        print("\n❌ Gerekli dosyaları oluşturun")
        create_minimal_test_config()
        sys.exit(1)
    
    print("\n✅ Tüm gereksinimler karşılandı!")
    print("\n🚀 Başlatma komutları:")
    print("Normal çalıştırma:")
    print("  python linkedin_mk6_clean.py")
    print("\nHızlı test (config_test.json ile):")
    print("  # config.json yerine config_test.json kullanmak için kod düzenlemesi gerekir")
    print("\nHeadless mod:")
    print("  .env dosyasında HEADLESS=true yapın")

if __name__ == "__main__":
    main()
