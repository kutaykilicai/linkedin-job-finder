# LinkedIn İş Başvuru Botu MK6

LinkedIn'de otomatik iş arama ve eşleşme skorlaması yapan Python botu.

## 🚀 Özellikler

- ✅ Otomatik LinkedIn giriş
- 🔍 Çoklu arama terimi desteği
- 📊 Akıllı iş eşleştirme skorlaması
- 📋 JSON formatında sonuç raporu
- 🎯 Deneyim seviyesi analizi
- 🧹 Otomatik popup/overlay temizleme

## 📋 Gereksinimler

```bash
pip install selenium python-dotenv webdriver-manager beautifulsoup4
```

## ⚙️ Kurulum

1. **Projeyi klonlayın:**
```bash
git clone https://github.com/kutaykilicai/linkedinbotmk6.git
cd linkedinbotmk6
```

2. **Gerekli paketleri yükleyin:**
```bash
pip install selenium python-dotenv webdriver-manager beautifulsoup4
```

3. **`.env` dosyası oluşturun:**
```bash
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_password
CHROME_USER_DATA_DIR=
HEADLESS=false
```

## 🎯 Kullanım

```bash
python linkedin_apply_mk6.py
```

## ⚙️ Konfigürasyon

`config.json` dosyasından ayarları düzenleyebilirsiniz:

- `queries`: Arama terimleri listesi
- `locations`: Arama yapılacak lokasyonlar
- `max_pages`: Taranacak maksimum sayfa sayısı
- `min_score`: Minimum eşleşme skoru (0-100)
- `max_results`: Maksimum sonuç sayısı

## 📊 Skorlama Sistemi

Bot, iş ilanlarını şu kriterlere göre skorlar:

### Yüksek Öncelikli (15-20 puan)
- Siber güvenlik, IT audit, bilgi güvenliği
- ISO 27001, COBIT, NIST, GRC
- Penetration testing, risk management

### Orta Öncelikli (5-10 puan)
- Python, otomasyon araçları
- Cloud platformları (AWS, Azure)
- Güvenlik araçları (Nessus, Wireshark)

### Negatif Faktörler
- Helpdesk/destek rolleri (-10 puan)
- Yüksek deneyim gereksinimi (-15 puan)
- Vardiya sistemi (-15 puan)

## 📁 Çıktı

Program `matches.json` dosyasında sonuçları kaydeder:

```json
{
  "job_title": "Siber Güvenlik Uzmanı",
  "company": "ABC Şirketi",
  "location": "İstanbul",
  "link": "https://linkedin.com/jobs/view/123456",
  "match_score": 85,
  "experience_required_text": "3-5 yıl",
  "top_reasons": ["bilgi güvenliği (+18)", "python (+5)"],
  "risks_or_gaps": []
}
```

## 🛡️ Güvenlik

- `.env` dosyası `.gitignore`'da - GitHub'a yüklenmez
- Chrome user data directory kullanarak oturum sürdürme
- Anti-bot tespitine karşı human-like davranış

## 📝 Lisans

MIT License

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın
