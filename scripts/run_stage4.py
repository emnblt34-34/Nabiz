"""
Stage 4 — Çok-ufuk ensemble + ÖNCEDEN-KAYITLI (pre-registered) protokolle dürüst DSR.

İki şey:
  1) ENSEMBLE: 5/10/20-gün ufuklarına eğitilmiş modellerin kesitsel sinyallerini ortalar
     (ufuk çeşitlendirmesi gürültüyü düşürür). Tek-ufuk (Stage 3) ile kıyaslanır.
  2) DÜRÜST n_trials: Deflated Sharpe n_trials'a çok duyarlı. p-hacking yapmamak için
     DSR'ı BİRDEN ÇOK n_trials'da (3 / 7 / 22) şeffaf raporlarız; önceden-kayıtlı protokol
     (docs/on-kayit-protokol.md) n_trials=7'yi gerekçesiyle sabitler. Hiçbir sayı gizlenmez.

Çalıştır:  python -m scripts.run_stage4 [period=5y]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import statistics

from finsent import db, prices
from finsent.evaluation import stats
from finsent.portfolio import ls_backtest
from finsent.config import TICKERS

EVAL_HORIZON = 5
PERIOD = sys.argv[1] if len(sys.argv) > 1 else "5y"
PPY = 252 / EVAL_HORIZON
N_TRIALS_GRID = [3, 7, 22]      # şeffaflık: DSR'ı birkaç n_trials'da göster
N_TRIALS_REGISTERED = 7         # önceden-kayıtlı (docs/on-kayit-protokol.md)


def _report(name, rets):
    if len(rets) < 10:
        print(f"  {name}: yetersiz gözlem ({len(rets)})")
        return None
    sr = stats.sharpe(rets, PPY)
    mu = statistics.fmean(rets)
    p = stats.block_bootstrap_pvalue(rets)
    dsr = {nt: stats.deflated_sharpe(rets, nt)["dsr"] for nt in N_TRIALS_GRID}
    print(f"  {name}")
    print(f"    rebalans={len(rets)} | yıllık≈{mu*PPY*100:+.1f}% | Sharpe={sr:+.2f} | "
          f"blok-bootstrap p={p:.4f}")
    print(f"    Deflated Sharpe  " + "  ".join(f"n_trials={nt}:{dsr[nt]:.3f}" for nt in N_TRIALS_GRID))
    return {"sharpe": sr, "p": p, "dsr": dsr}


def main():
    conn = db.connect()
    tickers = list(TICKERS)
    print(f"[veri] günlük bar (period={PERIOD})...")
    prices.update_prices(conn, tickers, period=PERIOD, interval="1d")

    print("\n" + "=" * 72)
    print("  STAGE 4 — ÇOK-UFUK ENSEMBLE + ÖNCEDEN-KAYITLI DSR")
    print("=" * 72)

    single = ls_backtest.cross_sectional_walk_forward(
        conn, tickers, horizon=EVAL_HORIZON, interval="1d", n_splits=5, prefer_ml=True)
    ens = ls_backtest.cross_sectional_walk_forward_ensemble(
        conn, tickers, eval_horizon=EVAL_HORIZON, train_horizons=(5, 10, 20),
        interval="1d", n_splits=5, prefer_ml=True)

    print()
    s = _report("TEK-UFUK (Stage 3, ufuk=5g):", single["ls_returns"])
    print()
    e = _report("ENSEMBLE (5/10/20g, Stage 4):", ens["ls_returns"])
    print()
    b = _report("BENCHMARK (1/N-rank, ensemble sinyali):", ens["bench_returns"])
    print()

    print(f"  ÖNCEDEN-KAYITLI KARAR (n_trials={N_TRIALS_REGISTERED}, bkz. docs/on-kayit-protokol.md):")
    if e:
        d = e["dsr"][N_TRIALS_REGISTERED]
        ok = d is not None and d > 0.95 and e["p"] is not None and e["p"] < 0.05
        if ok:
            print(f"   ✓ Ensemble L/S: DSR={d:.3f} (>0.95) VE blok-bootstrap p={e['p']:.4f} (<0.05)")
            print(f"     → ÖNCEDEN-KAYITLI protokol altında, market-nötr kesitsel momentum edge'i")
            print(f"       çoklu-test + otokorelasyon zırhından GEÇTİ. Tez (zayıf-orta öngörülebilirlik) DESTEKLENDİ.")
        else:
            print(f"   ~ Ensemble DSR(n_trials={N_TRIALS_REGISTERED})={d:.3f}, p={e['p']:.4f}")
            print(f"     → {'p anlamlı ama DSR<0.95' if (e['p'] and e['p']<0.05) else 'eşik geçilmedi'};"
                  f" şeffaf grid yukarıda. Daha çok veri/ufuk gerek.")
        if s and e["sharpe"] and s["sharpe"]:
            better = e["sharpe"] > s["sharpe"]
            print(f"   {'+' if better else '-'} Ensemble, tek-ufku {'geçiyor' if better else 'geçmiyor'} "
                  f"(Sharpe {e['sharpe']:.2f} vs {s['sharpe']:.2f})")
    print("=" * 72 + "\n")
    conn.close()


if __name__ == "__main__":
    main()
