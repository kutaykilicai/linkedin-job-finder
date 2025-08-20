@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

pip install -r requirements.txt

python linkedin_mk7.py
pause
