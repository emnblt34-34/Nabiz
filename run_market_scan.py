"""
PİYASA TARAMASI — yüksek güven POTANSİYELİ olan likit hisseleri bul (dürüst).

Soru: Mevcut 29 dışında, ŞU AN yüksek güven katmanına (kalibre proxy ≥0.66, hatta ≥0.70)
ulaşan likit/haber-zengin hisseler hangileri? Bunları canlı evrene ekleyelim.

DÜRÜSTLÜK: güven-proxy 0–1 bir OLASILIK DEĞİL. Kalibrasyon (Stage 14): yüksek kovada bile
ölçülen yön isabeti ~%59 — %70 değil. ">%70 güvenilir yön" veren hisse YOK (EMH). Burada
"potansiyel" = momentumları hizalı + trend rejiminde olan hisseler; ölçülen tavan ~%59.

Yöntem: mevcut evrende eğitilen kesitsel model → her aday için güncel sinyal + kalibre güven.
USD-bazlı (BIST kur-nötr; Stage 6). Çalıştır:  python run_market_scan.py
"""
from __future__ import annotations
from finsent import db, prices, fx, features, forecast
from finsent.config import TICKERS, TICKER_MARKET
from finsent.portfolio import ls_backtest
from finsent.portfolio.cross_section import _confidence, _conf_label, _why, CS_HORIZON

# Aday evren (mevcut 29 DIŞINDA): likit, haber-zengin, günlük trade edilebilir.
# ticker -> (market, [alias...]). Alias'lar kısa/ortak-kelime DEĞİL (false-match'i önler).
CANDIDATES: dict[str, tuple[str, list[str]]] = {
    # --- ABD large/mega-cap (sektör çeşitli) ---
    "GOOG": ("US", ["goog"]), "LLY": ("US", ["eli lilly", "lilly"]),
    "JNJ": ("US", ["johnson & johnson"]), "MA": ("US", ["mastercard"]),
    "HD": ("US", ["home depot"]), "PG": ("US", ["procter"]),
    "ORCL": ("US", ["oracle"]), "CRM": ("US", ["salesforce"]),
    "ADBE": ("US", ["adobe"]), "CSCO": ("US", ["cisco"]),
    "PEP": ("US", ["pepsico", "pepsi"]), "ABBV": ("US", ["abbvie"]),
    "BAC": ("US", ["bank of america"]), "GS": ("US", ["goldman sachs"]),
    "MS": ("US", ["morgan stanley"]), "CVX": ("US", ["chevron"]),
    "QCOM": ("US", ["qualcomm"]), "TXN": ("US", ["texas instruments"]),
    "AMAT": ("US", ["applied materials"]), "MU": ("US", ["micron"]),
    "INTC": ("US", ["intel"]), "BA": ("US", ["boeing"]),
    "CAT": ("US", ["caterpillar"]), "GE": ("US", ["general electric"]),
    "NKE": ("US", ["nike"]), "MCD": ("US", ["mcdonald"]),
    "SBUX": ("US", ["starbucks"]), "PYPL": ("US", ["paypal"]),
    "MRVL": ("US", ["marvell"]), "MRNA": ("US", ["moderna"]),
    "PFE": ("US", ["pfizer"]), "DE": ("US", ["deere"]),
    "LMT": ("US", ["lockheed"]), "RTX": ("US", ["raytheon"]),
    "HON": ("US", ["honeywell"]), "IBM": ("US", ["ibm"]),
    "NOW": ("US", ["servicenow"]), "INTU": ("US", ["intuit"]),
    "AMGN": ("US", ["amgen"]), "GILD": ("US", ["gilead"]),
    "BKNG": ("US", ["booking holdings"]), "TMUS": ("US", ["t-mobile", "tmobile"]),
    "LRCX": ("US", ["lam research"]), "SMCI": ("US", ["super micro", "supermicro"]),
    "ABNB": ("US", ["airbnb"]), "SNOW": ("US", ["snowflake"]),
    "CRWD": ("US", ["crowdstrike"]), "PANW": ("US", ["palo alto networks"]),
    "ANET": ("US", ["arista"]), "SHOP": ("US", ["shopify"]),
    "COIN": ("US", ["coinbase"]),
    # --- BIST-30 likit ---
    "FROTO": ("BIST", ["froto", "ford otosan"]), "TCELL": ("BIST", ["tcell", "turkcell"]),
    "SAHOL": ("BIST", ["sahol", "sabancı", "sabanci"]), "YKBNK": ("BIST", ["ykbnk", "yapı kredi", "yapi kredi"]),
    "ISCTR": ("BIST", ["isctr", "iş bankası", "is bankasi"]), "PETKM": ("BIST", ["petkm", "petkim"]),
    "PGSUS": ("BIST", ["pgsus", "pegasus"]), "TOASO": ("BIST", ["toaso", "tofaş", "tofas"]),
    "ARCLK": ("BIST", ["arclk", "arçelik", "arcelik"]), "SASA": ("BIST", ["sasa", "sasa polyester"]),
    "KOZAL": ("BIST", ["kozal", "koza altın", "koza altin"]), "TTKOM": ("BIST", ["ttkom", "türk telekom", "turk telekom"]),
    "KRDMD": ("BIST", ["krdmd", "kardemir"]), "HEKTS": ("BIST", ["hekts", "hektaş", "hektas"]),
}

