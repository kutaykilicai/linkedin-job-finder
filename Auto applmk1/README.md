# Auto Apply (Kutay) — LinkedIn & Kariyer.net

> Kişisel kullanım içindir. Her sitenin Kullanım Koşulları'na uyun. Aşırı otomasyon hesabınızı kısıtlayabilir.

## Kurulum
```bash
pip install -r requirements.txt
cp .env.example .env   # düzenleyin
python main.py
```

## Ne yapar?
- LinkedIn/Kariyer.net'e giriş yapar (Selenium).
- İstanbul içi ilanları filtreler; büyük şirketler için şehir esnekliği tanır.
- CV'yi yükleyip, dinamik ön yazı üretir (Jinja2).
- Başvurulan ilanları `data/applied_log.csv` ve `data/applied_log.json` dosyalarına kaydeder.

## Güvenlik
- Kimlik bilgilerini `.env` içinde tutun. 2FA açıksa girişte onay isteyebilir.
- Bu proje eğitim amaçlıdır.
