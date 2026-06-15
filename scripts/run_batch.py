"""
Günlük batch (cold path) — gerçek kaynaklarla. Tüm günü temiz hesaplar.
Cron örneği:  0 2 * * *  cd /path/finsent && python -m scripts.run_batch

İnternet + (opsiyonel) feedparser/requests gerektirir.
"""
from finsent.pipeline import run_once
from finsent.collectors import (
    RSSNewsCollector, RedditCollector, StockTwitsCollector, KAPCollector,
)

def main():
    collectors = [
        RSSNewsCollector(),
        RedditCollector(),
        StockTwitsCollector(),
        KAPCollector(),
    ]
    # FinBERT kuruluysa kullan; değilse otomatik lexicon.
    stats = run_once(collectors, prefer_transformer=True)
    print("BATCH bitti:", stats)

if __name__ == "__main__":
    main()
