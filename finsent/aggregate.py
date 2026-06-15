"""
Toplama ve skorlama katmanı.

Ham sentiment yeterli değil. Bir ticker için pencere (1h/24h/7d) bazında
AĞIRLIKLI net sentiment üretir. Ağırlık üç çarpanın çarpımı:

    ağırlık = kredibilite × kaynak_güveni × log(1 + etkileşim)

  - kredibilite: bot/şüpheli hesap sentiment'i az etkiler (credibility.py)
  - kaynak_güveni: KAP > haber > forum (config.SOURCE_TRUST / SOURCE_TYPE_WEIGHT)
  - etkileşim: 1000 beğenili yorum, 2 beğenili yorumdan ağır (log ile yumuşatılmış)

Momentum: bu pencere skoru ile bir önceki hesaplanan skor farkı. Genelde
sentiment'in YÖNÜ, seviyesinden daha güçlü bir sinyaldir.
"""
from __future__ import annotations

import math
import json
from datetime import datetime, timedelta, timezone
from .config import SOURCE_TRUST, SOURCE_TYPE_WEIGHT, WINDOWS
from . import db


def _record_weight(row) -> float:
    cred = row["credibility"]
    src_trust = SOURCE_TRUST.get(row["source"], 0.8)
    type_w = SOURCE_TYPE_WEIGHT.get(row["source_type"], 0.6)
    eng_w = math.log1p(max(row["engagement"], 0))
    # eng_w 0 olabilir (0 etkileşim); taban 1 ekleyerek kaybetme.
    return cred * src_trust * type_w * (1.0 + eng_w)


def aggregate_window(conn, ticker: str, window: str, now: datetime | None = None) -> dict | None:
    """
    Verilen ticker + pencere için ağırlıklı sentiment hesaplar.
    Kayıt yoksa None döner.
    """
    now = now or datetime.now(timezone.utc)
    hours = WINDOWS[window]
    since = (now - timedelta(hours=hours)).isoformat()

    rows = conn.execute(
        "SELECT * FROM records WHERE created_at >= ? AND created_at <= ?",
        (since, now.isoformat()),
    ).fetchall()

    # Bu ticker'ı içeren kayıtları süz.
    rel = [r for r in rows if ticker in json.loads(r["tickers"])]
    if not rel:
        return None

    num = den = 0.0
    pos = neg = 0
    for r in rel:
        w = _record_weight(r)
        num += w * r["sentiment_score"]
        den += w
        if r["sentiment"] == "positive":
            pos += 1
        elif r["sentiment"] == "negative":
            neg += 1

    sentiment = num / den if den else 0.0
    volume = len(rel)
    total_dir = pos + neg

    # Momentum: en son kaydedilmiş aynı-pencere skoruna göre değişim.
    prev = conn.execute(
        "SELECT sentiment FROM scores WHERE ticker=? AND window=? ORDER BY computed_at DESC LIMIT 1",
        (ticker, window),
    ).fetchone()
    momentum = sentiment - prev["sentiment"] if prev else 0.0

    return {
        "ticker": ticker,
        "window": window,
        "computed_at": now.isoformat(),
        "sentiment": round(sentiment, 4),
        "volume": volume,
        "momentum": round(momentum, 4),
        "pos_share": round(pos / total_dir, 4) if total_dir else 0.0,
        "neg_share": round(neg / total_dir, 4) if total_dir else 0.0,
    }


def aggregate_all(conn, tickers: list[str], windows: list[str] | None = None,
                  now: datetime | None = None) -> list[dict]:
    """Tüm ticker × pencere kombinasyonlarını hesaplar ve DB'ye yazar."""
    windows = windows or ["1h", "24h", "7d"]
    results = []
    for t in tickers:
        for w in windows:
            score = aggregate_window(conn, t, w, now=now)
            if score:
                db.upsert_score(conn, **score)
                results.append(score)
    return results
