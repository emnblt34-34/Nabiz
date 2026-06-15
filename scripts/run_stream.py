"""
Anlık (hot path) — ücretsiz, gerçek zamanlı kaynaklar (haber + sosyal).
Belirli aralıkla döngüde çalışır. X gibi pahalı kaynak BURADA kullanılmaz;
maliyet kontrolü için anlık katman bedava kaynaklara dayanır.

Çalıştır:  python -m scripts.run_stream
"""
import time
from finsent.pipeline import run_once
from finsent.collectors import RSSNewsCollector, StockTwitsCollector, RedditCollector

INTERVAL_SEC = 300  # 5 dk

def main():
    collectors = [RSSNewsCollector(), StockTwitsCollector(), RedditCollector()]
    while True:
        try:
            stats = run_once(collectors, prefer_transformer=False)
            print("STREAM döngüsü:", stats)
        except Exception as e:
            print("STREAM hata:", e)
        time.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    main()
