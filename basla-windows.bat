@echo off
REM Nabiz baslatici (Windows). Cift tikla.
cd /d "%~dp0"
REM UTF-8 cikti: Turkce konsol kod sayfasinda (cp1254) bazi karakterler cokmesin.
set PYTHONIOENCODING=utf-8
chcp 65001 >nul
echo Nabiz kuruluyor ve baslatiliyor...
python -m pip install --quiet -r requirements.txt
echo.
echo   Tarayicida ac:  http://localhost:8000
echo   Durdurmak icin: Ctrl + C
echo.
python server.py
pause
