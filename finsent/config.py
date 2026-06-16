"""
Merkezi yapılandırma. Hangi hisseleri izliyoruz, hangi takma adlarla anılıyorlar,
ağırlıklar ne — hepsi burada. Kod değiştirmeden buradan ayar yapılır.
İleride config.yaml'a taşınabilir; şimdilik sıfır bağımlılık için Python dict.
"""

# İzlenen semboller ve metinde geçebilecek takma adları.
# Anahtar = kanonik sembol, değer = bu sembole işaret eden ifadeler (küçük harf).
# Ticker eşleme (tickers.py) bunu kullanır. En kritik veri yapısı:
# yanlış eşleme tüm sentiment'i bozar, o yüzden alias'ları özenli tut.
TICKERS: dict[str, list[str]] = {
    # --- BIST ---
    "THYAO": ["thyao", "türk hava yolları", "turk hava yollari", "thy", "turkish airlines"],
    "GARAN": ["garan", "garanti", "garanti bankası", "garanti bbva"],
    "ASELS": ["asels", "aselsan"],
    "AKBNK": ["akbnk", "akbank"],
    "BIMAS": ["bimas", "bim", "bim mağazalar"],
    "TUPRS": ["tuprs", "tüpraş", "tupras"],
    "SISE":  ["sise", "şişecam", "sisecam"],
    "KCHOL": ["kchol", "koç holding", "koc holding"],
    "EREGL": ["eregl", "ereğli", "erdemir"],
    # --- US (mega-tech çekirdek) ---
    "AAPL":  ["aapl", "apple"],
    "TSLA":  ["tsla", "tesla"],
    "NVDA":  ["nvda", "nvidia"],
    "MSFT":  ["msft", "microsoft"],
    "AMZN":  ["amzn", "amazon"],
    "META":  ["meta", "facebook"],
    "GOOGL": ["googl", "google", "alphabet"],
    # --- US (likit + sektör-çeşitli genişleme; haber-zengin, günlük trade) ---
    # NOT: kısa/ortak-kelime alias YOK ("v"/"cost"/"ko"/"dis" gibi false-match yapardı);
    # yf:news zaten ticker'ı doğrudan atar (pipeline union eder).
    "AMD":   ["amd", "advanced micro"],
    "AVGO":  ["avgo", "broadcom"],
    "NFLX":  ["nflx", "netflix"],
    "PLTR":  ["pltr", "palantir"],
    "JPM":   ["jpm", "jpmorgan", "jp morgan"],
    "V":     ["visa"],
    "XOM":   ["xom", "exxon"],
    "UNH":   ["unh", "unitedhealth"],
    "WMT":   ["wmt", "walmart"],
    "COST":  ["costco"],
    "KO":    ["coca cola", "coca-cola"],
    "DIS":   ["disney"],
    "UBER":  ["uber"],
    # --- Stage 15: piyasa taraması ile eklenen YÜKSEK-POTANSİYELLİ likitler ---
    # run_market_scan.py (65 aday): bunlar 4/4 momentum HİZALI (güven-proxy ~0.60); rejim
    # trende dönünce yüksek-güven katmanına (≥0.66) geçebilirler. ŞU AN hiçbiri ≥0.70 DEĞİL
    # (ölçülen tavan ~%53–59; ">%70 güvenilir yön" yok — EMH). Canlı izleme/işaretleme için.
    "LLY":   ["eli lilly", "lilly"],
    "CSCO":  ["cisco"],
    "MU":    ["micron"],
    "INTC":  ["intel"],
    "PYPL":  ["paypal"],
    "MRVL":  ["marvell"],
    "TMUS":  ["t-mobile", "tmobile"],
    "SNOW":  ["snowflake"],
    "CRWD":  ["crowdstrike"],
    "COIN":  ["coinbase"],
    "FROTO": ["froto", "ford otosan"],
    "ARCLK": ["arclk", "arçelik", "arcelik"],
    # --- KRIPTO (canlı, 1 coin): en haber-zengin + en likit. 7/24 işler → SEANS YOK
    #     (günlük kapanış = UTC gün sınırı; hisselerin düzenli-seans kapanışından farklı).
    #     Stage 5: kripto kesitsel edge'i SEYRELTEBİLİR — eklendi ama izlenir. ---
    "BTC":   ["btc", "bitcoin"],
}

# Borsa/bölge bağlamı — dil ve kaynak seçiminde kullanılır.
TICKER_MARKET: dict[str, str] = {
    "THYAO": "BIST", "GARAN": "BIST", "ASELS": "BIST", "AKBNK": "BIST",
    "BIMAS": "BIST", "TUPRS": "BIST", "SISE": "BIST", "KCHOL": "BIST", "EREGL": "BIST",
    "AAPL": "US", "TSLA": "US", "NVDA": "US", "MSFT": "US",
    "AMZN": "US", "META": "US", "GOOGL": "US",
    "AMD": "US", "AVGO": "US", "NFLX": "US", "PLTR": "US", "JPM": "US", "V": "US",
    "XOM": "US", "UNH": "US", "WMT": "US", "COST": "US", "KO": "US", "DIS": "US", "UBER": "US",
    # Stage 15 eklenenler:
    "LLY": "US", "CSCO": "US", "MU": "US", "INTC": "US", "PYPL": "US", "MRVL": "US",
    "TMUS": "US", "SNOW": "US", "CRWD": "US", "COIN": "US",
    "FROTO": "BIST", "ARCLK": "BIST",
    "BTC": "CRYPTO",   # 7/24, seans yok (yf: BTC-USD)
}

