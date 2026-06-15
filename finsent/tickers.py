"""
Varlık (ticker) eşleme — projenin gizli kalbi.

Bir metnin hangi hisse(ler)den bahsettiğini çözer. Üç yöntemi birleştirir:
  1) Cashtag: "$THYAO" gibi açık işaretler (en güvenilir)
  2) Alias: "garanti", "tesla" gibi şirket adları (config.TICKERS)
  3) Kelime sınırı koruması: "asel" kelimesinin "aselsan" içinde yanlış
     eşleşmesini engeller; regex word-boundary kullanır.

Yanlış eşleme = çöp sentiment. O yüzden burada cömert değil, titiz davranıyoruz.
"""
from __future__ import annotations

import re
from .config import TICKERS

# Cashtag deseni: $THYAO, $AAPL — 1-6 harf/rakam.
_CASHTAG = re.compile(r"\$([A-Za-z]{1,6}[0-9]?)\b")

# Alias'lar için derlenmiş, kelime-sınırlı desenler. Uzun alias'lar önce gelsin
# ("garanti bankası" > "garanti") ki en spesifik eşleşme kazansın.
_ALIAS_PATTERNS: list[tuple[re.Pattern, str]] = []


def _build_patterns() -> None:
    pairs: list[tuple[str, str]] = []
    for symbol, aliases in TICKERS.items():
        for alias in aliases:
            pairs.append((alias, symbol))
    # Uzun alias önce (spesifiklik önceliği)
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    for alias, symbol in pairs:
        # \b ... \b kelime sınırı; alias içinde boşluk olabilir.
        pat = re.compile(r"\b" + re.escape(alias) + r"\b", re.IGNORECASE)
        _ALIAS_PATTERNS.append((pat, symbol))


_build_patterns()

# Cashtag eşlemesi için geçerli semboller kümesi (büyük harf).
_VALID_SYMBOLS = {s.upper() for s in TICKERS.keys()}


def resolve_tickers(text: str) -> list[str]:
    """
    Metinden ticker listesi çıkarır. Sıralı ve tekrarsız döner.

    >>> resolve_tickers("Garanti bugün uçtu, $AAPL de iyi")
    ['GARAN', 'AAPL']
    """
    found: list[str] = []
    seen: set[str] = set()

    # 1) Cashtag — en güvenilir
    for m in _CASHTAG.finditer(text):
        sym = m.group(1).upper()
        if sym in _VALID_SYMBOLS and sym not in seen:
            seen.add(sym)
            found.append(sym)

    # 2) Alias eşleme
    for pat, symbol in _ALIAS_PATTERNS:
        if symbol in seen:
            continue
        if pat.search(text):
            seen.add(symbol)
            found.append(symbol)

    return found


if __name__ == "__main__":
    # Hızlı kendi-test
    cases = [
        "Garanti bugün uçtu, $AAPL de iyi görünüyor",
        "ASELSAN savunmada güçlü, THYAO ise zayıf",
        "Bugün hava güzel",  # eşleşme yok
        "tesla ve nvidia rallisi sürüyor",
    ]
    for c in cases:
        print(f"{c!r:55} -> {resolve_tickers(c)}")
