# LinkedIn İlan Analiz Botu - MK6

## Özellikler

MK6, LinkedIn iş ilanlarını tarayıp CV'nize göre uygunluk analizi yapan gelişmiş bir araçtır. **Otomatik başvuru yapmaz**, sadece uygun ilanları listeler.

### Temel Özellikler:
- 🔍 LinkedIn iş ilanlarını tarama
- 📊 CV'nize göre eşleşme skoru hesaplama (0-100)
- 💼 Deneyim yılı analizi ve tolerans kontrolü
- 🎯 Anahtar kelime bazlı filtreleme
- 📝 Detaylı analiz raporu (konsol + JSON)
- 🚫 Tekrar eden şirket ilanlarını filtreleme

## Kurulum

1. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyası oluşturun:
```
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
CHROME_USER_DATA_DIR=C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data
HEADLESS=false
```

## Kullanım

```bash
python linkedin_apply_mk6.py
```

### Konfigürasyon (config.json)

```json
{
  "queries": ["Siber Güvenlik Uzmanı", "IT Auditor"],
  "locations": ["İstanbul, Türkiye"],
  "filters": {
    "easy_apply_only": false,
    "date_posted": "r604800"
  },
  "max_pages": 3,
  "min_score": 65,
  "max_results": 20
}
```

## Eşleşme Algoritması

### Yüksek Öncelikli Anahtar Kelimeler (15-20 puan):
- IT Audit, Information Security, ISO 27001, COBIT, NIST, GRC, SOX
- Cloud Security, AWS, Azure, Penetration Testing, Risk Management

### Orta Öncelikli Anahtar Kelimeler (5-10 puan):
- Python automation, Wireshark, Nessus, Burp Suite
- Access Management, Incident Management, Banking Audit

### Mühendislik Bonusu (4-12 puan):
- Elektrik/Elektronik Mühendisi, Güç Elektroniği, Devre Tasarımı
- Endüstriyel Otomasyon, PWM, IGBT/MOSFET

### Negatif Sinyaller (-8 ile -35 puan):
- Helpdesk, L2 Support, Vardiya, 24/7 
- Backend Development, 6+ yıl deneyim şartı

### Deneyim Toleransı:
- **0-3 yıl**: Tam uyumlu (+0 puan)
- **4-5 yıl**: Kabul edilebilir (-2 puan)
- **6+ yıl**: Fazla deneyim (-5 ile -20 puan)

## Çıktı Formatı

### Konsol Çıktısı:
```
🎯 UYGUN İŞ İLANLARI (5 adet):
================================================================================

1. 📋 Siber Güvenlik Uzmanı
   🏢 ABC Teknoloji
   📍 İstanbul, Türkiye
   🔗 https://www.linkedin.com/jobs/view/123
   ⭐ Eşleşme Skoru: 86/100
   💼 Deneyim: 3-5 yıl - deneyim yakın (ben ~3 yıl)
   ✅ Güçlü yanlar: ISO 27001 (+15), Cloud Security (+15), IT Audit (+20)
   ⚠️  Riskler: SOC vardiya gerekliliği (-12)
```

### JSON Çıktısı (matches.json):
```json
[
  {
    "job_title": "Siber Güvenlik Uzmanı",
    "company": "ABC Teknoloji",
    "location": "İstanbul, Türkiye",
    "link": "https://www.linkedin.com/jobs/view/123",
    "match_score": 86,
    "experience_required_text": "3-5 yıl",
    "experience_interpretation": "deneyim yakın (ben ~3 yıl)",
    "top_reasons": ["ISO 27001 (+15)", "Cloud Security (+15)", "IT Audit (+20)"],
    "risks_or_gaps": ["SOC vardiya gerekliliği (-12)"]
  }
]
```

## Profil Bilgileri

Algoritma aşağıdaki profil bilgilerine göre optimize edilmiştir:

- **Eğitim**: Elektrik ve Elektronik Mühendisi (İstanbul Aydın Üniversitesi, %100 İngilizce, C1 İngilizce)
- **Deneyim**: 2 yıl 9 ay profesyonel tecrübe (~3 yıl)
- **Uzmanlık**: IT Audit / Siber Güvenlik
- **Teknik Beceriler**: COBIT, ISO 27001, NIST, GRC, SOX/GITC, Cloud Security (AWS/Azure), Nessus, Burp Suite, Wireshark, Python otomasyon
- **Sektör Deneyimi**: KPMG'de IT Denetçisi (Experienced Assistant), bankalar ve finans kuruluşları

## Notlar

- MK6 **otomatik başvuru yapmaz**, sadece analiz eder
- Tarayıcı `HEADLESS=false` ile görsel olarak çalışır
- Sonuçlar hem konsola hem `matches.json` dosyasına kaydedilir
- Aynı şirketten sadece en yüksek skorlu ilan gösterilir
- Maksimum 20 ilan gösterilir (config'te değiştirilebilir)
