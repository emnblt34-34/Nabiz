"""
Finansal duygu analizi.

İki backend, ortak arayüz:
  1) LexiconSentiment  — sıfır bağımlılık, Türkçe+İngilizce finans sözlüğü.
     Hemen çalışır, hiçbir kurulum/indirme istemez. MVP varsayılanı.
  2) TransformerSentiment — lokal FinBERT (ücretsiz, makinende çalışır).
     transformers+torch kuruluysa devreye girer; değilse sessizce lexicon'a düşer.

Finansal dil genel dilden farklı: "short", "düştü", "zarar" negatif; "uçtu",
"ralli", "temettü" pozitif. Genel sentiment modelleri bunu kaçırır, o yüzden
sözlük finans-odaklı tutuldu.

Çıktı: (Sentiment etiketi, -1..+1 skor).
"""
from __future__ import annotations

import re
from .models import Sentiment

# --- Finans-odaklı sözlük (genişletmeye açık) -------------------------------
# Türkçe + İngilizce. Küçük harf, kelime-sınırlı eşleşir.
POSITIVE_WORDS = {
    # TR
    "uçtu", "ralli", "yükseliş", "kazanç", "kâr", "kar", "temettü", "güçlü",
    "rekor", "büyüme", "tavan", "alım", "boğa", "pozitif", "iyimser", "fırladı",
    "toparlandı", "destek", "primli", "yükseldi", "artış",
    # EN
    "bullish", "rally", "surge", "gain", "profit", "growth", "beat", "upgrade",
    "buy", "long", "moon", "breakout", "strong", "soared", "outperform",
}
NEGATIVE_WORDS = {
    # TR
    "düştü", "zarar", "çöküş", "satış", "ayı", "negatif", "kötümser", "dip",
    "taban", "kaybetti", "geriledi", "iflas", "borç", "zayıf", "panik",
    "düşüş", "eridi", "çakıldı", "kayıp", "baskı",
    # EN
    "bearish", "crash", "loss", "drop", "sell", "short", "downgrade", "dump",
    "weak", "plunge", "miss", "fell", "selloff", "underperform", "fraud",
}
# Olumsuzlayıcılar — "iyi değil" gibi durumlar için skoru ters çevirir.
NEGATORS = {"değil", "yok", "not", "no", "asla", "hiç"}

_WORD = re.compile(r"\w+", re.UNICODE)


class LexiconSentiment:
    """Sözlük tabanlı, sıfır bağımlılık. Olumsuzlama farkındalıklı."""

    name = "lexicon"

    def score(self, text: str) -> tuple[Sentiment, float]:
        tokens = [t.lower() for t in _WORD.findall(text)]
        if not tokens:
            return Sentiment.NEUTRAL, 0.0

        pos = neg = 0
        for i, tok in enumerate(tokens):
            polarity = 0
            if tok in POSITIVE_WORDS:
                polarity = 1
            elif tok in NEGATIVE_WORDS:
                polarity = -1
            if polarity == 0:
                continue
            # Önceki 2 token'da olumsuzlayıcı varsa ters çevir.
            window = tokens[max(0, i - 2):i]
            if any(w in NEGATORS for w in window):
                polarity *= -1
            if polarity > 0:
                pos += 1
            else:
                neg += 1

        total = pos + neg
        if total == 0:
            return Sentiment.NEUTRAL, 0.0
        raw = (pos - neg) / total          # -1..+1
        if raw > 0.15:
            return Sentiment.POSITIVE, raw
        if raw < -0.15:
            return Sentiment.NEGATIVE, raw
        return Sentiment.NEUTRAL, raw


class TransformerSentiment:
    """
    Lokal FinBERT backend. transformers+torch yoksa __init__ patlar; üst katman
    bunu yakalayıp lexicon'a düşer. İndirilen model makinende kalır, ücretsizdir.
    """
    name = "finbert"

    def __init__(self, model: str = "ProsusAI/finbert"):
        from transformers import pipeline  # lazy import
        self._pipe = pipeline("sentiment-analysis", model=model, truncation=True)

    def score(self, text: str) -> tuple[Sentiment, float]:
        out = self._pipe(text[:512])[0]
        label = out["label"].lower()
        conf = float(out["score"])
        if label.startswith("pos"):
            return Sentiment.POSITIVE, conf
        if label.startswith("neg"):
            return Sentiment.NEGATIVE, -conf
        return Sentiment.NEUTRAL, 0.0


def get_analyzer(prefer_transformer: bool = False):
    """
    Uygun analizörü döndürür. prefer_transformer=True ise FinBERT'i dener,
    kurulu değilse otomatik lexicon'a düşer. Varsayılan sıfır-bağımlılık.
    """
    if prefer_transformer:
        try:
            return TransformerSentiment()
        except Exception as e:
            print(f"[sentiment] FinBERT yüklenemedi ({e}); lexicon'a düşülüyor.")
    return LexiconSentiment()


if __name__ == "__main__":
    an = get_analyzer(prefer_transformer=False)
    tests = [
        "THYAO bugün uçtu, rekor kâr açıkladı",
        "Tesla çakıldı, büyük zarar var",
        "Garanti çok iyi değil bence",   # olumsuzlama
        "Bugün piyasa yatay seyrediyor",
        "$NVDA bullish breakout, strong buy",
    ]
    for t in tests:
        s, v = an.score(t)
        print(f"{v:+.2f} {s.value:8} | {t}")
