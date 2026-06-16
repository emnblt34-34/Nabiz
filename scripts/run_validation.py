"""
Stage 0/2 — DÜRÜST değerlendirme: sızıntılı in-sample vs purged+embargoed walk-forward
OOS; null/temel çizgiler + permütasyon p. "Borsa öngörülebilir" iddiasının dürüst sınaması.

Modlar:
  python -m scripts.run_validation            # saatlik (60m, ufuk 3 bar) — mevcut canlı model
  python -m scripts.run_validation daily      # GÜNLÜK (1d, ufuk 5 gün) — momentumun (1-12 ay)
                                              #   gerçek kanıt bölgesi. 2y günlük bar çeker.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finsent import db, forecast, prices, features
from finsent.evaluation import validation, benchmarks, backtest
from finsent.config import TICKERS, HORIZON_BARS, PRICE_INTERVAL


def _fmt(v, pct=False):
    if v is None:
        return "  –  "
    return f"{v*100:5.1f}%" if pct else f"{v:+.4f}"


def run(interval, horizon, period=None, fetch=False):
    conn = db.connect()
    tickers = list(TICKERS)

    if fetch and period:
        print(f"[veri] {interval} bar çekiliyor (period={period})...")
        stats = prices.update_prices(conn, tickers, period=period, interval=interval)
        print(f"[veri] {len(stats)} hisse, ~{sum(stats.values())} bar cache'lendi")

    # 1) SIZINTILI in-sample (fit=ölçüm aynı veri)
    X, y, _ = backtest._pool(conn, tickers, horizon, interval)
    if not X:
        print(f"\n[!] {interval} için yeterli veri yok. (daily modda önce fetch gerekir.)")
        conn.close()
        return
    fc, cal = forecast.fit_from_data(X, y, prefer_ml=True)
    leaky = backtest.evaluate(fc, X, y)

    # 2) DÜRÜST OOS — purged + embargoed walk-forward
    cv = validation.cross_validate(conn, tickers, horizon, prefer_ml=True, interval=interval)
    oos = cv["overall"]

    # 3) Null / temel çizgiler (OOS test örnekleri üzerinde)
    sig, lab = cv["oos_signals"], cv["oos_labels"]
    br = benchmarks.base_rate(lab)
    bh = benchmarks.buy_and_hold(lab)
    rs = benchmarks.random_sign(lab)
    perm = benchmarks.permutation_pvalue(sig, lab) if sig else {}

    print("\n" + "=" * 70)
    print(f"  DÜRÜST DEĞERLENDİRME — interval={interval}, ufuk={horizon} bar")
    print("=" * 70)
    print(f"  Model: {fc.name} | OOS örnek: {oos.get('n')} "
          f"({cv['n_folds_total']} fold, {len(cv['per_ticker'])} hisse)")
    print(f"  Özellik sayısı: {len(features.FEATURES)} "
          f"(momentum ailesi: {len(features.MOMENTUM_FEATURES)})")
    print()
    print("  ÖLÇÜM                       HIT-RATE        IC        n")
    print("  " + "-" * 56)
    print(f"  SIZINTILI in-sample        {_fmt(leaky.get('hit_rate'), True)}      {_fmt(leaky.get('ic'))}   {leaky.get('n')}")
    print(f"  DÜRÜST OOS (walk-forward)  {_fmt(oos.get('hit_rate'), True)}      {_fmt(oos.get('ic'))}   {oos.get('n')}")
    if leaky.get("ic") is not None and oos.get("ic") is not None:
        d_ic = leaky["ic"] - oos["ic"]
        print(f"  >>> SIZINTI ŞİŞMESİ                       {d_ic:+.4f}")
    print()
    # momentum özelliklerinin in-sample IC'si (umut verici mi? — yalnız ipucu)
    mic = {k: cal["price_ic"].get(k) for k in features.MOMENTUM_FEATURES if cal["price_ic"].get(k)}
    if mic:
        top = sorted(mic.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        print("  Momentum özellik IC (in-sample, ipucu): " +
              ", ".join(f"{k}={v:+.3f}" for k, v in top))
        print()
    print("  NULL / TEMEL ÇİZGİLER (OOS, yenilmesi gereken):")
    print(f"    base rate / buy&hold hit          : {_fmt(br, True)} / {_fmt(bh.get('hit_rate'), True)}")
    print(f"    random-sign (şans) ort. hit / IC  : {_fmt(rs.get('hit_rate'), True)} / {_fmt(rs.get('ic'))}")
    print(f"    permütasyon: actual_IC={_fmt(perm.get('actual_ic'))}  p={perm.get('p_value')}")
    print()
    print("  KARAR:")
    ic = oos.get("ic") or 0.0
    hit = oos.get("hit_rate") or 0.0
    p = perm.get("p_value")
    if p is not None and p < 0.05 and ic > 0:
        print(f"   + OOS IC permütasyon-null'dan ANLAMLI (p={p}<0.05) — zayıf da olsa gerçek sinyal!")
    else:
        print(f"   - OOS IC null'dan ayırt edilemiyor (p={p}) — bu kurguyla öngörü kanıtı yok (dürüst sonuç).")
    bhh = bh.get("hit_rate")
    if bhh is not None:
        cmp = "geçiyor" if hit > bhh else "GEÇEMİYOR"
        print(f"   {'+' if hit>bhh else '-'} buy&hold ({_fmt(bhh, True)}) {cmp} (hit={_fmt(hit, True)})")
    print("=" * 70 + "\n")
    conn.close()


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "hourly"
    if mode == "daily":
        run(interval="1d", horizon=5, period="2y", fetch=True)
    else:
        run(interval=PRICE_INTERVAL, horizon=HORIZON_BARS, period=None, fetch=False)


if __name__ == "__main__":
    main()
