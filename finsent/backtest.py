"""
Backtest & kalibrasyon — öngörüyü "gerçek" yapan katman.

İki iş:
  1) calibrate(): fiyat geçmişinden her FİYAT özelliğinin forward-return ile
     korelasyonunu (information coefficient) ve ölçekleyiciyi (mean/std) çıkarır.
     Kural modelinin ağırlıkları böylece VERİDEN gelir, elle uydurulmaz.
  2) backtest_forecaster(): modeli geçmiş üzerinde çalıştırıp yön isabet oranı,
     IC ve up/down sinyallerinin ortalama getirisini ölçer — sinyal kendi
     sicilini taşır.

Önemli dürüstlük notu: geçmiş DUYGU verisi olmadığından backtest, modelin
FİYAT bileşeninin gerçek isabetini ölçer. Duygu katkısı canlı tahmin
günlüğünde (predictions tablosu) zamanla doğrulanır.
"""
from __future__ import annotations

import math

from . import prices, features
from .config import PRICE_INTERVAL, NEUTRAL_BAND


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def _pool(conn, tickers, horizon: int, interval: str = PRICE_INTERVAL):
    """Tüm tickerların fiyat geçmişini (özellik, forward_return) olarak biriktir."""
    X: list[dict] = []
    y: list[float] = []
    per_ticker: dict[str, tuple[list[dict], list[float]]] = {}
    for t in tickers:
        c = prices.closes(conn, t, interval)
        if len(c) < features.MIN_BARS + horizon:
            continue
        xt, yt = features.build_price_dataset(c, horizon)
        if xt:
            per_ticker[t] = (xt, yt)
            X.extend(xt)
            y.extend(yt)
    return X, y, per_ticker


def calibrate_from(X: list[dict], y: list[float]) -> dict:
    """
    Verilen (özellik, getiri) setinden ölçekleyici (mean/std) + fiyat-özellik IC
    ağırlıkları + tipik hareket üretir. SAFTIR: yalnız verilen X,y'yi kullanır —
    walk-forward CV bunu her fold'un SADECE train dilimiyle çağırır (sızıntısız).
    """
    scaler: dict[str, tuple[float, float]] = {}
    for f in features.FEATURES:
        col = [row.get(f, 0.0) for row in X]
        m = sum(col) / len(col) if col else 0.0
        if len(col) >= 2:
            var = sum((v - m) ** 2 for v in col) / (len(col) - 1)
            s = math.sqrt(var)
        else:
            s = 0.0
        scaler[f] = (m, s if s > 1e-9 else 1.0)  # sıfır varyans -> 1 (geçişli)

    # Fiyat özelliklerinin IC'si: standardize edilmiş özellik ile getiri korelasyonu.
    price_ic: dict[str, float] = {}
    for f in features.PRICE_FEATURES:
        m, s = scaler[f]
        z = [(row.get(f, 0.0) - m) / s for row in X]
        price_ic[f] = round(pearson(z, y), 4)

    typical_move = (sum(abs(v) for v in y) / len(y)) if y else 0.01

    return {
        "scaler": scaler,
        "price_ic": price_ic,
        "typical_move": typical_move,  # ortalama |getiri| — beklenen hareket ölçeği
        "n": len(X),
    }


def calibrate(conn, tickers, horizon: int, interval: str = PRICE_INTERVAL) -> dict:
    """
    Fiyat geçmişinden kalibrasyon (TÜM örnek üzerinde — canlı/production fit için).
    NOT: Bu fonksiyon tüm veriyi kullanır; ÖLÇÜM/raporlama için DEĞİL, canlı tahmin
    için modeli kurar. Dürüst örnek-dışı ölçüm için bkz. validation.cross_validate.
    """
    X, y, _ = _pool(conn, tickers, horizon, interval)
    out = calibrate_from(X, y)
    out.update({"horizon": horizon, "interval": interval})
    return out


def evaluate(forecaster, X: list[dict], y: list[float]) -> dict:
    """Bir model + (özellik, getiri) seti üzerinde isabet metriklerini hesaplar."""
    signals = [forecaster.signal_only(feat) for feat in X]
    n_dir = hits = 0
    up_rets: list[float] = []
    down_rets: list[float] = []
    for s, ret in zip(signals, y):
        if s >= NEUTRAL_BAND:
            up_rets.append(ret)
        elif s <= -NEUTRAL_BAND:
            down_rets.append(ret)
        else:
            continue  # nötr sinyal yön bahsine girmez
        if ret == 0:
            continue
        n_dir += 1
        if (s > 0) == (ret > 0):
            hits += 1
    return {
        "n": len(X),
        "n_directional": n_dir,
        "hit_rate": round(hits / n_dir, 4) if n_dir else None,
        "ic": round(pearson(signals, y), 4),
        "avg_up_return": round(sum(up_rets) / len(up_rets), 5) if up_rets else None,
        "avg_down_return": round(sum(down_rets) / len(down_rets), 5) if down_rets else None,
        "n_up": len(up_rets),
        "n_down": len(down_rets),
    }


def backtest_forecaster(conn, tickers, horizon: int, forecaster,
                        interval: str = PRICE_INTERVAL) -> dict:
    """Modeli geçmiş üzerinde değerlendirir: genel + ticker bazında metrikler."""
    X, y, per_ticker = _pool(conn, tickers, horizon, interval)
    overall = evaluate(forecaster, X, y) if X else {"n": 0, "hit_rate": None}
    per: dict[str, dict] = {}
    for t, (xt, yt) in per_ticker.items():
        per[t] = evaluate(forecaster, xt, yt)
    return {"overall": overall, "per_ticker": per, "horizon": horizon}
