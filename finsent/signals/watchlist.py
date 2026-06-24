"""
Birleşik izleme tahtası (Stage 22): ŞU AN incelediğimiz TÜM varlıklar tek board'da.
Kripto → CoinGecko (HYPE dahil, keyless), hisse + forex → yfinance. "durum"/"board" için.

Kullanım: python -m finsent.signals.watchlist
"""
from __future__ import annotations

from . import crypto_feed

# Şu an takip/inceleme listesi (gruplu) — yeni varlık eklenince buraya ekle
CRYPTO = ["NEAR", "HYPE", "BTC", "ETH", "SOL", "AVAX"]
STOCKS = ["MRVL", "INTC", "MU", "FLEX", "WDC", "ARM", "HOOD", "CCL"]
FOREX = [("EURUSD=X", "EUR/USD"), ("DX-Y.NYB", "DXY")]


def _yf_live(sym: str):
    """Son fiyat + değişim. period='1mo' (5d quirk'i son günü atlayabiliyor) + seans-içi 1m tazelik."""
    import yfinance as yf
    tk = yf.Ticker(sym)
    c = [float(x) for x in tk.history(period="1mo", interval="1d",
                                      auto_adjust=False)["Close"].dropna().tolist()]
    if not c:
        return None, None
    px = c[-1]
    base = c[-2] if len(c) >= 2 else c[-1]
    try:  # seans açıksa daha taze fiyat (1m, pre/post dahil)
        it = tk.history(period="1d", interval="1m", prepost=True,
                        auto_adjust=False)["Close"].dropna()
        if len(it):
            live_px = float(it.iloc[-1])
            if abs(live_px - c[-1]) > 1e-6:  # gün-içi taze fiyat var → onu kullan
                px, base = live_px, c[-1]
    except Exception:
        pass
    chg = (px - base) / base * 100 if base else 0.0
    return px, chg


def board() -> None:
    print("=== KRIPTO (CoinGecko, keyless) ===")
    cg = crypto_feed.live(CRYPTO)
    for s in CRYPTO:
        v = cg.get(s)
        if v:
            print("  %-6s $%-11.4f  24s %+6.2f%%  hacim $%.0fM"
                  % (s, v["price"], v["chg24h"] or 0, (v["vol24h"] or 0) / 1e6))
        else:
            print("  %-6s veri yok" % s)
    print("=== HISSE (yfinance) ===")
    for s in STOCKS:
        try:
            px, chg = _yf_live(s)
            print("  %-6s $%-11.2f  gun %+6.2f%%" % (s, px, chg) if px else "  %-6s veri yok" % s)
        except Exception:
            print("  %-6s veri yok" % s)
    print("=== FOREX (yfinance) ===")
    for sym, name in FOREX:
        try:
            px, chg = _yf_live(sym)
            print("  %-8s %-10.4f  gun %+6.2f%%" % (name, px, chg) if px else "  %-8s veri yok" % name)
        except Exception:
            print("  %-8s veri yok" % name)


if __name__ == "__main__":
    board()
