"""
Depolama katmanı — SQLite (sıfır kurulum).

İki tablo:
  records      : işlenmiş tüm kayıtlar (ham metin + sentiment + kredibilite)
  scores       : ticker × pencere bazında toplanmış sentiment skorları (zaman serisi)

Deduplication: records.fingerprint üzerinde UNIQUE değil ama INSERT OR IGNORE
ile id (kaynak+url+parmak izi) tekilliği sağlanır; ayrıca pipeline içinde
fingerprint bazlı haber dedup'ı yapılır.

Postgres/Supabase'e geçiş: aynı şema, sqlite3 yerine psycopg/SQLAlchemy.
Zaman serisi büyürse records.created_at + scores için TimescaleDB hypertable.
"""
from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from .models import Record

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "finsent.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id           TEXT PRIMARY KEY,
    source       TEXT NOT NULL,
    source_type  TEXT NOT NULL,
    text         TEXT NOT NULL,
    url          TEXT,
    lang         TEXT,
    created_at   TEXT NOT NULL,
    author       TEXT NOT NULL,
    tickers      TEXT NOT NULL,
    credibility  REAL NOT NULL,
    sentiment    TEXT,
    sentiment_score REAL NOT NULL,
    engagement   INTEGER NOT NULL,
    fingerprint  TEXT NOT NULL,
    ingested_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_created ON records(created_at);
CREATE INDEX IF NOT EXISTS idx_records_fingerprint ON records(fingerprint);

CREATE TABLE IF NOT EXISTS scores (
    ticker       TEXT NOT NULL,
    window       TEXT NOT NULL,
    computed_at  TEXT NOT NULL,
    sentiment    REAL NOT NULL,   -- ağırlıklı net sentiment -1..+1
    volume       INTEGER NOT NULL,
    momentum     REAL NOT NULL,   -- önceki pencereye göre değişim
    pos_share    REAL NOT NULL,
    neg_share    REAL NOT NULL,
    PRIMARY KEY (ticker, window, computed_at)
);
CREATE INDEX IF NOT EXISTS idx_scores_ticker ON scores(ticker, window);

-- Fiyat barları (yfinance). Öngörü özellikleri ve backtest bunlardan beslenir.
CREATE TABLE IF NOT EXISTS prices (
    ticker    TEXT NOT NULL,
    ts        TEXT NOT NULL,      -- bar zamanı, UTC iso
    interval  TEXT NOT NULL,      -- "60m" vb.
    open  REAL, high REAL, low REAL, close REAL, volume REAL,
    PRIMARY KEY (ticker, ts, interval)
);
CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker, interval, ts);

