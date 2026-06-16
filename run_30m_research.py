"""
30 DAKİKALIK ÖNGÖRÜLEBİLİRLİK ARAŞTIRMASI — dürüst ön ölçüm.

Soru: yarım saatlik (30m) barlarda, hisse bazında ÖLÇÜLEBİLİR bir yön edge'i var mı?
Yöntem: aynı sızıntısız makine — purged+embargoed walk-forward CV (validation.cross_validate)
30m barlar üzerinde, horizon=1 (≈30dk) ve horizon=2 (≈1s). Permütasyon p ile şans testi.
Uydurmuyoruz: sadece OOS'ta ölçülen IC/isabet raporlanır; eşik geçen hisse var mı bakılır.

Çalıştır:  python run_30m_research.py
"""
from __future__ import annotations
import sys
from finsent import db, prices
from finsent.config import TICKERS, TICKER_MARKET
from finsent.evaluation import validation, benchmarks, stats

INTERVAL = "30m"
PERIOD = "60d"        # yfinance 30m için üst sınır ~60 gün
HORIZONS = [1, 2]     # 1 bar ≈ 30dk, 2 bar ≈ 1s


def main():
    conn = db.connect()
    print(f"[1/3] 30m barlar çekiliyor (period={PERIOD})...")
    st = prices.update_prices(conn, list(TICKERS), period=PERIOD, interval=INTERVAL)
    bars = {t: st.get(t, 0) for t in TICKERS}
    have = {t: len(prices.closes(conn, t, INTERVAL)) for t in TICKERS}
    print("    bar sayıları (toplam db):")
    for t in sorted(TICKERS, key=lambda x: -have[x]):
        print(f"      {t:8s} {TICKER_MARKET.get(t,'US'):4s}  bars={have[t]:5d}  (yeni={bars[t]})")

    for H in HORIZONS:
        print(f"\n[2/3] Walk-forward CV — horizon={H} bar (~{H*30}dk), interval={INTERVAL}")
        cv = validation.cross_validate(conn, list(TICKERS), horizon=H, interval=INTERVAL,
                                       n_splits=5, embargo=2)
        ov = cv["overall"]
        n = ov.get("n") or 0
        ic = ov.get("ic")
        hit = ov.get("hit_rate")
        perm = benchmarks.permutation_pvalue(cv["oos_signals"], cv["oos_labels"]) \
            if cv["oos_signals"] else {}
        print(f"    HAVUZ (tüm hisseler birleşik): n={n}  OOS-IC={ic}  hit={hit}  "
              f"perm_p={perm.get('p_value')}")
        print(f"    skip={cv['skipped']}")
        # hisse bazında, IC'ye göre sırala — ölçülen edge nerede?
        pt = cv["per_ticker"]
        ranked = sorted(pt.items(), key=lambda kv: (kv[1].get("ic") or -9), reverse=True)
        print("    hisse bazında (IC azalan):")
        print("      tkr       n     IC      hit    folds")
        for t, m in ranked:
            print(f"      {t:8s} {m.get('n',0):5d}  {m.get('ic',0):+.4f}  "
                  f"{(m.get('hit_rate') or 0):.3f}  {m.get('folds',0)}")

    print("\n[3/3] Dürüst yorum:")
    print("    - OOS-IC ~ 0 ve perm_p > 0.1 ise: 30dk ≈ yazı-tura (öngörü yok) → UYDURMAYIZ.")
    print("    - Birkaç hisse IC>0 + hit>0.52 + n büyük ise: SADECE onları, dürüst etiketle göster.")
    conn.close()


if __name__ == "__main__":
    sys.exit(main())
