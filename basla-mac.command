#!/bin/bash
# Nabız başlatıcı (Mac/Linux). Çift tıkla ya da: bash basla-mac.command
cd "$(dirname "$0")"
echo "Nabız kuruluyor ve başlatılıyor..."
python3 -m pip install --quiet -r requirements.txt
echo ""
echo "  Tarayıcıda aç:  http://localhost:8000"
echo "  Durdurmak için: Ctrl + C"
echo ""
python3 server.py
