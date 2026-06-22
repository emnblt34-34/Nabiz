#!/usr/bin/env python3
"""
Nabız BULUT nöbeti — GitHub Actions cron ile 7/24 çalışır (PC kapalı olsa bile).
Kripto + hisse haber RSS'lerini tarar; katalizör-kelimeli, SON ~35 dakikada yayınlanmış
başlıkları Telegram'a yollar. Stateless (zaman-pencereli dedup) — sadece Python stdlib,
pip kurulumu YOK.

Ortam değişkenleri (GitHub Secrets):
  TG_TOKEN  = BotFather'dan alınan bot token
  TG_CHAT   = senin chat_id'in
  WINDOW_MIN= kaç dakikalık pencere taransın (cron aralığı + buffer; varsayılan 35)

chat_id öğrenmek için:  python cloud/nabiz_cloud_watch.py --chatid   (TG_TOKEN set olmalı)
"""
import os
import re
import sys
import html
import email.utils
import datetime
import urllib.request
import urllib.parse

TG_TOKEN = os.environ.get("TG_TOKEN", "").strip()
TG_CHAT = os.environ.get("TG_CHAT", "").strip()
WINDOW_MIN = int(os.environ.get("WINDOW_MIN", "35"))

# Kripto haberlerinde aranan katalizör kelimeleri (hisse haberlerinde filtre YOK — hepsi watchlist)
KW = [
    "treasury", "etf", "approv", "spot etf", "listing", " lists ", "delist",
    "partnership", "partners with", "acquir", "integrat", "unlock", "staking",
    "billion", "buyback", "mainnet", " launch", "raises", "sec filing", "upgrade",
    "price target", " stake", "adds ", "halving", "airdrop", "hack", "exploit",
]
CRYPTO_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://news.bitcoin.com/feed/",
    "https://decrypt.co/feed",
]
STOCK_FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=HOOD,MRVL,INTC,AAPL,MU,FLEX,NVDA&region=US&lang=en-US",
]
# Hisse haberlerinde alâka filtresi: başlık bizim isimlerimizden birini ya da bir katalizör
# kelimesini içermeli (yoksa "Costco/SpaceX" gibi genel piyasa gürültüsü elenir)
STOCK_NAMES = [
    "robinhood", "hood", "marvell", "mrvl", "intel", "intc", "apple", "aapl",
    "micron", " mu ", "flex", "nvidia", "nvda", "foundry", "semiconductor", "chip",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")


def parse_items(xml):
    out = []
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
        tm = re.search(r"<title>(.*?)</title>", block, re.S)
        dm = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        if not tm:
            continue
        title = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", tm.group(1))).strip()
        pub = None
        if dm:
            try:
                pub = email.utils.parsedate_to_datetime(dm.group(1).strip())
            except Exception:
                pub = None
        out.append((title, pub))
    return out


def send(msg):
    if not (TG_TOKEN and TG_CHAT):
        print("[TG yapilandirilmadi] " + msg)
        return
    url = "https://api.telegram.org/bot%s/sendMessage" % TG_TOKEN
    data = urllib.parse.urlencode(
        {"chat_id": TG_CHAT, "text": msg, "disable_web_page_preview": "true"}
    ).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20).read()
    except Exception as e:
        print("TG hata:", e)


def print_chatid():
    if not TG_TOKEN:
        print("Once TG_TOKEN set et."); return
    u = "https://api.telegram.org/bot%s/getUpdates" % TG_TOKEN
    print(fetch(u))


def main():
    if "--chatid" in sys.argv:
        print_chatid(); return
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(minutes=WINDOW_MIN)
    hits, seen = [], set()
    for feeds, tag in [(CRYPTO_FEEDS, "KRIPTO"), (STOCK_FEEDS, "HISSE")]:
        for f in feeds:
            try:
                for title, pub in parse_items(fetch(f)):
                    if pub is not None and pub < cutoff:
                        continue  # sadece son pencere
                    low = title.lower()
                    if tag == "KRIPTO":
                        if not any(k in low for k in KW):
                            continue
                    else:  # HISSE: bizim isim VEYA katalizör kelimesi olmali
                        if not (any(n in low for n in STOCK_NAMES) or any(k in low for k in KW)):
                            continue
                    if title in seen:
                        continue
                    seen.add(title)
                    hits.append((tag, title))
            except Exception as e:
                print("feed hata:", f, e)
    for tag, t in hits[:8]:
        send("\U0001F4F0 NABIZ %s: %s" % (tag, t))
    if os.environ.get("TEST_PING", "").lower() == "true":
        send("✅ Nabiz BULUT nobeti BAGLANDI. Katalizor cikinca buraya alarm dusecek (kripto + hisse). Bu bir test mesajidir.")
    print("Gonderilen:", min(len(hits), 8), "| test:", os.environ.get("TEST_PING", ""), "| pencere(dk):", WINDOW_MIN, "|", now.isoformat())


if __name__ == "__main__":
    main()
