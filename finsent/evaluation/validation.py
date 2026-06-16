"""
Bilimsel doğrulama — purged + embargoed walk-forward CV (Stage 0).

NEDEN: Mevcut backtest.backtest_forecaster modeli TÜM örnekte fit edip AYNI örnekte
ölçüyordu → in-sample iyimserlik (sızıntı). Bu modül modeli her fold'un SADECE
TRAIN dilimiyle (zaman-önce) fit eder, sonraki test diliminde ölçer; train↔test
arasında ETİKET UFKU kadar PURGE + EMBARGO boşluğu bırakır (örtüşen forward-return
etiketlerinin sızıntısını keser). Dönen metrikler DÜRÜST örnek-dışıdır (OOS).

Referans: López de Prado, "Advances in Financial Machine Learning" (purged k-fold,
embargo, walk-forward).
"""
from __future__ import annotations

from .. import prices, features, forecast
from . import backtest
from ..config import PRICE_INTERVAL, HORIZON_BARS, NEUTRAL_BAND


def walk_forward_folds(n: int, n_splits: int = 5, horizon: int = HORIZON_BARS,
                       embargo: int = 1, min_train: int = 60) -> list[tuple[list[int], list[int]]]:
    """
    Genişleyen-pencere (expanding) walk-forward fold'ları üretir.
    Her fold: train = [0, t0 - gap), test = [t0, t1). gap = horizon + embargo —
    bu boşluk, train'in son örneklerinin forward-return etiketinin test penceresine
    SARKMASINI (sızıntı) engeller. Train her zaman test'ten ÖNCEDİR (gelecek görmez).
    """
    folds: list[tuple[list[int], list[int]]] = []
    if n <= min_train + 10:
        return folds
    usable = n - min_train
    # küçük örnekte split sayısını otomatik düşür
    n_splits = max(1, min(n_splits, usable // 8))
    test_size = max(5, usable // n_splits)
    gap = horizon + embargo
    t0 = min_train
    k = 0
    while t0 + 3 <= n and k < n_splits:
        t1 = min(t0 + test_size, n)
        train_end = t0 - gap
        if train_end >= max(min_train // 2, 10) and (t1 - t0) >= 3:
            folds.append((list(range(0, train_end)), list(range(t0, t1))))
        t0 = t1
        k += 1
    return folds


def _metrics(signals: list[float], labels: list[float]) -> dict:
    """Sinyal+getiri setinden yön isabeti, IC ve up/down ortalama getirisi."""
    n_dir = hits = 0
    up: list[float] = []
    down: list[float] = []
    for s, ret in zip(signals, labels):
        if s >= NEUTRAL_BAND:
            up.append(ret)
        elif s <= -NEUTRAL_BAND:
            down.append(ret)
        else:
            continue
        if ret == 0:
            continue
        n_dir += 1
        if (s > 0) == (ret > 0):
            hits += 1
    return {
        "n": len(signals),
        "n_directional": n_dir,
        "hit_rate": round(hits / n_dir, 4) if n_dir else None,
        "ic": round(backtest.pearson(signals, labels), 4) if len(signals) >= 3 else None,
        "avg_up_return": round(sum(up) / len(up), 5) if up else None,
        "avg_down_return": round(sum(down) / len(down), 5) if down else None,
        "n_up": len(up), "n_down": len(down),
    }


def cross_validate(conn, tickers, horizon: int = HORIZON_BARS, prefer_ml: bool = True,
                   n_splits: int = 5, embargo: int = 1,
                   interval: str = PRICE_INTERVAL) -> dict:
    """
    Purged+embargoed walk-forward CV. Her ticker'da modeli SADECE train-fold'da
    fit eder (forecast.fit_from_data), test-fold'da sinyal üretir. Test sinyallerini
    tüm fold/ticker boyunca biriktirip DÜRÜST OOS metrik döner.
    """
    oos_sig: list[float] = []
    oos_lab: list[float] = []
    per_ticker: dict[str, dict] = {}
    n_folds_total = 0
    skipped: list[str] = []

    for t in tickers:
        c = prices.closes(conn, t, interval)
        if len(c) < features.MIN_BARS + horizon + 20:
            skipped.append(t)
            continue
        X, y = features.build_price_dataset(c, horizon)
        folds = walk_forward_folds(len(X), n_splits=n_splits, horizon=horizon, embargo=embargo)
        if not folds:
            skipped.append(t)
            continue
        tsig: list[float] = []
        tlab: list[float] = []
        for train_idx, test_idx in folds:
            Xtr = [X[i] for i in train_idx]
            ytr = [y[i] for i in train_idx]
            fc, _ = forecast.fit_from_data(Xtr, ytr, prefer_ml)   # SADECE train dilimi
            for i in test_idx:
                tsig.append(fc.signal_only(X[i]))
                tlab.append(y[i])
        if tsig:
            m = _metrics(tsig, tlab)
            m["folds"] = len(folds)
            per_ticker[t] = m
            n_folds_total += len(folds)
            oos_sig.extend(tsig)
            oos_lab.extend(tlab)

    overall = _metrics(oos_sig, oos_lab) if oos_sig else {"n": 0, "hit_rate": None, "ic": None}
    return {
        "method": "purged+embargoed walk-forward",
        "overall": overall,
        "per_ticker": per_ticker,
        "oos_signals": oos_sig,
        "oos_labels": oos_lab,
        "n_folds_total": n_folds_total,
        "skipped": skipped,
        "horizon": horizon,
        "embargo": embargo,
    }
