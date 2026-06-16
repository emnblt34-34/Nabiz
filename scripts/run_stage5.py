"""
Stage 5 — Veri/araç genişletme: daha uzun geçmiş + KRİPTO (kriteri değiştirmeden
DSR(7)>0.95'i muhafazakâr geçmeye çalış). n↑ → SR*↓; kripto → kesitsel genişlik +
bağımsız varlık sınıfı OOS doğrulaması.

Coin CANLI ürüne eklenmez — yalnız bilimsel evren (config.science_universe).
Şeffaf: DSR n_trials {3,7,22} grid'inde; önceden-kayıtlı n_trials=7 (docs/on-kayit-protokol.md).

Çalıştır:  python -m scripts.run_stage5 [period=max]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import statistics

from finsent import db, prices
from finsent.evaluation import stats
from finsent.portfolio import ls_backtest
from finsent.config import TICKERS, CRYPTO_TICKERS, science_universe

EVAL_HORIZON = 5
PERIOD = sys.argv[1] if len(sys.argv) > 1 else "max"
PPY = 252 / EVAL_HORIZON
N_TRIALS_GRID = [3, 7, 22]
N_TRIALS_REGISTERED = 7


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


def _run(conn, universe, label):
    res = ls_backtest.cross_sectional_walk_forward(
        conn, universe, horizon=EVAL_HORIZON, interval="1d", n_splits=5, prefer_ml=True)
    return _report(label, res["ls_returns"])


def main():
    conn = db.connect()
    eq = list(TICKERS)
    uni = science_universe()
    print(f"[veri] günlük bar (period={PERIOD}) — {len(uni)} araç ({len(eq)} hisse + {len(CRYPTO_TICKERS)} kripto)...")
    prices.update_prices(conn, uni, period=PERIOD, interval="1d")

    print("\n" + "=" * 74)
    print("  STAGE 5 — GENİŞLETİLMİŞ EVREN + DAHA UZUN GEÇMİŞ (kesitsel L/S)")
    print("=" * 74 + "\n")

    a = _run(conn, eq, "A) Hisse-only (16), max geçmiş:")
    print()
    b = _run(conn, uni, f"B) Hisse + Kripto ({len(uni)}), max geçmiş:")
    print()

    print(f"  ÖNCEDEN-KAYITLI KARAR (n_trials={N_TRIALS_REGISTERED}):")
    for tag, r in (("Hisse-only", a), ("Hisse+Kripto", b)):
        if not r:
            continue
        d = r["dsr"][N_TRIALS_REGISTERED]
        ok = d is not None and d > 0.95 and r["p"] is not None and r["p"] < 0.05
        mark = "✓ GEÇTİ" if ok else "✗ sınırda/altında"
        print(f"   {tag:14}: DSR(7)={d:.3f}, bootstrap p={r['p']:.4f} → {mark}")
    print("\n  (n_trials=3/7/22 grid yukarıda; tek sayı seçip 'kazandık' demiyoruz.)")
    print("=" * 74 + "\n")
    conn.close()


if __name__ == "__main__":
    main()