-- Canlı tahmin günlüğü. Her tahmin kaydedilir; ufuk dolunca gerçek getiriyle
-- eşlenip "isabetli mi" işaretlenir. ASIL dürüstlük buradan gelir: modelin
-- sahadaki gerçek isabet oranı zamanla burada birikir.
CREATE TABLE IF NOT EXISTS predictions (
    id            TEXT PRIMARY KEY,   -- ticker|made_at hash
    ticker        TEXT NOT NULL,
    made_at       TEXT NOT NULL,      -- tahmin anı, UTC iso
    horizon_bars  INTEGER NOT NULL,
    target_ts     TEXT NOT NULL,      -- olgunlaşma anı (yaklaşık), UTC iso
    model         TEXT NOT NULL,      -- rule / ml / blend
    signal        REAL NOT NULL,      -- -1..+1
    direction     TEXT NOT NULL,      -- up / down / neutral
    confidence    REAL NOT NULL,      -- 0..1
    expected_move REAL,               -- beklenen % hareket
    price_at      REAL NOT NULL,      -- tahmin anındaki fiyat
    features      TEXT NOT NULL,      -- json
    realized_return REAL,             -- olgunlaşınca doldurulur (%)
    realized_dir  TEXT,               -- gerçekleşen yön
    correct       INTEGER,            -- 1/0 (yön tuttu mu)
    resolved_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_pred_ticker ON predictions(ticker, made_at);
CREATE INDEX IF NOT EXISTS idx_pred_open ON predictions(realized_return);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # timeout + WAL: arka plan toplayıcı yazarken arayüz okumaları kilitlenmesin
    conn = sqlite3.connect(db_path, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=15000")
    conn.executescript(_SCHEMA)
    return conn


def insert_records(conn: sqlite3.Connection, records: list[Record]) -> int:
    """Kayıtları ekler. id çakışırsa yok sayar (dedup). Eklenen sayıyı döner."""
    inserted = 0
    now = datetime.now(timezone.utc).isoformat()
    for r in records:
        row = r.to_row()
        cur = conn.execute(
            """INSERT OR IGNORE INTO records
               (id, source, source_type, text, url, lang, created_at, author,
                tickers, credibility, sentiment, sentiment_score, engagement,
                fingerprint, ingested_at)
               VALUES (:id,:source,:source_type,:text,:url,:lang,:created_at,
                :author,:tickers,:credibility,:sentiment,:sentiment_score,
                :engagement,:fingerprint,:ingested_at)""",
            {**row, "ingested_at": now},
        )
        inserted += cur.rowcount
    conn.commit()
    return inserted


def fetch_records_since(conn: sqlite3.Connection, since_iso: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM records WHERE created_at >= ? ORDER BY created_at",
        (since_iso,),
    ).fetchall()


def upsert_score(conn: sqlite3.Connection, **kw) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO scores
           (ticker, window, computed_at, sentiment, volume, momentum,
            pos_share, neg_share)
           VALUES (:ticker,:window,:computed_at,:sentiment,:volume,:momentum,
            :pos_share,:neg_share)""",
        kw,
    )
    conn.commit()


def latest_scores(conn: sqlite3.Connection, window: str = "24h") -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT s.* FROM scores s
           JOIN (SELECT ticker, MAX(computed_at) mx FROM scores
                 WHERE window=? GROUP BY ticker) t
           ON s.ticker=t.ticker AND s.computed_at=t.mx AND s.window=?
           ORDER BY s.sentiment DESC""",
        (window, window),
    ).fetchall()


# ---------------------------------------------------------------------------
# Fiyat barları
# ---------------------------------------------------------------------------
def upsert_prices(conn: sqlite3.Connection, ticker: str, interval: str,
                  bars: list[tuple]) -> int:
    """bars = [(ts_iso, open, high, low, close, volume), ...]. Eklenen/güncel sayısı."""
    n = 0
    for ts, o, h, l, c, v in bars:
        conn.execute(
            """INSERT OR REPLACE INTO prices
               (ticker, ts, interval, open, high, low, close, volume)
               VALUES (?,?,?,?,?,?,?,?)""",
            (ticker, ts, interval, o, h, l, c, v),
        )
        n += 1
    conn.commit()
    return n


def get_prices(conn: sqlite3.Connection, ticker: str, interval: str,
               limit: int | None = None) -> list[sqlite3.Row]:
    """Bir ticker'ın barlarını zaman sırasıyla (eskiden yeniye) döner."""
    sql = "SELECT * FROM prices WHERE ticker=? AND interval=? ORDER BY ts"
    if limit:
        # son `limit` barı al, sonra tekrar kronolojik sırala
        rows = conn.execute(
            "SELECT * FROM prices WHERE ticker=? AND interval=? ORDER BY ts DESC LIMIT ?",
            (ticker, interval, limit),
        ).fetchall()
        return list(reversed(rows))
    return conn.execute(sql, (ticker, interval)).fetchall()


def latest_price(conn: sqlite3.Connection, ticker: str, interval: str) -> float | None:
    row = conn.execute(
        "SELECT close FROM prices WHERE ticker=? AND interval=? ORDER BY ts DESC LIMIT 1",
        (ticker, interval),
    ).fetchone()
    return float(row["close"]) if row and row["close"] is not None else None


# ---------------------------------------------------------------------------
# Tahmin günlüğü
# ---------------------------------------------------------------------------
def insert_prediction(conn: sqlite3.Connection, **kw) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO predictions
           (id, ticker, made_at, horizon_bars, target_ts, model, signal,
            direction, confidence, expected_move, price_at, features)
           VALUES (:id,:ticker,:made_at,:horizon_bars,:target_ts,:model,:signal,
            :direction,:confidence,:expected_move,:price_at,:features)""",
        kw,
    )
    conn.commit()


def open_predictions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Henüz sonuçlanmamış (olgunlaşmayı bekleyen) tahminler."""
    return conn.execute(
        "SELECT * FROM predictions WHERE realized_return IS NULL ORDER BY target_ts"
    ).fetchall()


def resolve_prediction(conn: sqlite3.Connection, pred_id: str, realized_return: float,
                       realized_dir: str, correct: int, resolved_at: str) -> None:
    conn.execute(
        """UPDATE predictions
           SET realized_return=?, realized_dir=?, correct=?, resolved_at=?
           WHERE id=?""",
        (realized_return, realized_dir, correct, resolved_at, pred_id),
    )
    conn.commit()


def prediction_stats(conn: sqlite3.Connection, ticker: str | None = None) -> dict:
    """Sonuçlanmış tahminlerin canlı isabet özeti (yön belirsizler hariç)."""
    where = "WHERE correct IS NOT NULL AND direction != 'neutral'"
    args: tuple = ()
    if ticker:
        where += " AND ticker=?"
        args = (ticker,)
    row = conn.execute(
        f"""SELECT COUNT(*) n, SUM(correct) hits, AVG(realized_return) avg_ret
            FROM predictions {where}""",
        args,
    ).fetchone()
    n = row["n"] or 0
    hits = row["hits"] or 0
    return {
        "resolved": n,
        "hits": int(hits),
        "hit_rate": round(hits / n, 4) if n else None,
        "avg_realized_return": round(row["avg_ret"], 4) if row["avg_ret"] is not None else None,
        "open": conn.execute(
            "SELECT COUNT(*) c FROM predictions WHERE realized_return IS NULL"
            + (" AND ticker=?" if ticker else ""),
            (ticker,) if ticker else (),
        ).fetchone()["c"],
    }
