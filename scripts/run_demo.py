"""
Offline demo: SampleCollector ile tüm pipeline'ı uçtan uca çalıştırır,
sonra güncel skorları ekrana basar. İnternet gerekmez.

Çalıştır:  python -m scripts.run_demo
"""
from finsent.pipeline import run_once
from finsent.collectors import SampleCollector
from finsent import db


def main():
    stats = run_once([SampleCollector()], prefer_transformer=False)
    print("\n=== ÖZET ===", stats)

    conn = db.connect()
    print("\n=== GÜNCEL SKORLAR (24h) ===")
    print(f"{'TICKER':8} {'SENT':>7} {'MOM':>7} {'VOL':>4} {'POS%':>6} {'NEG%':>6}")
    for s in db.latest_scores(conn, window="24h"):
        print(f"{s['ticker']:8} {s['sentiment']:+7.3f} {s['momentum']:+7.3f} "
              f"{s['volume']:>4} {s['pos_share']*100:>5.0f}% {s['neg_share']*100:>5.0f}%")
    conn.close()


if __name__ == "__main__":
    main()
