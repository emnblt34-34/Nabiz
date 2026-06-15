"""
Stage 0 — DÜRÜST değerlendirme: sızıntılı in-sample backtest vs purged+embargoed
walk-forward OOS; üstüne null/temel çizgiler (buy&hold, random-sign, persistence)
ve permütasyon p-değeri. "Borsa öngörülebilir" iddiasının ilk dürüst sınaması.

Çalıştır:  python -m scripts.run_validation
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finsent import db, forecast, validation, benchmarks, features
from finsent.config import TICKERS, HORIZON_BARS


def _fmt(v, pct=False):
    if v is None:
        return "  –  "
    return f"{v*100:5.1f}%" if pct else f"{v:+.4f}"


def main():
    conn = db.connect()
    tickers = list(TICKERS)

    # 1) Mevcut (SIZINTILI) in-sample backtest — eski raporlanan sayı
    fc, cal, bt = forecast.train_forecaster(conn, tickers, HORIZON_BARS)
    leaky = bt["overall"]

    # 2) DÜRÜST OOS — purged + embargoed walk-forward
    cv = validation.cross_validate(conn, tickers, HORIZON_BARS, prefer_ml=True)
    oos = cv["overall"]

    # 3) Null / temel çizgiler (OOS test örnekleri üzerinde)
    sig, lab = cv["oos_signals"], cv["oos_labels"]
    br = benchmarks.base_rate(lab)
    bh = benchmarks.buy_and_hold(lab)
    rs = benchmarks.random_sign(lab)
    perm = benchmarks.permutation_pvalue(sig, lab) if sig else {}

    print("\n" + "=" * 66)
    print("  STAGE 0 — DÜRÜST ÖNGÖRÜ DEĞERLENDİRMESİ")
    print("=" * 66)
    print(f"  Model: {fc.name} | ufuk: {HORIZON_BARS} bar | OOS örnek: {oos.get('n')} "
          f"({cv['n_folds_total']} fold, {len(cv['per_ticker'])} hisse)")
    if cv["skipped"]:
        print(f"  (yetersiz veri atlanan: {', '.join(cv['skipped'])})")
    print()
    print("  ÖLÇÜM                       HIT-RATE        IC        n")
    print("  " + "-" * 56)
    print(f"  SIZINTILI in-sample        {_fmt(leaky.get('hit_rate'), True)}      {_fmt(leaky.get('ic'))}   {leaky.get('n')}")
    print(f"  DÜRÜST OOS (walk-forward)  {_fmt(oos.get('hit_rate'), True)}      {_fmt(oos.get('ic'))}   {oos.get('n')}")
    # sızıntı şişmesi
    if leaky.get("ic") is not None and oos.get("ic") is not None:
        d_ic = leaky["ic"] - oos["ic"]
        d_hit = ((leaky.get("hit_rate") or 0) - (oos.get("hit_rate") or 0)) * 100
        print(f"  >>> SIZINTI ŞİŞMESİ        {d_hit:+5.1f}pp     {d_ic:+.4f}")
    print()
    print("  NULL / TEMEL ÇİZGİLER (OOS, yenilmesi gereken):")
    print(f"    pozitif-getiri tabanı (base rate) : {_fmt(br, True)}")
    print(f"    buy & hold (hep yukarı) hit       : {_fmt(bh.get('hit_rate'), True)}")
    print(f"    random-sign (şans) ort. hit / IC  : {_fmt(rs.get('hit_rate'), True)} / {_fmt(rs.get('ic'))}")
    print(f"    permütasyon testi: actual_IC={_fmt(perm.get('actual_ic'))}  "
          f"p={perm.get('p_value')}  [{perm.get('one_sided','')}]")
    print()

    # --- KARAR (falsifiability) ---
    print("  KARAR:")
    ic = oos.get("ic") or 0.0
    hit = oos.get("hit_rate") or 0.0
    p = perm.get("p_value")
    if p is not None and p < 0.05 and ic > 0:
        print(f"   + OOS IC permütasyon-null'dan ANLAMLI (p={p}<0.05) — zayıf da olsa gerçek sinyal işareti.")
    else:
        print(f"   - OOS IC null'dan AYIRT EDİLEMİYOR (p={p}) — bu ufuk/özelliklerle"
              f" öngörü kanıtı YOK. Bu da dürüst, bilimsel bir sonuçtur.")
    bhh = bh.get("hit_rate")
    if bhh is not None and hit <= bhh:
        print(f"   - Model buy&hold yön isabetini ({_fmt(bhh, True)}) GEÇEMİYOR — yön edge'i zayıf.")
    elif bhh is not None:
        print(f"   + Model buy&hold'u ({_fmt(bhh, True)}) geçiyor (hit={_fmt(hit, True)}).")
    print()
    print("  Not: Stage 0. Çoklu-test düzeltmesi (Deflated Sharpe / PBO / SPA-FDR)")
    print("       ve blok-bootstrap Stage 1'de eklenecek.")
    print("=" * 66 + "\n")
    conn.close()


if __name__ == "__main__":
    main()
