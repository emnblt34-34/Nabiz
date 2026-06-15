"""
Fiyat katmanı — gerçek piyasa verisi (yfinance, ücretsiz).

Öngörü "gerçek" olsun diye fiyat lazım: hem özelliklerin bir kısmı (kısa vadeli
trend/volatilite) buradan gelir, hem de modelin isabeti GERÇEK fiyat hareketiyle
backtest edilir. Aksi halde "öngörü" doğrulanamayan bir sayı olur.

  - US sembolleri eksiz çekilir (AAPL), BIST sembolleri ".IS" ekiyle (THYAO.IS).
  - Barlar SQLite'a (prices tablosu) cache'lenir; arayüz/backtest oradan okur.
  - yfinance kurulu değilse ya da bir sembol düşerse: sessizce boş döner,
    sistemin geri kalanı (duygu paneli) çalışmaya devam eder.

Not: yfinance'in kendi tz-cache'i eşzamanlı erişimde "database is locked"
verebiliyor; bu yüzden sembolleri TEK TEK (sıralı) çekiyoruz.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import db
from .config import yf_symbol, PRICE_INTERVAL, PRICE_PERIOD_LIVE


def _yf():
    """yfinance'i tembel import eder. Kurulu değilse None döner (zarif fallback)."""
    try:
        import yfinance as yf  # noqa: WPS433
        return yf
    except Exception as e:  # pragma: no cover
        print(f"[prices] yfinance yok ({e}); fiyat/öngörü katmanı pasif.")
        return None


def _to_utc_iso(ts) -> str:
    """pandas Timestamp -> UTC iso string. tz yoksa UTC varsay."""
    py = ts.to_pydatetime()
    if py.tzinfo is None:
        py = py.replace(tzinfo=timezone.utc)
    return py.astimezone(timezone.utc).isoformat()


def fetch_bars(ticker: str, period: str = PRICE_PERIOD_LIVE,
               interval: str = PRICE_INTERVAL) -> list[tuple]:
    """
    Tek sembol için OHLCV barları çeker.
    Dönüş: [(ts_iso, open, high, low, close, volume), ...] (kronolojik).
    Hata/boş veride [] döner — çağıran taraf bunu tolere eder.
    """
    yf = _yf()
    if yf is None:
        return []
    sym = yf_symbol(ticker)
    for attempt in range(2):  # tz-cache kilidi geçiciyse bir kez daha dene
        try:
            df = yf.Ticker(sym).history(period=period, interval=interval, auto_adjust=True)
            if df is None or df.empty:
                return []
            out: list[tuple] = []
            for ts, row in df.iterrows():
                close = row.get("Close")
                if close is None or close != close:  # NaN ele
                    continue
                out.append((
                    _to_utc_iso(ts),
                    _f(row.get("Open")), _f(row.get("High")), _f(row.get("Low")),
                    _f(close), _f(row.get("Volume")),
                ))
            return out
        except Exception as e:  # pragma: no cover
            if attempt == 0:
                continue
            print(f"[prices] {sym} çekilemedi: {e}")
            return []
    return []


def _f(x) -> float | None:
    try:
        v = float(x)
        return v if v == v else None  # NaN -> None
    except Exception:
        return None


def update_prices(conn, tickers, period: str = PRICE_PERIOD_LIVE,
                  interval: str = PRICE_INTERVAL) -> dict:
    """
    Verilen tickerlar için barları çekip cache'e yazar (sıralı — kilit riski yok).
    Dönüş: {ticker: yazılan_bar_sayısı}.
    """
    stats: dict[str, int] = {}
    for t in tickers:
        bars = fetch_bars(t, period=period, interval=interval)
        if bars:
            stats[t] = db.upsert_prices(conn, t, interval, bars)
    return stats


def closes(conn, ticker: str, interval: str = PRICE_INTERVAL,
           limit: int | None = None) -> list[float]:
    """Bir ticker'ın kapanışları (kronolojik). Özellik/backtest için ham seri."""
    rows = db.get_prices(conn, ticker, interval, limit=limit)
    return [float(r["close"]) for r in rows if r["close"] is not None]


def bar_times(conn, ticker: str, interval: str = PRICE_INTERVAL) -> list[str]:
    """Kapanışlarla hizalı bar zamanları (UTC iso)."""
    rows = db.get_prices(conn, ticker, interval)
    return [r["ts"] for r in rows if r["close"] is not None]


def price_at_or_after(conn, ticker: str, target_iso: str,
                      interval: str = PRICE_INTERVAL) -> tuple[str, float] | None:
    """
    target zamanından SONRAKİ ilk barı döner (ts_iso, close). Tahmin olgunlaşmasını
    bu çözer: hedef saat piyasa kapalıya denk gelirse bir sonraki seans barını alır.
    """
    row = conn.execute(
        """SELECT ts, close FROM prices
           WHERE ticker=? AND interval=? AND ts>=? AND close IS NOT NULL
           ORDER BY ts LIMIT 1""",
        (ticker, interval, target_iso),
    ).fetchone()
    if row:
        return row["ts"], float(row["close"])
    return None
