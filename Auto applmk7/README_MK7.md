# LinkedIn Job Finder MK7

LinkedIn iş ilanlarını otomatik olarak tarar, CV profilinize göre 0-100 arası skorlar ve en uygun ilanları listeler. **Başvuru yapmaz, sadece analiz eder.**

## 🚀 Hızlı Başlangıç

1. **Kurulum**: `setup.bat` dosyasını çalıştırın
2. **Yapılandırma**: `.env` dosyasına LinkedIn bilgilerinizi girin
3. **Çalıştırma**: `run_mk7.bat` ile başlatın

## 📋 Detaylı Kurulum

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Yapılandırma Dosyaları

**.env dosyası** (LinkedIn kimlik bilgileri):
```env
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_password
HEADLESS=false
CHROME_USER_DATA_DIR=
```

**config.json** (Arama parametreleri):
```json
{
  "queries": ["Siber Güvenlik Uzmanı", "IT Auditor"],
  "locations": ["İstanbul, Türkiye"],
  "min_score": 65,
  "max_results": 20
}
```

## 📊 Çıktılar
- `matches.json`: Detaylı sonuçlar (JSON formatında)
- `matches.csv`: Excel'de açılabilir format

## 🔧 Sorun Giderme
- Chrome güncel olmalı
- LinkedIn hesabı aktif olmalı
- 2FA varsa manuel olarak tamamlayın
