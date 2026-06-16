"""
Pipeline orkestrasyonu.

Akış:
  collect()  → her toplayıcıdan ham Record listesi
  process()  → her kayıt için: dil tespiti, ticker eşleme, kredibilite skoru,
               sentiment; ticker'ı olmayan kayıtlar elenir
  dedupe()   → fingerprint bazlı tekilleştirme (aynı haber 10 sitede)
  store      → SQLite'a yaz (id çakışması ayrıca yok sayılır)
  aggregate  → ticker × pencere skorlarını hesapla

run_once() bütün bunu tek seferde yapar. Stream (anlık) ve batch (günlük)
script'leri bunu farklı kaynak setleriyle çağırır.
"""
from __future__ import annotations

from .models import Record
from .tickers import resolve_tickers
from .credibility import score_author
from .sentiment import get_analyzer
from . import db, aggregate
from .config import TICKERS


def _detect_lang(text: str) -> str:
    """Kaba dil tespiti: Türkçe'ye özgü karakter/kelime varsa 'tr', yoksa 'en'.
    Sıfır bağımlılık için basit sezgisel; istersen langdetect ile değiştir."""
    tr_chars = set("çğıöşüÇĞİÖŞÜ")
    tr_words = {" ve ", " bir ", " bu ", " için ", " ile ", "hisse", "borsa"}
    t = text.lower()
    if any(c in tr_chars for c in text) or any(w in t for w in tr_words):
        return "tr"
    return "en"


def process(records: list[Record], analyzer=None) -> list[Record]:
    """Ham kayıtları zenginleştirir. Ticker eşleşmeyen kayıtları eler."""
    analyzer = analyzer or get_analyzer(prefer_transformer=False)
    out: list[Record] = []
    for r in records:
        # Collector ticker'ı önceden atadıysa (ör. yf:news) KORU; metinden çözülenlerle birleştir.
        resolved = resolve_tickers(r.text)
        r.tickers = sorted(set(r.tickers) | set(resolved)) if r.tickers else resolved
        if not r.tickers:
            continue  # hangi hisse olduğu belirsiz → çöp, atla
        r.lang = _detect_lang(r.text)
        r.credibility = score_author(r.author).credibility
        r.sentiment, r.sentiment_score = analyzer.score(r.text)
        out.append(r)
    return out


def dedupe(records: list[Record]) -> list[Record]:
    """fingerprint bazlı tekilleştirme. Aynı içeriğin ilk görüleni tutulur.
    Not: koordineli bot kampanyaları (aynı metin, farklı hesap) burada da
    tekilleşir; istenirse kampanya sayısı ayrı bir sinyale çevrilebilir."""
    seen: set[str] = set()
    out: list[Record] = []
    for r in records:
        if r.fingerprint in seen:
            continue
        seen.add(r.fingerprint)
        out.append(r)
    return out


def run_once(collectors: list, prefer_transformer: bool = False) -> dict:
    """Tüm pipeline'ı bir kez çalıştırır. Özet istatistik döner."""
    analyzer = get_analyzer(prefer_transformer=prefer_transformer)
    conn = db.connect()

    # 1) Topla
    raw: list[Record] = []
    for c in collectors:
        got = c.collect()
        print(f"[collect] {c.name}: {len(got)} ham kayıt")
        raw.extend(got)

    # 2) İşle (zenginleştir + ticker filtresi)
    processed = process(raw, analyzer=analyzer)
    print(f"[process] {len(processed)} kayıt ticker eşleşti")

    # 3) Dedup
    deduped = dedupe(processed)
    print(f"[dedupe] {len(deduped)} benzersiz kayıt ({len(processed)-len(deduped)} kopya elendi)")

    # 4) Kaydet
    inserted = db.insert_records(conn, deduped)
    print(f"[store] {inserted} yeni kayıt DB'ye yazıldı")

    # 5) Topla/skorla
    scores = aggregate.aggregate_all(conn, list(TICKERS.keys()))
    print(f"[aggregate] {len(scores)} ticker×pencere skoru güncellendi")

    conn.close()
    return {
        "raw": len(raw), "processed": len(processed),
        "deduped": len(deduped), "inserted": inserted, "scores": len(scores),
    }
