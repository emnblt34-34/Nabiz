"""
Gün-içi Risk/Ödül Derecelendirme — RVOL & Risk-to-Reward Tier System.

DÜRÜSTLÜK (Stage 13): 30dk–1s YÖN ≈ yazı-tura (OOS-IC≈0, perm_p≈0.60). Bu modül YÖN
ÖNGÖRMEZ. Yaptığı, KULLANICININ kuralları:
  1) Zaman dilimi: 15dk (seviye+RVOL) + 1s (trend teyidi). Seviyeler gün-içi/1-3 gün.
  2) RVOL = anlık hacim / aynı saat-diliminin 20-gün ortalaması. RVOL<1.5 → ELE (raporlama).
  3) R:R = (Kâr-Al − Giriş) / (Giriş − Zarar-Kes).  Seviyeler ATR + swing'den (teknik).
  4) Tier: ≥3.0 🥇 | 2.0–2.9 🥈 | 1.5–1.9 🥉 | 1.0–1.4 🎗️ (RVOL yüksek ama stop derin).

UYARI: Yüksek R:R = yüksek KAZANMA olasılığı DEĞİL (genelde tersi — hedef uzak). Yön
öngörülmez; bu, tanımlı-riskli kurulumların hacim+geometri sıralamasıdır. Karar kullanıcının.
"""
from __future__ import annotations

from .. import db
from ..config import TICKER_MARKET

INTERVAL = "15m"          # seviye + RVOL
CONFIRM_INTERVAL = "60m"  # 1 saatlik trend teyidi
ATR_PERIOD = 14
RVOL_MIN = 1.5
RVOL_LOOKBACK = 20        # gün (aynı saat-dilimi)
SWING_LOW_BARS = 16       # ~4 saat (15dk bar)
RES_BARS = 48             # ~12 saat — direnç/destek penceresi


def _sma(xs: list[float], n: int) -> float | None:
    if len(xs) < n or n <= 0:
        return None
    return sum(xs[-n:]) / n


def _atr(highs, lows, closes, period=ATR_PERIOD) -> float | None:
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    if len(trs) < period:
        return None
    return sum(trs[-period:]) / period


def _rvol(rows) -> float | None:
    """Göreli hacim (kullanıcı kuralı 2): BUGÜN bu saat-dilimine kadar biriken hacim /
    son ~20 günün AYNI saate kadarki birikmiş hacim ortalaması. Kümülatif kullanmak
    yfinance'in son (kısmi) bar'ından kaynaklı yapay düşük RVOL'ü önler — standart RVOL tanımı."""
    if not rows:
        return None
    last_tod = rows[-1]["ts"][11:16]   # "HH:MM" (UTC) — şu anki gün-içi nokta
    last_date = rows[-1]["ts"][:10]
    by_date: dict[str, float] = {}
    order: list[str] = []
    for r in rows:
        if r["volume"] is None:
            continue
        d, tod = r["ts"][:10], r["ts"][11:16]
        if tod > last_tod:             # sadece günün AYNI saatine kadarı (adil kıyas)
            continue
        if d not in by_date:
            by_date[d] = 0.0
            order.append(d)
        by_date[d] += float(r["volume"])
    today = by_date.get(last_date)
    if today is None:
        return None
    prior = [by_date[d] for d in order if d != last_date][-RVOL_LOOKBACK:]
    if len(prior) < 5:                 # yeterli geçmiş gün yok
        return None
    avg = sum(prior) / len(prior)
    if avg <= 0:
        return None
    return today / avg


def _round(x: float) -> float:
    if x >= 100:
        return round(x, 2)
    if x >= 1:
        return round(x, 3)
    return round(x, 4)


def _tier(rr: float) -> int | None:
    if rr >= 3.0:
        return 1
    if rr >= 2.0:
        return 2
    if rr >= 1.5:
        return 3
    if rr >= 1.0:
        return 4
    return None