# Kaynak türü bazında temel ağırlık. Haber sosyalden ağır çünkü daha az gürültülü.
SOURCE_TYPE_WEIGHT: dict[str, float] = {
    "news": 1.0,
    "disclosure": 1.2,   # resmi açıklama en güvenilir
    "social": 0.6,
}

# Belirli kaynaklara güven çarpanı (0..1.5). Kurumsal kaynak > anonim forum.
SOURCE_TRUST: dict[str, float] = {
    "kap": 1.5,
    "rss:bloomberght": 1.1,
    "rss:investing": 1.0,
    "reddit": 0.7,
    "stocktwits": 0.6,
}

# RSS haber kaynakları (hepsi ücretsiz). Çalışmayanı kaldır, yenisini ekle.
RSS_FEEDS: dict[str, str] = {
    # Türkçe / BIST (doğrulandı çalışıyor — BIST şirketlerini anar, ticker eşleşir):
    "rss:bloomberght": "https://www.bloomberght.com/rss",
    "rss:investing":   "https://tr.investing.com/rss/news.rss",
    "rss:dunya":       "https://www.dunya.com/rss",
    "rss:ntv_ekonomi": "https://www.ntv.com.tr/ekonomi.rss",
    # İngilizce / global:
    "rss:cnbc":        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
}

# Reddit subreddit'leri (ücretsiz okuma). Borsa odaklı topluluklar.
REDDIT_SUBS: list[str] = ["borsa", "BorsaIstanbul", "stocks", "wallstreetbets"]

# Toplama aşamasında zaman penceresi tanımları (saat).
WINDOWS = {
    "live": 0.25,   # son 15 dk — anlık (hot path)
    "1h": 1,
    "24h": 24,
    "7d": 24 * 7,
}

# ---------------------------------------------------------------------------
# Öngörü (forecast) katmanı ayarları
# ---------------------------------------------------------------------------
# Duygu + momentum + fiyat trendinden GELECEĞE dönük (gün içi) bir sinyal
# üretiriz; sinyalin gerçek isabet oranı fiyat geçmişiyle backtest edilir.
#
# Fiyat verisi yfinance'ten gelir (ücretsiz). BIST sembolleri ".IS" eki ister
# (THYAO -> THYAO.IS), US sembolleri eksiz çekilir.
YF_SUFFIX: dict[str, str] = {"BIST": ".IS", "US": "", "CRYPTO": "-USD"}

PRICE_INTERVAL = "60m"          # saatlik bar (gün içi ufuk için yeterli çözünürlük)
PRICE_PERIOD_LIVE = "5d"        # canlı özellikler için kısa geçmiş (hızlı tazeleme)
PRICE_PERIOD_BACKTEST = "730d"  # saatlik model ~2y (3-saatlik minik edge ancak büyük örnekle görünür)
HORIZON_BARS = 3                # kaç bar (≈ saat) ilerisi tahmin edilsin — "birkaç saat"

# Sinyal kararsız (neutral) sayılma bandı: |signal| bunun altındaysa yön belirsiz.
NEUTRAL_BAND = 0.10

# Sentiment özelliklerine başlangıç (prior) ağırlıkları. Fiyat-geçmişi backtest'i
# bunları ölçemez (geçmiş duygu verisi yok); canlı tahmin günlüğü zamanla doğrular.
# Hipotez: pozitif duygu/momentum -> pozitif kısa vadeli getiri.
SENT_PRIORS: dict[str, float] = {
    "sent": 0.18, "mom": 0.18, "posneg": 0.10, "logvol": 0.04,
}


def yf_symbol(ticker: str) -> str:
    """Kanonik sembolü yfinance sembolüne çevirir (BIST -> .IS, CRYPTO -> -USD)."""
    market = TICKER_MARKET.get(ticker, "US")
    return ticker + YF_SUFFIX.get(market, "")


# ---------------------------------------------------------------------------
# Bilimsel universe genişlemesi — KRİPTO (yalnız araştırma/backtest)
# ---------------------------------------------------------------------------
# Coin'ler CANLI ürüne (TICKERS, panel, duygu hattı) EKLENMEZ — orası 16 hisse kalır.
# Yalnız öngörülebilirlik çalışmasının EVRENİNİ genişletir (yfinance "BTC-USD").
# Kripto = büyük ölçüde bağımsız 3. faktör bloğu → kesitsel genişlik + edge'in
# bağımsız bir varlık sınıfında da görünmesi = en güçlü OOS doğrulama.
CRYPTO_TICKERS: dict[str, list[str]] = {
    # NOT: BTC artık CANLI evrende (TICKERS) — burada tekrar yok (science_universe dup'ını önler).
    "ETH":  ["eth", "ethereum"],
    "SOL":  ["sol", "solana"],
    "BNB":  ["bnb", "binance coin"],
    "XRP":  ["xrp", "ripple"],
    "ADA":  ["ada", "cardano"],
    "DOGE": ["doge", "dogecoin"],
    "AVAX": ["avax", "avalanche"],
}
for _c in CRYPTO_TICKERS:
    TICKER_MARKET[_c] = "CRYPTO"


def science_universe() -> list[str]:
    """Öngörülebilirlik çalışmasının evreni: canlı hisseler + kripto (yalnız backtest)."""
    return list(TICKERS) + list(CRYPTO_TICKERS)
