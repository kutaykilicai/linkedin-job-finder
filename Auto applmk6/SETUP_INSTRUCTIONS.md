# MK6 Kurulum Talimatları 🚀

## 1. .env Dosyası Oluşturun

**Proje klasöründe `.env` dosyası oluşturun ve şu içeriği yazın:**

```env
LINKEDIN_EMAIL=gerçek_email@gmail.com
LINKEDIN_PASSWORD=gerçek_şifreniz
CHROME_USER_DATA_DIR=C:\Users\Kutay\AppData\Local\Google\Chrome\User Data
HEADLESS=false
```

### ⚠️ Önemli Notlar:

1. **LINKEDIN_EMAIL**: Gerçek LinkedIn email adresinizi yazın
2. **LINKEDIN_PASSWORD**: Gerçek LinkedIn şifrenizi yazın  
3. **CHROME_USER_DATA_DIR**: Chrome profil klasörünüz (otomatik bulunur, boş bırakabilirsiniz)
4. **HEADLESS**: 
   - `false` = Tarayıcı görünür (önerilen)
   - `true` = Tarayıcı gizli

## 2. Hızlı Test

```bash
# 1. Gereksinim kontrolü
python test_mk6.py

# 2. Ana program (HEADLESS=false ile)
python linkedin_mk6_clean.py
```

## 3. Sorun Giderme

### Headless Çalışmıyor
- `.env` dosyasında `HEADLESS=false` yapın
- İlk testte tarayıcı görünür modda çalıştırın

### LinkedIn Giriş Yapamıyor
1. `.env` dosyasında email/şifre doğru mu?
2. 2FA aktif mi? Manuel olarak tamamlayın
3. Chrome profilinizde zaten giriş yapılmış mı?

### Chrome Profil Hatası
- `CHROME_USER_DATA_DIR=` boş bırakın
- Program otomatik bulacak

## 4. İlk Çalıştırma

```bash
# Adım 1: Test
python test_mk6.py

# Adım 2: Ana program (tarayıcı görünür)
python linkedin_mk6_clean.py

# Başarılı olursa, headless mode:
# .env dosyasında HEADLESS=true yapın
```

## 5. Beklenen Çıktı

✅ **Başarılı çalıştırma:**
- LinkedIn'e giriş yapar
- İş ilanlarını tarar
- Skorlar ve matches.json oluşturur
- Konsola uygun ilanları listeler

❌ **Hiç bir otomatik başvuru yapmaz!**