def _setup(conn, ticker: str) -> dict | None:
    rows = db.get_prices(conn, ticker, INTERVAL, limit=800)
    rows = [r for r in rows if r["close"] is not None and r["high"] is not None
            and r["low"] is not None]
    if len(rows) < max(ATR_PERIOD + 2, RES_BARS + 2):
        return None
    rvol = _rvol(rows)
    if rvol is None or rvol < RVOL_MIN:           # kural 2: RVOL<1.5 → ele
        return None

    highs = [float(r["high"]) for r in rows]
    lows = [float(r["low"]) for r in rows]
    closes = [float(r["close"]) for r in rows]
    atr = _atr(highs, lows, closes)
    if not atr or atr <= 0:
        return None
    entry = closes[-1]

    # Trend (1s teyidi) + 15dk yön → side
    crows = [r for r in db.get_prices(conn, ticker, CONFIRM_INTERVAL, limit=120)
             if r["close"] is not None]
    c1h = [float(r["close"]) for r in crows]
    sma1h = _sma(c1h, 20)
    trend_1h = ("up" if c1h[-1] > sma1h else "down") if (sma1h and c1h) else None
    sma15 = _sma(closes, 20)
    trend_15 = "up" if (sma15 and entry > sma15) else "down"
    side = trend_1h or trend_15
    confirm_1h = (trend_1h is not None and trend_1h == trend_15)

    if side == "up":
        swing_low = min(lows[-SWING_LOW_BARS:])
        stop = min(swing_low, entry - 1.5 * atr)
        risk = entry - stop
        resistance = max(highs[-RES_BARS:])
        if resistance > entry + 0.3 * atr:
            target, breakout = resistance, False
        else:                                      # tepe kırılımı → üstte direnç yok
            target, breakout = entry + 2.0 * risk, True
        reward = target - entry
    else:
        swing_high = max(highs[-SWING_LOW_BARS:])
        stop = max(swing_high, entry + 1.5 * atr)
        risk = stop - entry
        support = min(lows[-RES_BARS:])
        if support < entry - 0.3 * atr:
            target, breakout = support, False
        else:
            target, breakout = entry - 2.0 * risk, True
        reward = entry - target

    if risk <= 0 or reward <= 0:
        return None
    rr = reward / risk
    tier = _tier(rr)
    if tier is None:                               # R:R<1.0 → raporlama dışı
        return None
    return {
        "ticker": ticker, "market": TICKER_MARKET.get(ticker, "US"), "side": side,
        "rvol": round(rvol, 2), "entry": _round(entry), "stop": _round(stop),
        "target": _round(target), "rr": round(rr, 2), "tier": tier,
        "atr_pct": round(atr / entry * 100, 2), "breakout": breakout,
        "confirm_1h": confirm_1h, "asof": rows[-1]["ts"],
    }


def compute_tiers(conn, tickers) -> dict:
    """Tüm varlıkları tara → RVOL≥1.5 geçenleri R:R'a göre 4 Tier'e ayır (kural 4).
    Ayrıca RVOL liderlerini döner (boş-durumda 'en yakın adaylar' gösterimi için)."""
    tiers: dict[int, list] = {1: [], 2: [], 3: [], 4: []}
    scanned = 0
    rejected = 0
    leaders: list[dict] = []
    for t in tickers:
        scanned += 1
        rows = [r for r in db.get_prices(conn, t, INTERVAL, limit=800) if r["close"] is not None]
        rv = _rvol(rows) if rows else None
        if rv is not None:
            leaders.append({"ticker": t, "market": TICKER_MARKET.get(t, "US"), "rvol": round(rv, 2)})
        s = _setup(conn, t)
        if s is None:
            rejected += 1
            continue
        tiers[s["tier"]].append(s)
    for k in tiers:
        tiers[k].sort(key=lambda x: (-x["rr"], -x["rvol"]))
    leaders.sort(key=lambda x: -x["rvol"])
    return {
        "tiers": tiers,
        "scanned": scanned,
        "qualified": sum(len(v) for v in tiers.values()),
        "rejected_or_lowrr": rejected,
        "rvol_leaders": leaders[:6],
        "params": {"interval": INTERVAL, "confirm": CONFIRM_INTERVAL,
                   "rvol_min": RVOL_MIN, "atr_period": ATR_PERIOD},
    }
