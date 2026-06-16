"""
Stage 6 — USD-bazlı BIST: TL enflasyonunu sinyalden çıkar + uzun temiz geçmiş aç.

Stage 5'te 'max' geçmiş çöktü (BIST TL enflasyonu). Çözüm: BIST'i USDTRY ile USD'ye
çevir. Hem enflasyon-nötr uzun geçmiş, hem de tüm evren ortak para biriminde (kesitsel
momentum karşılaştırması tutarlı). TL vs USD'yi aynı pencerede kıyaslar.

Çalıştır:  python -m scripts.run_stage6 [period=max]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import statistics

from finsent import db, prices, fx
from finsent.evaluation import stats
from finsent.portfolio import ls_backtest
from finsent.config import TICKERS

EVAL_HORIZON = 5
PERIOD = sys.argv[1] if len(sys.argv) > 1 else "max"
PPY = 252 / EVAL_HORIZON
N_TRIALS_GRID = [3, 7, 22]
N_REG = 7


def _report(name, rets):
    if len(rets) < 10:
        print(f"  {name}: yetersiz gözlem ({len(rets)})")
        return None
    sr = stats.sharpe(rets, PPY)
    mu = statistics.fmean(rets)
    p = stats.block_bootstrap_pvalue(rets)
    dsr = {nt: stats.deflated_sharpe(rets, nt)["dsr"] for nt in N_TRIALS_GRID}
    print(f"  {name}")
    print(f"    rebalans={len(rets)} | yıllık≈{mu*PPY*100:+.1f}% | Sharpe={sr:+.2f} | bootstrap p={p:.4f}")
    print(f"    Deflated Sharpe  " + "  ".join(f"n={nt}:{dsr[nt]:.3f}" for nt in N_TRIALS_GRID))
    return {"sharpe": sr, "p": p, "dsr": dsr}


def _run(conn, usd, label):
    res = ls_backtest.cross_sectional_walk_forward(
        conn, list(TICKERS), horizon=EVAL_HORIZON, interval="1d", n_splits=5, usd=usd)
    return _report(label, res["ls_returns"])


def main():
    conn = db.connect()
    print(f"[veri] USDTRY + hisse günlük (period={PERIOD})...")
    nfx = fx.update_fx(conn, period=PERIOD, interval="1d")
    prices.update_prices(conn, list(TICKERS), period=PERIOD, interval="1d")
    print(f"[veri] USDTRY bar: {nfx}")

    print("\n" + "=" * 74)
    print("  STAGE 6 — USD-BAZLI BIST (kesitsel L/S, max geçmiş)")
    print("=" * 74 + "\n")
    a = _run(conn, False, "A) TL-bazlı (enflasyon dahil):")
    print()
    b = _run(conn, True, "B) USD-bazlı (enflasyon-nötr):")
    print()
    print(f"  ÖNCEDEN-KAYITLI KARAR (n_trials={N_REG}):")
    for tag, r in (("TL-bazlı", a), ("USD-bazlı", b)):
        if not r:
            continue
        d = r["dsr"][N_REG]
        ok = d is not None and d > 0.95 and r["p"] is not None and r["p"] < 0.05
        print(f"   {tag:10}: Sharpe={r['sharpe']:+.2f} DSR(7)={d:.3f} p={r['p']:.4f} → "
              f"{'✓ GEÇTİ' if ok else '✗ sınırda/altında'}")
    print("=" * 74 + "\n")
    conn.close()


if __name__ == "__main__":
    main()
