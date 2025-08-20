
# LinkedIn Easy Apply Bot (Kariyer.net olmadan)

## Kurulum
1) Python 3.10+ kurulu olsun.
2) Gerekli paketleri yükleyin:
   pip install selenium python-dotenv webdriver-manager

## .env
`.env.example` dosyasını `.env` olarak kopyalayın ve doldurun:
- LINKEDIN_EMAIL, LINKEDIN_PASSWORD
- RESUME_PATH: CV'nizin tam yolu
- CHROME_USER_DATA_DIR: C:\Users\Kutay\AppData\Local\Google\Chrome\User Data\Default

## Ayarlar
- `config.json` içinde arama kelimeleri, lokasyonlar, filtreler, sayfa sayısı ve başvuru limiti var.

## Çalıştırma
python linkedin_apply.py

> Notlar:
> - Çok adımlı/karmaşık formlar tespit edilirse otomatik iptal edilir.
> - Tarayıcıyı gizli çalıştırmak için `.env` içinde HEADLESS=true yapabilirsiniz.
