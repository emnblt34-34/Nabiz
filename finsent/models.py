"""
Çekirdek veri şemaları.

Tüm kaynaklar (Reddit, StockTwits, RSS haber, KAP, ileride X) ham verilerini
tek bir ortak şemaya — Record — normalize eder. Pipeline'ın geri kalanı sadece
bu şemayı tanır; kaynak çeşitliliği bu noktadan sonra görünmez olur.

Bilerek dataclass kullanıldı (pydantic yerine): sıfır bağımlılık, sıfır kurulum.
Postgres'e/Supabase'e geçişte buradaki alanlar birebir kolon olur.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import hashlib
import json


class SourceType(str, Enum):
    """Kaynak türü. Ağırlıklandırma ve işleme mantığı buna göre dallanır."""
    SOCIAL = "social"      # Reddit, StockTwits, X — gürültülü, hacimli
    NEWS = "news"          # RSS finans haberleri — daha güvenilir, dedup şart
    DISCLOSURE = "disclosure"  # KAP — resmi şirket olayı, sentiment değil event


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class Author:
    """
    Bir içeriğin yazarı. Kredibilite skorlaması bu alanları besler.
    Haber kaynaklarında çoğu alan boş olur (kaynak adı = handle).
    """
    handle: str
    source: str                      # "reddit", "stocktwits", ...
    followers: Optional[int] = None
    following: Optional[int] = None
    account_age_days: Optional[int] = None
    post_count: Optional[int] = None
    has_avatar: Optional[bool] = None
    has_bio: Optional[bool] = None
    verified: Optional[bool] = None

    @property
    def uid(self) -> str:
        return f"{self.source}:{self.handle}"


@dataclass
class Record:
    """
    Pipeline'ın evrensel birimi. Bir tweet, bir Reddit yorumu, bir haber,
    bir KAP açıklaması — hepsi bir Record'a dönüşür.
    """
    source: str                      # somut kaynak: "reddit", "rss:bloomberght"
    source_type: SourceType
    text: str
    created_at: datetime
    author: Author
    url: Optional[str] = None
    lang: Optional[str] = None       # "tr" / "en" — normalize aşamasında doldurulur

    # Pipeline aşamalarında doldurulan alanlar:
    tickers: list[str] = field(default_factory=list)   # eşlenen semboller
    credibility: float = 1.0          # 0..1 yazar güven skoru
    sentiment: Optional[Sentiment] = None
    sentiment_score: float = 0.0      # -1 (negatif) .. +1 (pozitif)
    engagement: int = 0               # beğeni/upvote/yorum toplamı — hacim ağırlığı

    @property
    def fingerprint(self) -> str:
        """
        Deduplication için içerik parmak izi. Aynı haberin 10 sitede çıkması
        veya kopyala-yapıştır bot kampanyaları bu sayede tekilleşir.
        Metni normalize edip (küçük harf, boşluk sadeleştirme) hash'liyoruz.
        """
        norm = " ".join(self.text.lower().split())
        return hashlib.sha1(norm.encode("utf-8")).hexdigest()

    @property
    def id(self) -> str:
        """Kaynak + url + parmak izi ile benzersiz kayıt kimliği."""
        base = f"{self.source}|{self.url or ''}|{self.fingerprint}"
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]

    def to_row(self) -> dict:
        """SQLite/Postgres satırına çevir."""
        d = asdict(self)
        d["source_type"] = self.source_type.value
        d["sentiment"] = self.sentiment.value if self.sentiment else None
        d["created_at"] = self.created_at.astimezone(timezone.utc).isoformat()
        d["tickers"] = json.dumps(self.tickers)
        d["author"] = json.dumps(asdict(self.author))
        d["id"] = self.id
        d["fingerprint"] = self.fingerprint
        return d


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
