"""
Döviz katmanı — BIST'i USD'ye çevirir (TL enflasyonunu sinyalden çıkarır).

Stage 5 dersi: 'max' geçmişte BIST nominal fiyatları TL enflasyonuyla 50x+ şişiyor →
ölçüm bozuluyor. Ayrıca kesitsel sıralama TL-bazlı BIST momentumunu USD-bazlı ABD
momentumuyla kıyaslıyor (tutarsız). Çözüm: BIST kapanışını USDTRY'ye bölerek USD'ye
çevir. Böylece (a) enflasyon-nötr uzun geçmiş açılır, (b) tüm evren ortak para biriminde
karşılaştırılabilir hale gelir.

yfinance: "USDTRY=X" = 1 USD kaç TL. usd_price = try_price / usdtry.
"""
from __future__ import annotations

from . import db, prices
from .config import TICKER_MARKET

FX_TICKER = "USDTRY"   # prices tablosunda saklandığı ad
FX_YF = "USDTRY=X"     # yfinance sembolü


def update_fx(conn, period: str = "5y", interval: str = "1d") -> int:
    """USDTRY kurunu çekip prices tablosuna (ticker=USDTRY) yazar. Bar sayısı döner."""
    yf = prices._yf()
    if yf is None:
        return 0
    for attempt in range(2):
        try:
            df = yf.Ticker(FX_YF).history(period=period, interval=interval, auto_adjust=True)
            if df is None or df.empty:
                return 0
            bars = []
            for ts, row in df.iterrows():
                c = row.get("Close")
                if c is None or c != c:
                    continue
                bars.append((prices._to_utc_iso(ts), None, None, None, float(c), None))
            return db.upsert_prices(conn, FX_TICKER, interval, bars)
        except Exception as e:  # pragma: no cover
            if attempt == 0:
                continue
            print(f"[fx] USDTRY çekilemedi: {e}")
            return 0
    return 0


def _fx_map(conn, interval: str) -> dict:
    """tarih(YYYY-MM-DD) -> USDTRY kuru."""
    rows = db.get_prices(conn, FX_TICKER, interval)
    return {r["ts"][:10]: float(r["close"]) for r in rows if r["close"] is not None}


def usd_series(conn, ticker: str, interval: str = "1d"):
    """
    USD cinsinden (closes, dates). BIST -> TL kapanışı / USDTRY (kur olan günlerde);
    US/CRYPTO -> aynen (zaten USD). Kur bulunamayan BIST günleri atlanır.
    """
    rows = db.get_prices(conn, ticker, interval)
    series = [(r["ts"][:10], float(r["close"])) for r in rows if r["close"] is not None]
    if TICKER_MARKET.get(ticker, "US") != "BIST":
        return [c for _, c in series], [d for d, _ in series]
    fx = _fx_map(conn, interval)
    closes, dates = [], []
    for d, c in series:
        rate = fx.get(d)
        if rate and rate > 0:
            closes.append(c / rate)
            dates.append(d)
    return closes, dates
