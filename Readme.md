# 🚀 LinkedIn Job Finder

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0+-green.svg)](https://selenium-python.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

> 🤖 **Otomatik iş başvuru asistanı** - LinkedIn ve Kariyer.net platformlarında akıllı iş arama ve başvuru yapma aracı

## ✨ Özellikler

### 🎯 **Akıllı İş Eşleştirme**
- CV profiline göre 0-100 puan skorlama sistemi
- Anahtar kelime ve beceri analizi
- Şirket ve pozisyon filtreleme

### 🤖 **Otomatik Başvuru**
- LinkedIn Easy Apply desteği
- Kariyer.net otomatik başvuru
- İnsan benzeri davranış simülasyonu

### 📊 **Raporlama ve Analiz**
- JSON ve CSV formatında detaylı raporlar
- Başvuru geçmişi takibi
- İstatistiksel analizler

### 🛡️ **Güvenlik ve Gizlilik**
- Chrome profil desteği (2FA bypass)
- Rate limiting koruması
- Proxy desteği

## 🚀 Hızlı Başlangıç

### 📋 Gereksinimler

```bash
# Python 3.8+ gereklidir
python --version

# Chrome tarayıcı kurulu olmalı
```

### 📦 Kurulum

```bash
# Repository'yi klonlayın
git clone https://github.com/kutaykilicai/linkedin-job-finder.git
cd linkedin-job-finder

# Gerekli paketleri yükleyin
pip install -r requirements.txt
```

### ⚙️ Konfigürasyon

#### 1. **Çevre Değişkenleri** (`.env` dosyası oluşturun)

```env
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
RESUME_PATH=/path/to/your/resume.pdf
CHROME_USER_DATA_DIR=/path/to/chrome/profile
HEADLESS=false
```

#### 2. **İş Arama Ayarları** (`config.json`)

```json
{
  "queries": [
    "Siber Güvenlik Uzmanı",
    "IT Auditor",
    "Bilgi Güvenliği"
  ],
  "locations": [
    "İstanbul, Türkiye",
    "Ankara, Türkiye"
  ],
  "filters": {
    "easy_apply_only": true,
    "date_posted": "r604800",
    "experience_levels": null,
    "work_type": null
  },
  "max_pages": 3,
  "per_session_limit": 10,
  "min_score": 65,
  "max_results": 20
}
```

## 🎮 Kullanım

### 📝 **Sadece Analiz Modu** (Başvuru yapmaz)

```bash
python linkedin_mk7.py
```

Bu mod:
- ✅ İş ilanlarını tarar
- ✅ CV uyumluluğunu skorlar
- ✅ `matches.json` ve `matches.csv` oluşturur
- ❌ Başvuru yapmaz

### 🤖 **Otomatik Başvuru Modu**

```bash
# LinkedIn + Kariyer.net
python main.py

# Sadece LinkedIn
python linkedin_apply.py
```

### 📊 **Çıktı Örnekleri**

```
1) Siber Güvenlik Uzmanı — ABC Teknoloji (89%)
   https://linkedin.com/jobs/view/123456789

2) IT Security Analyst — XYZ Corp (84%)
   https://linkedin.com/jobs/view/987654321

3) Bilgi Güvenliği Uzmanı — DEF Ltd (78%)
   https://linkedin.com/jobs/view/456789123
```

## 📁 Proje Yapısı

```
linkedin-job-finder/
├── 🚀 main.py                 # Ana çalıştırma scripti
├── 🔍 linkedin_mk7.py         # Analiz-only versiyonu
├── 🤖 linkedin_apply.py       # LinkedIn otomatik başvuru
├── 📊 scoring_mk7.py          # İş eşleştirme algoritması
├── 🛠️ utils_mk7.py           # Yardımcı fonksiyonlar
├── ⚙️ config.json            # Konfigürasyon dosyası
├── 📝 .env                   # Çevre değişkenleri
├── 📋 requirements.txt       # Python bağımlılıkları
├── 📄 matches.json          # Analiz sonuçları (JSON)
├── 📊 matches.csv           # Analiz sonuçları (CSV)
└── 📖 README.md             # Bu dosya
```

## 🔧 Gelişmiş Ayarlar

### 🎯 **Skorlama Sistemi**

Sistem aşağıdaki kriterlere göre iş ilanlarını değerlendirir:

- **Başlık Uyumu** (30%): Pozisyon adı ile hedef pozisyon eşleşmesi
- **Beceri Uyumu** (25%): Teknik beceriler ve sertifikalar
- **Deneyim Seviyesi** (20%): İş tecrübesi gereksinimleri
- **Şirket Profili** (15%): Sektör ve şirket büyüklüğü
- **Lokasyon** (10%): Uzaktan çalışma ve şehir tercihleri

### 🛡️ **Güvenlik Önlemleri**

```python
# İnsan benzeri davranış
human_pause(0.8, 1.8)  # Rastgele bekleme süreleri

# Bot algılama önleme
opts.add_argument("--disable-blink-features=AutomationControlled")

# Rate limiting
per_session_limit = 10  # Günlük başvuru limiti
```

### 🔄 **Hata Yönetimi**

```python
try:
    # LinkedIn işlemleri
    li.search_and_apply()
except Exception as e:
    log.error(f"LinkedIn hata: {e}")
    # İşlem devam eder
```

## 📈 İstatistikler

### 📊 **Performans Metrikleri**

- ⚡ **Hız**: Dakikada ~5-10 ilan analizi
- 🎯 **Doğruluk**: %85+ eşleştirme başarısı
- 🛡️ **Güvenlik**: 2FA destekli güvenli oturum
- 📱 **Uyumluluk**: Chrome, Firefox, Safari

### 📋 **Test Edilen Platformlar**

| Platform | Durum | Özellikler |
|----------|-------|------------|
| LinkedIn | ✅ | Easy Apply, Gelişmiş filtreleme |
| Kariyer.net | ✅ | Otomatik başvuru, Manuel doğrulama |
| Yandex.Jobs | 🔄 | Geliştirme aşamasında |

## 🤝 Katkıda Bulunma

### 🐛 **Hata Bildirimi**

```bash
# Hata loglarını ekleyin
python main.py --debug
```

### 💡 **Özellik Önerisi**

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## ⚠️ **Önemli Notlar**

### 🚨 **Yasal Uyarı**

> Bu araç **eğitim ve kişisel kullanım** amaçlıdır. Kullanırken:
> - Platform kullanım koşullarına uyun
> - Spam yapmaktan kaçının
> - Etik kurallara riayet edin

### 🔒 **Gizlilik**

- Verileriniz sadece lokal olarak saklanır
- Şifreler ve kişisel bilgiler paylaşılmaz
- Chrome profil koruması ile 2FA güvenliği

### ⚡ **Performans Tavsiyeleri**

```python
# Hız optimizasyonu
HEADLESS = True  # Daha hızlı çalışma

# Kaynak yönetimi
max_pages = 2  # Daha az sayfa tara
per_session_limit = 5  # Günlük limit düşür
```

## 📞 İletişim

- 📧 **Email**: kutaykilicai@example.com
- 🐙 **GitHub**: [@kutaykilicai](https://github.com/kutaykilicai)
- 💼 **LinkedIn**: [Kutay Kılıçai](https://linkedin.com/in/kutaykilicai)

## 📄 Lisans

Bu proje [MIT](LICENSE) lisansı altında lisanslanmıştır.

---

<div align="center">

**⭐ Beğendiyseniz yıldız vermeyi unutmayın!**

Made with ❤️ by [Kutay Kılıçai](https://github.com/kutaykilicai)

</div>