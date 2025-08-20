# LinkedIn İş İlanı Analiz Botu MK6 🎯

**Amaç:** LinkedIn ilanlarını tarayıp açıklamalarını analiz eder, CV profilinize göre 0-100 arası uygunluk skoru hesaplar. **KEsİNLİKLE otomatik başvuru yapmaz!**

## 🚀 Hızlı Başlangıç

### 1. Gerekli Paketleri Kurun
```bash
pip install selenium python-dotenv webdriver-manager beautifulsoup4
```

### 2. .env Dosyası Oluşturun
```env
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_password
CHROME_USER_DATA_DIR=
HEADLESS=false
```

### 3. Programı Çalıştırın
```bash
# Test kontrolü
python test_mk6.py

# Ana program
python linkedin_mk6_clean.py
```

## 📊 Skorlama Sistemi

**Profiliniz:** Elektrik-Elektronik Mühendisi + IT Audit/Siber Güvenlik (~3 yıl deneyim)

### Yüksek Öncelik (+12 ~ +20 puan)
- IT Audit, Siber Güvenlik, Information Security
- ISO 27001, COBIT, NIST, GRC, SOX
- Cloud Security, Penetration Testing, Risk Management

### Orta Öncelik (+5 ~ +10 puan)
- Python, Automation, Wireshark, Nessus, Burp Suite
- Policy/Standard, Access Management, Incident Response

### Mühendislik Bonusu (+4 ~ +12 puan)
- Elektrik/Elektronik Mühendisi
- Güç Elektroniği, Devre Tasarımı, Endüstriyel Otomasyon

### Negatif Faktörler (-8 ~ -35 puan)
- Helpdesk/L2 Support, Vardiya çalışması
- Backend Development, 6+ yıl deneyim şartı

### Deneyim Toleransı
- **0-3 yıl:** Tam uyumlu ✅
- **4-5 yıl:** Kabul edilebilir (-2 ~ -5 puan)
- **6+ yıl:** Büyük ceza (-15 ~ -35 puan)

## 📋 Çıktı Formatı

### Konsol Çıktısı
```
1) Siber Güvenlik Uzmanı — ABC Teknoloji
   https://www.linkedin.com/jobs/view/123
   Skor: 86% | Deneyim: 3-5 yıl → deneyim yakın (ben ~3 yıl)
   Gerekçe: ISO27001/NIST/COBIT + IT audit + cloud sec
```

### matches.json
```json
{
  "job_title": "Siber Güvenlik Uzmanı",
  "company": "ABC Teknoloji",
  "location": "İstanbul, Türkiye",
  "link": "https://www.linkedin.com/jobs/view/123",
  "match_score": 86,
  "experience_required_text": "3-5 yıl",
  "experience_interpretation": "deneyim yakın (ben ~3 yıl)",
  "top_reasons": ["ISO 27001, NIST, COBIT", "Cloud Security", "IT Audit"],
  "risks_or_gaps": []
}
```

## ⚙️ Konfigürasyon (config.json)

```json
{
  "queries": [
    "Siber Güvenlik Uzmanı",
    "IT Auditor", 
    "Information Security"
  ],
  "locations": ["İstanbul, Türkiye"],
  "filters": {
    "easy_apply_only": false,
    "date_posted": "r604800",
    "experience_levels": null,
    "work_type": null
  },
  "max_pages": 3,
  "min_score": 65,
  "max_results": 20
}
```

## 🛡️ Güvenlik ve Limitler

- **.env dosyası hiç bir koşulda log'a yazılmaz**
- İnsan benzeri davranış (rastgele beklemeler)
- Popup/overlay agresif temizleme
- Rate limit koruması
- **Otomatik başvuru kesinlikle yapmaz**

## 🧪 Test Senaryoları

### Görünür Tarayıcı ile Test
```bash
# .env dosyasında HEADLESS=false
python linkedin_mk6_clean.py
```

### Headless Mode Test  
```bash
# .env dosyasında HEADLESS=true
python linkedin_mk6_clean.py
```

### Başarı Kriterleri
✅ LinkedIn'e girer  
✅ En az 1 sayfadan ilan açıklaması çeker  
✅ Skor ≥65 olanları listeler  
✅ matches.json UTF-8 formatında oluştur  
❌ Hiç bir otomatik başvuru yapılmaz  

## 📁 Dosya Yapısı

```
mk6/
├── linkedin_mk6_clean.py    # Ana program
├── config.json              # Arama ayarları  
├── .env                     # Giriş bilgileri (GIT'e eklenmez)
├── test_mk6.py              # Test araçları
├── matches.json             # Çıktı dosyası
└── README_MK6.md            # Bu dosya
```

## 🔧 Mimari

**Modüler tasarım:** 
- `login_and_nav()` - LinkedIn girişi
- `collect_job_cards()` - İlan toplama  
- `extract_job_description()` - Açıklama çıkarma
- `extract_experience()` - Deneyim analizi
- `score_job()` - Skorlama algoritması
- `filter_and_rank()` - Filtreleme ve sıralama
- `save_results()` & `print_results()` - Çıktı

**Sağlamlık özellikleri:**
- Alternatif CSS seçiciler
- Stale element retry mekanizması  
- Timeout yönetimi
- Exception handling

## ⚠️ Önemli Notlar

1. **Yasal Uyum:** Sadece iş arama amacıyla kullanın
2. **Rate Limiting:** Çok sık çalıştırmayın
3. **2FA:** İlk girişte 2FA gerekebilir  
4. **Chrome Profil:** `CHROME_USER_DATA_DIR` ayarlayarak oturum sürdürün

---

**MK6 = Temiz Mimari, Sadece Analiz, Sıfır Başvuru** 🎯
