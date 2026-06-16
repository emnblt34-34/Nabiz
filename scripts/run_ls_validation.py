"""
Kesitsel Long-Short doğrulaması — Stage 2 sinyalini MARKET-NÖTR hasat edip
istatistiksel olarak sertleştirir (block-bootstrap + Deflated Sharpe).

Stage 2: günlük momentum IC=0.069 anlamlı AMA kesitsel (yön drift'i geçmiyor). Bu script
o sıralama sinyalini dolar-nötr L/S deftere çevirir; getiri serisinin Sharpe'ını
otokorelasyon-dayanıklı (blok-bootstrap) ve çoklu-test-düzeltmeli (DSR) sınar; 1/N-rank
benchmark'ıyla kıyaslar.

Çalıştır:  python -m scripts.run_ls_validation
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import statistics

from finsent import db, prices, features
from finsent.evaluation import stats
from finsent.portfolio import ls_backtest
from finsent.config import TICKERS

HORIZON = 5            # gün
INTERVAL = "1d"
PERIOD = sys.argv[1] if len(sys.argv) > 1 else "2y"   # ör: python -m scripts.run_ls_validation 5y
PPY = 252 / HORIZON    # rebalans/yıl (örtüşmesiz)
# DSR için denenen "deneme sayısı" (dürüst alt sınır: özellik/konfig çeşitliliği proxy'si)
N_TRIALS = len(features.FEATURES)


def _stat_block(name, rets):
    if len(rets) < 10:
        print(f"  {name}: yetersiz gözlem ({len(rets)})")
        return
    sr = stats.sharpe(rets, PPY)
    mu = statistics.fmean(rets)
    hit = sum(1 for r in rets if r > 0) / len(rets)
    p = stats.block_bootstrap_pvalue(rets)
    dsr = stats.deflated_sharpe(rets, N_TRIALS)
    print(f"  {name}")
    print(f"    rebalans: {len(rets)} | ortalama getiri/rebalans: {mu*100:+.3f}% | "
          f"yıllık ≈ {mu*PPY*100:+.1f}%")
    print(f"    Sharpe (yıllık): {sr:+.2f}" if sr is not None else "    Sharpe: –")
    print(f"    pozitif-rebalans oranı: {hit*100:.1f}%")
    print(f"    blok-bootstrap p (ort>0): {p}")
    print(f"    Deflated Sharpe (n_trials={dsr['n_trials']}): "
          f"dsr={dsr['dsr']:.3f}  (SR*/period={dsr['sr_star_per_period']})"
          if dsr["dsr"] is not None else "    Deflated Sharpe: –")
    return {"sharpe": sr, "p": p, "dsr": dsr["dsr"], "hit": hit}


def main():
    conn = db.connect()
    tickers = list(TICKERS)
    print(f"[veri] {INTERVAL} bar çekiliyor (period={PERIOD})...")
    st = prices.update_prices(conn, tickers, period=PERIOD, interval=INTERVAL)
    print(f"[veri] {len(st)} hisse cache'lendi")

    res = ls_backtest.cross_sectional_walk_forward(
        conn, tickers, horizon=HORIZON, interval=INTERVAL, n_splits=5, prefer_ml=True)

    print("\n" + "=" * 70)
    print(f"  KESİTSEL LONG-SHORT — market-nötr ölçüm (interval={INTERVAL}, ufuk={HORIZON}g)")
    print("=" * 70)
    if res["n_rebalances"] < 10:
        print(f"  Yetersiz rebalans ({res['n_rebalances']}).")
        conn.close()
        return
    print()
    ls = _stat_block("MODEL (rank L/S, dolar-nötr + ters-vol):", res["ls_returns"])
    print()
    bn = _stat_block("BENCHMARK (1/N-rank L/S):", res["bench_returns"])
    print()
    print("  KARAR:")
    if ls:
        ok_sr = (ls["sharpe"] or 0) > 0
        ok_p = ls["p"] is not None and ls["p"] < 0.05
        ok_dsr = ls["dsr"] is not None and ls["dsr"] > 0.95
        beats = bn and (ls["sharpe"] or 0) > (bn["sharpe"] or 0)
        if ok_sr and ok_p and ok_dsr:
            print(f"   ✓ L/S Sharpe pozitif, blok-bootstrap p<0.05 VE Deflated Sharpe>0.95")
            print(f"     → momentum edge'i MARKET-NÖTR, otokorelasyon+çoklu-test sonrası AYAKTA. İSPAT.")
        elif ok_sr and ok_p:
            print(f"   ~ p<0.05 ama Deflated Sharpe (dsr={ls['dsr']:.2f}) eşiği geçmiyor")
            print(f"     → çoklu-test sonrası anlamlılık zayıf; daha fazla veri/ufuk gerek.")
        else:
            print(f"   ✗ L/S edge istatistiksel olarak doğrulanmadı (Sharpe={ls['sharpe']}, p={ls['p']})")
            print(f"     → dürüst sonuç: sinyal market-nötr defterde anlamlı getiri üretmiyor.")
        if bn:
            print(f"   {'+' if beats else '-'} 1/N-rank benchmark'ı {'geçiyor' if beats else 'GEÇEMİYOR'}")
    print("=" * 70 + "\n")
    conn.close()


if __name__ == "__main__":
    main()
