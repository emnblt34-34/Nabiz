"""
GÜVEN (confidence) KALİBRASYON ARAŞTIRMASI — "güven" demeden önce ölç.

Soru: Momentum-hizalama (mom_21/63/126/252 sinyalle aynı yönde mi?) + trend rejimi (ER),
bir hissenin O ANKİ sinyalinin OOS isabetini GERÇEKTEN artırıyor mu? Yani "yüksek güven"
diyeceğimiz durumlar gerçekten daha mı isabetli? (Değilse "güven" göstermek dürüstlük dışı.)

Yöntem: günlük USD kesitsel kurulum (horizon=5), sızıntısız walk-forward. Her OOS noktasında
güven-proxy hesapla → kovalara böl → kova başına isabet/IC ölç. Monotonik artıyorsa kalibre.

Çalıştır:  python run_confidence_research.py
"""
from __future__ import annotations
from finsent import db, fx, features, forecast
from finsent.config import TICKERS
from finsent.evaluation.validation import walk_forward_folds
from finsent.portfolio.cross_section import CS_HORIZON

LOOKBACKS = [21, 63, 126, 252]


def _sign(x: float) -> int:
    return 1 if x > 0 else -1 if x < 0 else 0


def confidence(feat: dict, signal: float) -> float:
    """Güven-proxy [0..1]: momentum-hizalama (0.6) + trend rejimi (0.4). SİNYAL DEĞİL — kalite."""
    s = _sign(signal)
    if s == 0:
        return 0.0
    align = sum(1 for n in LOOKBACKS if _sign(feat.get(f"mom_{n}", 0.0)) == s) / len(LOOKBACKS)
    er = feat.get("er", 0.5)
    regime = max(0.0, min(1.0, (er - 0.45) / 0.20))
    return 0.6 * align + 0.4 * regime


def main():
    conn = db.connect()
    pts = []  # (conf, signal, fwd)
    for t in TICKERS:
        closes, _ = fx.usd_series(conn, t, "1d")
        if len(closes) < features.MIN_BARS + CS_HORIZON + 40:
            continue
        X, y = features.build_price_dataset(closes, CS_HORIZON)
        folds = walk_forward_folds(len(X), n_splits=5, horizon=CS_HORIZON, embargo=1)
        for tr, te in folds:
            fc, _ = forecast.fit_from_data([X[i] for i in tr], [y[i] for i in tr], True)
            for i in te:
                sig = fc.signal_only(X[i])
                pts.append((confidence(X[i], sig), sig, y[i]))
    conn.close()

    n = len(pts)
    print(f"Toplam OOS nokta: {n}\n")

    def bucket_stats(lo, hi, name):
        sub = [(c, s, f) for (c, s, f) in pts if lo <= c < hi and _sign(s) != 0]
        if not sub:
            print(f"  {name:14s} n=0")
            return
        hit = sum(1 for _, s, f in sub if _sign(s) == _sign(f)) / len(sub)
        # IC (sinyal vs forward) bu kovada
        ss = [s for _, s, _ in sub]; ff = [f for _, _, f in sub]
        ms, mf = sum(ss) / len(ss), sum(ff) / len(ff)
        cov = sum((s - ms) * (f - mf) for s, f in zip(ss, ff))
        ds = sum((s - ms) ** 2 for s in ss) ** 0.5; dfv = sum((f - mf) ** 2 for f in ff) ** 0.5
        ic = cov / (ds * dfv) if ds and dfv else 0.0
        avg_fwd_dir = sum(f * _sign(s) for _, s, f in sub) / len(sub)  # sinyal-yönlü ort. getiri
        print(f"  {name:14s} n={len(sub):5d}  isabet={hit:.4f}  IC={ic:+.4f}  "
              f"sinyal-yonlu-ort-getiri={avg_fwd_dir:+.4f}")

    print("Güven kovasına göre OOS performans (kalibre ise isabet artmalı):")
    bucket_stats(0.0, 0.40, "düşük <0.40")
    bucket_stats(0.40, 0.66, "orta 0.40-66")
    bucket_stats(0.66, 1.01, "yüksek >=0.66")
    print("\n  (referans: yazı-tura isabet = 0.50)")
    print("\nYORUM: yüksek kova isabeti düşük kovadan BELİRGİN yüksekse → 'güven' KALİBRE,")
    print("       arayüzde dürüstçe gösterilebilir. Aksi halde güven göstermek yanıltıcı olur.")


if __name__ == "__main__":
    main()
