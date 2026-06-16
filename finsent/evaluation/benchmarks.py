"""
Null modeller & temel çizgiler (Stage 0) — "edge gerçek mi?" kararının zemini.

Bir sinyalin OOS hit-rate/IC'si tek başına bir şey söylemez; YENMESİ GEREKEN
null'lara karşı kıyaslanmalı:
  - base_rate / buy_and_hold : yön bahsinin trivial tabanı (pozitif-getiri oranı).
  - random_sign              : saf şans (yön tahmini bilgisizse buraya yakınsar).
  - persistence              : naif "son hareket devam eder" (momentum-0).
  - permutation_pvalue       : sinyal–getiri ilişkisi martingale-null altında
                               şans eseri mi? (etiket karıştırma → IC null dağılımı).

Stage 1'de eklenecek: blok-bootstrap (zaman yapısını koruyan), Deflated Sharpe,
PBO, White Reality Check / SPA, FDR.
"""
from __future__ import annotations

import random

from . import backtest
from ..config import NEUTRAL_BAND


def _dir_metrics(signals: list[float], labels: list[float]) -> dict:
    n_dir = hits = 0
    for s, ret in zip(signals, labels):
        if abs(s) < NEUTRAL_BAND or ret == 0:
            continue
        n_dir += 1
        if (s > 0) == (ret > 0):
            hits += 1
    return {
        "hit_rate": round(hits / n_dir, 4) if n_dir else None,
        "n_directional": n_dir,
        "ic": round(backtest.pearson(signals, labels), 4) if len(signals) >= 3 else None,
    }


def base_rate(labels: list[float]) -> float | None:
    """Pozitif getiri oranı — sınıf dengesizliği / 'hep yukarı' tahmininin isabeti."""
    pos = sum(1 for r in labels if r > 0)
    n = sum(1 for r in labels if r != 0)
    return round(pos / n, 4) if n else None


def buy_and_hold(labels: list[float]) -> dict:
    """Her zaman 'yukarı' (long). Yön isabeti = pozitif-getiri oranı."""
    return _dir_metrics([1.0] * len(labels), labels)


def random_sign(labels: list[float], seed: int = 7, reps: int = 25) -> dict:
    """Rastgele ±1 sinyal — şans tabanı. reps tekrar ortalaması (deterministik seed)."""
    rng = random.Random(seed)
    hits: list[float] = []
    ics: list[float] = []
    for _ in range(reps):
        sig = [rng.choice((-1.0, 1.0)) for _ in labels]
        m = _dir_metrics(sig, labels)
        if m["hit_rate"] is not None:
            hits.append(m["hit_rate"])
        if m["ic"] is not None:
            ics.append(m["ic"])
    return {
        "hit_rate": round(sum(hits) / len(hits), 4) if hits else None,
        "ic": round(sum(ics) / len(ics), 4) if ics else None,
        "reps": reps,
    }


def persistence(features_list: list[dict], labels: list[float]) -> dict:
    """Naif kalıcılık: son bar getirisinin (ret1) işareti = tahmin."""
    sig = [1.0 if f.get("ret1", 0.0) > 0 else -1.0 for f in features_list]
    return _dir_metrics(sig, labels)


def permutation_pvalue(signals: list[float], labels: list[float],
                       n_perm: int = 1000, seed: int = 13) -> dict:
    """
    Martingale/random-walk null testi: etiketleri karıştırıp IC'nin null dağılımını
    kur. Tek-yönlü p = (perm_IC >= gerçek_IC sayısı + 1) / (n_perm + 1).
    Küçük p → sinyal–getiri ilişkisi ŞANSTAN farklı (zayıf da olsa gerçek).
    NOT (Stage 0 kısıtı): iid karıştırma; otokorelasyonu yok sayar. Stage 1'de
    blok-bootstrap ile değiştirilecek.
    """
    if len(signals) < 10:
        return {"actual_ic": None, "p_value": None, "n_perm": 0}
    actual = backtest.pearson(signals, labels)
    rng = random.Random(seed)
    lab = list(labels)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(lab)
        if backtest.pearson(signals, lab) >= actual:
            ge += 1
    return {
        "actual_ic": round(actual, 4),
        "p_value": round((ge + 1) / (n_perm + 1), 4),
        "n_perm": n_perm,
        "one_sided": "P(perm_IC >= actual_IC)",
    }