THRESH_HIGH = 0.70   # kullanıcının istediği eşik
THRESH_TIER = 0.66   # kalibre "yüksek" katman başlangıcı (ölçülen isabet ~%59)


def main():
    conn = db.connect()
    for t, (m, _a) in CANDIDATES.items():
        TICKER_MARKET.setdefault(t, m)   # yf_symbol/usd_series doğru çalışsın (bellekte)

    print(f"[1/4] USDTRY + {len(CANDIDATES)} aday günlük geçmiş çekiliyor...")
    fx.update_fx(conn, period="max", interval="1d")
    prices.update_prices(conn, list(CANDIDATES), period="3y", interval="1d")

    print("[2/4] Mevcut evrende kesitsel model eğitiliyor (USD)...")
    X, y = [], []
    for t in TICKERS:
        for r in ls_backtest._records(conn, t, CS_HORIZON, "1d", usd=True):
            X.append(r["feat"]); y.append(r["fwd"])
    fc, _ = forecast.fit_from_data(X, y, prefer_ml=True)

    print("[3/4] Adaylar puanlanıyor (güncel sinyal + kalibre güven)...\n")
    results = []
    for t in CANDIDATES:
        closes, dates = fx.usd_series(conn, t, "1d")
        if len(closes) < features.MIN_BARS + 1:
            continue
        last = len(closes) - 1
        feat = features.price_features(closes, last)
        if feat is None:
            continue
        vmap = {r["ts"][:10]: (r["volume"] or 0.0) for r in db.get_prices(conn, t, "1d")}
        volumes = [vmap.get(d, 0.0) for d in dates]
        feat = {**feat, **features.volume_features(closes, volumes, last),
                **{k: 0.0 for k in features.SENT_FEATURES}}
        sig = fc.signal_only(feat)
        conf = _confidence(feat, sig)
        lbl, hit = _conf_label(conf)
        results.append((t, conf, sig, lbl, hit, feat))
    results.sort(key=lambda r: -r[1])

    print(f"  {'tkr':8s} {'mkt':5s} conf   sinyal  katman   ölçülen-isabet")
    for t, conf, sig, lbl, hit, _f in results:
        mark = "  <== EKLE (≥0.70)" if conf >= THRESH_HIGH else ("  <- yüksek katman" if conf >= THRESH_TIER else "")
        print(f"  {t:8s} {TICKER_MARKET[t]:5s} {conf:.3f}  {sig:+.3f}  {lbl:7s}  ~%{int(hit*100)}{mark}")

    add = [(t, conf) for t, conf, *_ in results if conf >= THRESH_HIGH]
    tier = [(t, conf) for t, conf, *_ in results if conf >= THRESH_TIER]
    print(f"\n[4/4] ≥0.70 güven: {[t for t,_ in add]}")
    print(f"      ≥0.66 (yüksek katman, ölçülen ~%59): {[t for t,_ in tier]}")
    print("\n  Eklenecekler için örnek 'neden' (en güçlü aday):")
    if results and results[0][1] >= THRESH_TIER:
        t, conf, sig, lbl, hit, feat = results[0]
        for w in _why(feat, sig, 0, "long" if sig > 0 else "short"):
            print(f"    - {w}")
    print("\n  NOT: güven-proxy olasılık DEĞİL; en yüksek katmanda bile ölçülen yön isabeti ~%59.")
    conn.close()


if __name__ == "__main__":
    main()
