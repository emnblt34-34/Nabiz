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

from .signals import regime

BASE_PRICE_FEATURES = ["ret1", "ret3", "ret6", "vol", "sma_dist", "rsi"]

# Çok-ölçekli momentum ailesi (Stage 2) — araştırmanın "gerçek kanıt bölgesi".
# Geriye-bakış BAR cinsindendir: GÜNLÜK bar'da [21,63,126,252] ≈ 1/3/6/12 ay
# (zaman-serisi momentumun en güçlü kanıt aralığı). Her ölçek için:
#   mom_n   = ham n-bar getirisi (işaretiyle yön)
#   momsc_n = vol-ölçekli (getiri / (bar-vol·√n)) — Kim-Tse-Wald vol-artefaktını
#             ham momentumdan AYIRMAK için ayrı tutulur.
# Yeterli geçmiş yoksa 0 döner (no-look-ahead korunur; MIN_BARS'ı şişirmez).
MOMENTUM_LOOKBACKS = [21, 63, 126, 252]
MOMENTUM_FEATURES = ([f"mom_{n}" for n in MOMENTUM_LOOKBACKS]
                     + [f"momsc_{n}" for n in MOMENTUM_LOOKBACKS])

# Rejim koşullama (Stage 3) — SİNYAL DEĞİL: rejim göstergeleri (er, hurst) + momentumu
# trend-gücüyle çarpan etkileşimler (mom*_reg). Trendli rejimde momentum, choppy'de
# reversal. Pre-registered + MİNİMAL (çoklu-test/n_trials şişmesin diye 4 ile sınırlı).
REGIME_FEATURES = ["er", "hurst", "mom63_reg", "mom252_reg"]

# Hacim-olay ailesi (Stage 7) — haber-etki kanalının BACKTEST EDİLEBİLİR proxy'si.
# Gerçek duygu/haber geçmişi yok; ama HACİM SPIKE'I dikkat/haber proxy'sidir. Olay-sonrası
# drift (post-news drift) gerçekse bu özellikler edge taşır. closes+volumes ister; _records
# ve rank_now merge eder (price_features'a dokunmaz). Yeterli geçmiş yoksa 0.
VOLUME_FEATURES = ["vol_spike", "vol_trend", "event_ret"]

PRICE_FEATURES = BASE_PRICE_FEATURES + MOMENTUM_FEATURES + REGIME_FEATURES + VOLUME_FEATURES
SENT_FEATURES = ["sent", "mom", "posneg", "logvol"]
FEATURES = PRICE_FEATURES + SENT_FEATURES

# Taban özellikler için gereken minimum geçmiş (ret6/vol/rsi 6 bar). Momentum kendi
# geçmişini ayrıca ister; yoksa 0 olur — bu yüzden MIN_BARS küçük kalır.
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
    feat = {
        "ret1": ret(1),
        "ret3": ret(3),
        "ret6": ret(6),
        "vol": _std(_returns(c[i - 6:i + 1])),
        "sma_dist": (c[i] - sma6) / sma6 if sma6 else 0.0,
        "rsi": _rsi(c[:i + 1]),
    }
    feat.update(momentum_features(closes, i))
    feat.update(_regime_features(closes, i, feat))
    return feat


def _regime_features(closes: list[float], i: int, feat: dict) -> dict:
    """Rejim göstergeleri + TREND-GEÇİTLİ momentum (Stage 3 koşullama).
    ts ∈ [-1,1]: >0 trend (momentum açılır), <0 choppy (reversal). mom*_reg = mom · ts."""
    ts = regime.trend_score(closes, i, 63)
    return {
        "er": (ts + 1.0) / 2.0,
        "hurst": regime.hurst(closes, i, 100),
        "mom63_reg": feat.get("mom_63", 0.0) * ts,
        "mom252_reg": feat.get("mom_252", 0.0) * ts,
    }


def momentum_features(closes: list[float], i: int) -> dict:
    """Çok-ölçekli momentum (ham + vol-ölçekli). Yeterli geçmiş yoksa o ölçek 0."""
    out: dict[str, float] = {}
    for n in MOMENTUM_LOOKBACKS:
        base = closes[i - n] if i >= n else 0.0
        if i >= n and base:
            r = (closes[i] - base) / base
            rr = _returns(closes[i - n:i + 1])
            sd = _std(rr)
            sc = r / (sd * math.sqrt(n)) if sd else 0.0
        else:
            r = sc = 0.0
        out[f"mom_{n}"] = r
        out[f"momsc_{n}"] = sc
    return out


def volume_features(closes: list[float], volumes: list[float], i: int, lookback: int = 20) -> dict:
    """
    Hacim-olay özellikleri (haber-etki kanalı proxy'si). HACİM SPIKE'I = dikkat/haber.
    closes + volumes ister; yeterli geçmiş/hacim yoksa hepsi 0. No-look-ahead.
    """
    zero = {"vol_spike": 0.0, "vol_trend": 0.0, "event_ret": 0.0}
    if i < lookback or not volumes or len(volumes) <= i:
        return zero
    win = [v for v in volumes[i - lookback + 1:i + 1] if v]
    avg = _mean(win)
    if avg <= 0 or not volumes[i]:
        return zero
    avg5 = _mean([v for v in volumes[i - 4:i + 1] if v]) if i >= 4 else avg
    spike = min(volumes[i] / avg, 6.0)              # bugünkü hacim / 20-bar ort (capped)
    trend = min(avg5 / avg, 4.0) if avg else 1.0    # son 5 / 20 hacim eğilimi
    ret5 = (closes[i] - closes[i - 5]) / closes[i - 5] if i >= 5 and closes[i - 5] else 0.0
    return {
        "vol_spike": spike - 1.0,                   # 0 merkezli (dikkat artışı)
        "vol_trend": trend - 1.0,
        "event_ret": ret5 * (spike - 1.0),          # hacimle ağırlıklı son hareket (olay-drift)
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
