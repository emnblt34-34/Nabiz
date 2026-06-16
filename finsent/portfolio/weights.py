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

    def _demean(d):
        m = sum(d.values()) / len(d)
        return {t: v - m for t, v in d.items()}

    def _gnorm(d):
        gr = sum(abs(v) for v in d.values()) or 1.0
        return {t: v / gr for t, v in d.items()}

    # 3) ÖNCELİK Σw=0 (market-nötrlük — asıl bilimsel şart). Sharpe ölçek-bağımsız
    # olduğundan brüt'ü (Σ|w|) kesin 1 yapmak ZORUNLU değil; cap soft konsantrasyon limiti.
    # Sıra: demean → brüt~1 → cap → demean (Σw=0 KESİN, cap yaklaşık).
    # NOT: eski sürüm cap'ten SONRA yalnız normalize ediyordu → Σw≠0 (artık net piyasa
    # maruziyeti; market-nötr ölçümü bozar, Sharpe'ı şişirebilir). Bu test'le yakalandı.
    a = _gnorm(_demean(a))
    a = {t: max(-cap, min(cap, v)) for t, v in a.items()}   # cap
    w = _demean(a)                                          # Σw=0 KESİN (küçük kaydırma)

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
