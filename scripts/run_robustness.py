"""
Stage 8 — Dayanıklılık: USD+hacim kesitsel momentum edge'i STABİL mi yoksa overfit/
tek-dönem flukı mı? DSR(7)=0.935'e güvenmeden önce bunu sınarız.

- Alt-dönem Sharpe: 16y'yi 4 döneme böl, her birinde Sharpe (çoğu pozitif mi?).
- Block-bootstrap Sharpe CI: alt sınır (p05) > 0 ise edge sağlam.

Çalıştır:  python -m scripts.run_robustness
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finsent import db, prices, fx
from finsent.evaluation import stats, robustness
from finsent.portfolio import ls_backtest
from finsent.config import TICKERS

PPY = 252 / 5


def main():
    conn = db.connect()
    print("[veri] USDTRY + hisse günlük (max)...")
    fx.update_fx(conn, period="max", interval="1d")
    prices.update_prices(conn, list(TICKERS), period="max", interval="1d")

    res = ls_backtest.cross_sectional_walk_forward(
        conn, list(TICKERS), horizon=5, interval="1d", n_splits=5, usd=True)
    rets, dates = res["ls_returns"], res["dates"]
    if len(rets) < 40:
        print("yetersiz gözlem"); conn.close(); return

    overall = stats.sharpe(rets, PPY)
    sp = robustness.subperiod_sharpe(rets, dates, n_blocks=4, ppy=PPY)
    ci = robustness.sharpe_bootstrap_ci(rets, ppy=PPY)

    print("\n" + "=" * 70)
    print("  STAGE 8 — DAYANIKLILIK (USD + hacim-olay kesitsel L/S, 16y)")
    print("=" * 70)
    print(f"  Genel: rebalans={len(rets)} | yıllık Sharpe={overall:+.2f}")
    print()
    print("  ALT-DÖNEM SHARPE (stabil mi, yoksa tek döneme mi yığılı?):")
    for b in sp["blocks"]:
        bar = "+" if (b["sharpe"] or 0) > 0 else "-"
        print(f"    {b['period']}  n={b['n']:>4}  Sharpe={b['sharpe']:+.2f} {bar}")
    print(f"    → {sp['n_positive']}/{sp['n_blocks']} dönem pozitif")
    print()
    if ci:
        print("  BLOCK-BOOTSTRAP SHARPE GÜVEN ARALIĞI:")
        print(f"    p05={ci['sharpe_p05']:+.2f}  ortanca={ci['sharpe_p50']:+.2f}  p95={ci['sharpe_p95']:+.2f}")
        print(f"    pozitif Sharpe oranı: {ci['frac_positive']*100:.0f}%")
    print()
    # --- Dürüst karar ---
    stable = (sp["n_positive"] >= 3) and (ci and ci["sharpe_p05"] > 0)
    print("  KARAR:")
    if stable:
        print("   ✓ STABİL: çoğu dönemde pozitif VE bootstrap alt sınırı (p05) > 0.")
        print("     → 0.935 DSR tek-dönem flukı değil; zayıf-ama-GERÇEK ve dağılmış bir edge.")
    else:
        why = []
        if sp["n_positive"] < 3:
            why.append(f"yalnız {sp['n_positive']}/4 dönem pozitif")
        if ci and ci["sharpe_p05"] <= 0:
            why.append(f"bootstrap alt sınırı p05={ci['sharpe_p05']} ≤ 0")
        print(f"   ✗ KIRILGAN: {', '.join(why)}.")
        print("     → 0.935 DSR'ye GÜVENME; edge belirli dönemlere yığılı / overfit riski yüksek.")
    print("=" * 70 + "\n")
    conn.close()


if __name__ == "__main__":
    main()
