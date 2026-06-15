"""
Özellik (feature) üretimi — öngörü modelinin girdileri.

İki grup özellik:
  FİYAT  : kısa vadeli getiri, volatilite, ortalamaya uzaklık, RSI — saatlik
           barlardan türetilir. Geçmişle backtest EDİLEBİLİR (fiyat tarihi var).
  DUYGU  : ağırlıklı sentiment, momentum, pos/neg dengesi, hacim — scores
           tablosundan. Geçmiş duygu verisi olmadığı için bunların katkısı
           CANLI tahmin günlüğünde ölçülür (bkz. SENT_PRIORS).

Kritik kural: özellik hesabında GELECEĞE bakma yok. i. bar için yalnızca
closes[:i+1] kullanılır; etiket (forward return) ayrı tutulur.
"""
from __future__ import annotations

import math

PRICE_FEATURES = ["ret1", "ret3", "ret6", "vol", "sma_dist", "rsi"]
SENT_FEATURES = ["sent", "mom", "posneg", "logvol"]
FEATURES = PRICE_FEATURES + SENT_FEATURES

# Özellik hesabı için gereken minimum geçmiş bar sayısı (ret6/vol/rsi 6 bar ister).
MIN_BARS = 7


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _returns(closes: list[float]) -> list[float]:
    out = []
    for i in range(1, len(closes)):
        p = closes[i - 1]
        out.append((closes[i] - p) / p if p else 0.0)
    return out


def _rsi(closes: list[float], period: int = 6) -> float:
    """0..100 RSI -> -1..+1'e ölçeklenmiş döner (0=aşırı satım, 0=nötr civarı)."""
    if len(closes) <= period:
        return 0.0
    rets = _returns(closes[-(period + 1):])
    gains = [r for r in rets if r > 0]
    losses = [-r for r in rets if r < 0]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        rsi = 100.0 if avg_gain > 0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - 100 / (1 + rs)
    return (rsi - 50) / 50  # -1..+1 (50 nötr)


def price_features(closes: list[float], i: int) -> dict | None:
    """
    closes[i] barı için fiyat özellikleri (yalnızca geçmişe bakarak).
    Yeterli geçmiş yoksa None.
    """
    if i < MIN_BARS - 1:
        return None
    c = closes
    def ret(n):
        base = c[i - n]
        return (c[i] - base) / base if base else 0.0
    win6 = c[i - 5:i + 1]
    sma6 = _mean(win6)
    return {
        "ret1": ret(1),
        "ret3": ret(3),
        "ret6": ret(6),
        "vol": _std(_returns(c[i - 6:i + 1])),
        "sma_dist": (c[i] - sma6) / sma6 if sma6 else 0.0,
        "rsi": _rsi(c[:i + 1]),
    }


def sentiment_features(score_row) -> dict:
    """scores tablosundan bir satır -> duygu özellikleri. None ise hepsi 0."""
    if not score_row:
        return {k: 0.0 for k in SENT_FEATURES}
    sent = float(score_row["sentiment"])
    mom = float(score_row["momentum"])
    pos = float(score_row["pos_share"])
    neg = float(score_row["neg_share"])
    vol = float(score_row["volume"])
    return {
        "sent": sent,
        "mom": mom,
        "posneg": pos - neg,
        "logvol": math.log1p(max(vol, 0)) / 5.0,  # ~0..1 bandına çek
    }


def forward_return(closes: list[float], i: int, horizon: int) -> float | None:
    """closes[i]'den `horizon` bar sonrasına getiri (etiket). Veri yetmezse None."""
    j = i + horizon
    if j >= len(closes):
        return None
    base = closes[i]
    return (closes[j] - base) / base if base else None


def to_vector(feat: dict) -> list[float]:
    """Özellik dict'ini FEATURES sırasına göre listeye çevirir (eksik -> 0)."""
    return [float(feat.get(k, 0.0)) for k in FEATURES]


def build_price_dataset(closes: list[float], horizon: int) -> tuple[list[dict], list[float]]:
    """
    Fiyat geçmişinden (özellik, forward_return) eğitim/backtest seti üretir.
    Duygu özellikleri 0'dır (geçmiş duygu verisi yok) — bu yüzden backtest
    fiyat-bileşeninin GERÇEK isabetini ölçer, duygu katkısı canlı doğrulanır.
    """
    X: list[dict] = []
    y: list[float] = []
    for i in range(MIN_BARS - 1, len(closes)):
        pf = price_features(closes, i)
        if pf is None:
            continue
        fr = forward_return(closes, i, horizon)
        if fr is None:
            continue
        feat = {**pf, **{k: 0.0 for k in SENT_FEATURES}}
        X.append(feat)
        y.append(fr)
    return X, y
