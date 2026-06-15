"""
Servis katmanı — FastAPI.

Pipeline'ın ürettiği skorları ve ham kayıtları HTTP üzerinden sunar.
Dashboard / mobil uygulama bu uçları tüketir.

Çalıştır:  uvicorn finsent.api:app --reload
Bağımlılık: fastapi, uvicorn
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Query
from . import db
from .config import WINDOWS

app = FastAPI(title="finsent", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/scores")
def scores(window: str = Query("24h", enum=list(WINDOWS.keys()))):
    """Tüm ticker'lar için en güncel skorlar, sentiment'e göre sıralı."""
    conn = db.connect()
    rows = db.latest_scores(conn, window=window)
    conn.close()
    return [dict(r) for r in rows]


@app.get("/ticker/{symbol}")
def ticker_detail(symbol: str, window: str = "24h", limit: int = 20):
    """Bir ticker için güncel skor + en son örnek kayıtlar (kanıt)."""
    symbol = symbol.upper()
    conn = db.connect()
    score = conn.execute(
        "SELECT * FROM scores WHERE ticker=? AND window=? ORDER BY computed_at DESC LIMIT 1",
        (symbol, window),
    ).fetchone()

    rows = conn.execute(
        "SELECT * FROM records ORDER BY created_at DESC LIMIT 500"
    ).fetchall()
    samples = []
    for r in rows:
        if symbol in json.loads(r["tickers"]):
            samples.append({
                "text": r["text"], "source": r["source"],
                "sentiment": r["sentiment"], "score": r["sentiment_score"],
                "credibility": r["credibility"], "url": r["url"],
                "created_at": r["created_at"],
            })
        if len(samples) >= limit:
            break
    conn.close()
    return {
        "ticker": symbol,
        "score": dict(score) if score else None,
        "samples": samples,
    }


@app.get("/timeseries/{symbol}")
def timeseries(symbol: str, window: str = "24h"):
    """Bir ticker'ın sentiment zaman serisi — grafik için."""
    conn = db.connect()
    rows = conn.execute(
        "SELECT computed_at, sentiment, volume, momentum FROM scores "
        "WHERE ticker=? AND window=? ORDER BY computed_at",
        (symbol.upper(), window),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
