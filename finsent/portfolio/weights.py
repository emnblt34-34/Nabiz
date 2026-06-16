"""
Kesitsel ağırlıklandırma — "Tahmin Gücü Ölçer" çekirdeği.

Amaç kâr değil: forecast sinyalinin NET (piyasa-yönünden arındırılmış) öngörü gücünü
ölçmek. Tek-hisse mutlak tahmin gürültülü; ama hisseleri BİRBİRİNE GÖRE sıralamak
(cross-sectional rank) daha sağlam. Üstü long / altı short + dolar-nötr → portföy
getirisi piyasa yönünden mekanik izole; kalan PnL = saf sıralama isabeti.

Tasarım (bkz. docs/portfoy-mimarisi.md): optimizör YOK (N≈T'de Σ tekil, error-
maximization); rank + ters-vol + dolar-nötr + cap yeterli ve robust.
"""
from __future__ import annotations


def cross_sectional_weights(signals: dict, vols: dict, cap: float = 0.25) -> dict:
    """
    Kesitsel sinyal → long-short ağırlık. Adımlar:
      rank → merkeze al → ters-vol ölçekle → dolar-nötrle → cap → brüt=1 normalize.
    Dönüş: {ticker: weight}, Σw≈0 (dolar-nötr), Σ|w|=1 (birim-bahis).
    """
    ts = [t for t in signals if signals[t] is not None]
    n = len(ts)
    if n < 2:
        return {t: 0.0 for t in signals}

    # 1) rank (outlier'a bağışık) → merkeze al
    order = sorted(ts, key=lambda t: signals[t])
    rank = {t: i for i, t in enumerate(order)}
    mean_rank = (n - 1) / 2.0
    g = {t: rank[t] - mean_rank for t in ts}

    # 2) ters-vol ölçekle (oynak isimler risk bütçesini gasp etmesin)
    a = {t: g[t] / (vols.get(t) if vols.get(t) else 1.0) for t in ts}

    # 3) dolar-nötrle (ters-vol nötrlüğü bozar → ortalamayı çıkar)
    m = sum(a.values()) / n
    a = {t: a[t] - m for t in ts}

    # 4) brüt=1 normalize, sonra cap, sonra tekrar normalize
    gross = sum(abs(v) for v in a.values()) or 1.0
    w = {t: a[t] / gross for t in ts}
    w = {t: max(-cap, min(cap, v)) for t, v in w.items()}
    gross2 = sum(abs(v) for v in w.values()) or 1.0
    w = {t: v / gross2 for t, v in w.items()}

    for t in signals:
        w.setdefault(t, 0.0)
    return w


def rank_long_short(signals: dict) -> dict:
    """
    1/N-rank benchmark: üst yarı eşit-long, alt yarı eşit-short (dolar-nötr, brüt≈1).
    "Yenilmesi gereken" naif kesitsel kol.
    """
    ts = sorted([t for t in signals if signals[t] is not None], key=lambda t: signals[t])
    n = len(ts)
    w = {t: 0.0 for t in signals}
    k = n // 2
    if k == 0:
        return w
    for t in ts[:k]:
        w[t] = -0.5 / k
    for t in ts[-k:]:
        w[t] = 0.5 / k
    return w
