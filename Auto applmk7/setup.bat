@echo off
setlocal
chcp 65001 >nul
echo ====================================
echo LinkedIn Job Finder MK7 - Setup
echo ====================================
echo.

echo 1. .env dosyasını oluşturuluyor...
if not exist ".env" (
    copy ".env.example" ".env"
    echo .env dosyası oluşturuldu. Lütfen LinkedIn kimlik bilgilerinizi girin.
) else (
    echo .env dosyası zaten mevcut.
)

echo.
echo 2. Python paketleri kuruluyor...
pip install -r requirements.txt

echo.
echo 3. Kurulum tamamlandı!
echo.
echo ÖNEMLİ: 
echo - .env dosyasını açın ve LinkedIn email/şifrenizi girin
echo - config.json dosyasında arama parametrelerini düzenleyin
echo - Çalıştırmak için run_mk7.bat kullanın
echo.
pause
