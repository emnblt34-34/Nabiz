"""
Rejim göstergeleri — SİNYAL DEĞİL KOŞULLAMA değişkeni (araştırma: ADX/Hurst tek başına
öngörü taşımaz, değeri momentum/reversal'ı KOŞULLAMAKTADIR).

Temel olgu (Hurst): piyasalar bazı ölçeklerde TRENDLİ (momentum çalışır), bazılarında
ORTALAMAYA DÖNER (reversal çalışır). Bu modül her bar için rejimi ölçer; features.py
bunu momentumu "trend-geçitli" hale getirmek için kullanır.

Tümü NO-LOOK-AHEAD: yalnız closes[:i+1]. Bağımlılık yok (stdlib).
"""
from __future__ import annotations

import math


def efficiency_ratio(closes: list[float], i: int, n: int = 63) -> float:
    """
    Kaufman Efficiency Ratio: |net hareket| / toplam |adım hareketi|, son n bar. 0..1.
    Yüksek = doğrusal/güçlü trend; düşük = gidip-gelen (choppy) → ortalamaya dönüş.
    Geçmiş yetmezse 0.5 (nötr).
    """
    if i < n or n < 2:
        return 0.5
    net = abs(closes[i] - closes[i - n])
    path = sum(abs(closes[k] - closes[k - 1]) for k in range(i - n + 1, i + 1))
    return net / path if path else 0.5


def trend_score(closes: list[float], i: int, n: int = 63) -> float:
    """
    Trend yönü-gücü = 2·ER − 1 ∈ [−1, 1]. >0 trendli (momentum rejimi),
    <0 choppy (reversal rejimi), 0 nötr. Momentum bununla çarpılınca rejime adapte olur.
    """
    return 2.0 * efficiency_ratio(closes, i, n) - 1.0


def hurst(closes: list[float], i: int, window: int = 100) -> float:
    """
    Hurst üsteli (varyans-oranı yaklaşımı). >0.5 trend-süren, <0.5 ortalamaya-dönen,
    ~0.5 rastgele yürüyüş. Geçmiş yetmezse 0.5. No-look-ahead.

    Yöntem: k-adımlı toplam getirilerin varyansı ~ k^(2H) ölçeklenir; log-log eğim = 2H.
    """
    if i < window or window < 40:
        return 0.5
    seg = closes[i - window + 1:i + 1]
    rets = [math.log(seg[k] / seg[k - 1]) for k in range(1, len(seg))
            if seg[k - 1] > 0 and seg[k] > 0]
    if len(rets) < 20:
        return 0.5

    def var_of_ksum(rs, k):
        agg = [sum(rs[j:j + k]) for j in range(0, len(rs) - k + 1)]
        if len(agg) < 2:
            return None
        m = sum(agg) / len(agg)
        return sum((a - m) ** 2 for a in agg) / (len(agg) - 1)

    xs, ys = [], []
    for k in (1, 2, 4, 8):
        v = var_of_ksum(rets, k)
        if v and v > 0:
            xs.append(math.log(k))
            ys.append(math.log(v))
    if len(xs) < 2:
        return 0.5
    nn = len(xs)
    mx = sum(xs) / nn
    my = sum(ys) / nn
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den if den else 1.0
    return max(0.0, min(1.0, slope / 2.0))
