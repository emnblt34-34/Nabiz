"""
CoinGecko kripto veri katmanı (Stage 22).

NEDEN: yfinance bazı coinleri (özellikle HYPE/Hyperliquid) VERMİYOR ve kripto gün-içi
gecikebiliyor. CoinGecko keyless public API'si 17.000+ coin'i (HYPE dahil) gerçek-zamanlı,
ÜCRETSİZ, KEY GEREKTİRMEDEN verir. Böylece HYPE + tüm takip coinleri canlı çekilebilir ve
seviye motoru (levels._levels_core) yfinance'te olmayan coinlerde de çalışır.

Kullanım:
  crypto_feed.live(['HYPE','NEAR','BTC'])      # canlı fiyat + 24s değişim + hacim
  crypto_feed.cg_levels('HYPE')                # CoinGecko OHLC → tam seviye haritası
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

CG_BASE = "https://api.coingecko.com/api/v3"

# Takip ettiğimiz kripto → CoinGecko id eşlemesi (alias kabul: HYPE/hype/hyperliquid)
CG_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "AVAX": "avalanche-2",
    "NEAR": "near", "LINK": "chainlink", "ONDO": "ondo-finance",
    "HYPE": "hyperliquid", "DOGE": "dogecoin", "SUI": "sui", "XRP": "ripple",
    "ADA": "cardano", "BNB": "binancecoin",
    # RWA / DeFi / momentum genişlemesi (Stage 23+)
    "INJ": "injective-protocol", "XLM": "stellar", "RENDER": "render-token",
    "FET": "fetch-ai", "TIA": "celestia", "SEI": "sei-network",
    "JUP": "jupiter-exchange-solana", "PENDLE": "pendle", "ENA": "ethena",
    "TON": "the-open-network", "ARB": "arbitrum", "OP": "optimism", "TAO": "bittensor",
    "UNI": "uniswap", "WLD": "worldcoin-wld", "AAVE": "aave", "XMR": "monero",
    "ZEC": "zcash", "WIF": "dogwifcoin", "JTO": "jito-governance-token",
    "ZRO": "layerzero", "PEAQ": "peaq-2", "KAITO": "kaito", "LDO": "lido-dao",
    "MORPHO": "morpho", "SPK": "spark-2",
    "AXS": "axie-infinity", "SAND": "the-sandbox", "EIGEN": "eigenlayer", "AAVE2": "aave",
    "AERO": "aerodrome-finance",  # status-board glitch fix (live('AERO') $0 donuyordu)
}


def _id(sym: str) -> str:
    """Kanonik sembol ('HYPE') ya da doğrudan CoinGecko id ('hyperliquid') kabul."""
    u = sym.upper()
    if u in CG_IDS:
        return CG_IDS[u]
    return sym.lower()


def _get(path: str, params: dict | None = None):
    url = CG_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310
        return json.loads(r.read())


def live(symbols) -> dict:
    """Verilen kriptolar için canlı fiyat + 24s değişim% + 24s hacim (CoinGecko keyless)."""
    ids = ",".join(_id(s) for s in symbols)
    try:
        d = _get("/simple/price", {"ids": ids, "vs_currencies": "usd",
                                   "include_24hr_change": "true", "include_24hr_vol": "true"})
    except Exception as e:  # pragma: no cover
        return {"_error": str(e)}
    out: dict = {}
    for s in symbols:
        v = d.get(_id(s))
        if v:
            out[s.upper()] = {"price": v["usd"],
                              "chg24h": v.get("usd_24h_change"),
                              "vol24h": v.get("usd_24h_vol")}
    return out


def cg_ohlc(symbol: str, days=90):
    """CoinGecko OHLC mumları → (highs, lows, closes, opens, dates).
    days: 1/7/14/30/90/180/365/max. Granülerlik CoinGecko'ya göre otomatik
    (1-2g=30dk, 3-30g=4s, 31+g=4g). yfinance'te olmayan coinlerde seviye motorunu besler."""
    raw = _get(f"/coins/{_id(symbol)}/ohlc", {"vs_currency": "usd", "days": str(days)})
    highs, lows, closes, opens, dates = [], [], [], [], []
    for row in raw:
        ts, o, h, l, c = row
        dt = datetime.fromtimestamp(ts / 1000, timezone.utc)
        opens.append(float(o))
        highs.append(float(h))
        lows.append(float(l))
        closes.append(float(c))
        dates.append(dt.strftime("%Y-%m-%d"))
    return highs, lows, closes, opens, dates


def cg_ath(symbol: str):
    """GERÇEK tüm-zaman tepe (CoinGecko /coins/{id}). KISA OHLC penceresi ATH'ı KAÇIRIR
    (örn. PENDLE: pencere $2.00 der, gerçek ATH $7.50/2024) → bu endpoint şart."""
    import time
    for attempt in range(3):  # rate-limit'e (429) dayanıklı: sessizce pencere-tepeye düşmek YASAK
        try:
            d = _get(f"/coins/{_id(symbol)}", {"localization": "false", "tickers": "false",
                     "market_data": "true", "community_data": "false", "developer_data": "false"})
            md = d["market_data"]
            return {"price": float(md["ath"]["usd"]), "date": str(md["ath_date"]["usd"])[:10]}
        except Exception:
            if attempt < 2:
                time.sleep(2.5)
    return None


def cg_levels(symbol: str, days=30) -> dict:
    """yfinance'te olmayan coin (HYPE vb.) için tam seviye haritası: CoinGecko OHLC →
    levels._levels_core (test-garantili saf çekirdek). Granülerlik CoinGecko'ya bağlı,
    o yüzden '52h/SMA200' etiketleri pencereyle sınırlı — çıktıda kaynak belirtilir."""
    from .levels import _levels_core, _r  # lazy: döngüsel import önlemi
    try:
        highs, lows, closes, opens, dates = cg_ohlc(symbol, days=days)
    except Exception as e:  # pragma: no cover
        return {"ticker": symbol.upper(), "error": f"CoinGecko OHLC: {e}"}
    if len(closes) < 20:
        return {"ticker": symbol.upper(), "error": "yetersiz CoinGecko verisi"}
    lv = live([symbol]).get(symbol.upper(), {})
    price = lv.get("price") or closes[-1]
    now = datetime.now(timezone.utc)
    d = _levels_core(symbol.upper(), _id(symbol), "CRYPTO",
                     price, highs, lows, closes, opens, dates, now)
    d["source"] = f"CoinGecko OHLC ~{days}g + gerçek-ATH endpoint (52h/SMA pencereyle sınırlı)"
    # GERÇEK ATH ile değiştir (kısa pencere 2024 tepesini kaçırır — MRVL $321 hatasının önlemi)
    a = cg_ath(symbol)
    if a and a["price"] > 0:
        d["window_high"] = d["ath"]["price"]  # eski (kısa-pencere) yerel tepe, referans
        d["ath"] = {"price": _r(a["price"]), "date": a["date"],
                    "below_pct": round((price - a["price"]) / a["price"] * 100, 2)}
    else:
        # cg_ath çekilemedi → pencere-tepeyi GERÇEK ATH gibi SUNMA, işaretle
        d["ath"]["note"] = "⚠ pencere-yerel-tepe (gerçek ATH çekilemedi, rate-limit) — doğrula"
    if lv.get("chg24h") is not None:
        d["chg24h"] = round(lv["chg24h"], 2)
    return d
