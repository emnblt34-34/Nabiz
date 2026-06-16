"""
Sosyal toplayıcılar — Reddit ve StockTwits. İkisi de ücretsiz okuma sağlar.

Reddit: Eski public .json uçları yetkisiz okumaya (düşük hacim) izin verir.
  Hacim arttığında ücretsiz OAuth app (script type) açıp token kullan — yine $0.
StockTwits: Bu iş için tasarlanmış; mesajların kendi 'sentiment' etiketi bile
  vardır. Public API rate-limit'li ama ücretsizdir.

Bağımlılık: requests
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
import time
from .base import BaseCollector
from ..models import Record, Author, SourceType
from ..config import REDDIT_SUBS, TICKERS, TICKER_MARKET

# Tarayıcı-benzeri UA: jenerik UA Reddit/bazı uçlarda 403 yer. Residential IP'den geçer.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")


def _reddit_token() -> str | None:
    """Reddit app-only OAuth token (ücretsiz). REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET
    env değişkenleri varsa alınır; yoksa None (bloklu public .json'a düşülür).
    Ücretsiz app: reddit.com/prefs/apps → 'script' tipi oluştur, id+secret'i env'e koy."""
    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not (cid and secret):
        return None
    import requests
    try:
        r = requests.post("https://www.reddit.com/api/v1/access_token",
                          auth=(cid, secret), data={"grant_type": "client_credentials"},
                          headers={"User-Agent": UA}, timeout=15)
        r.raise_for_status()
        return r.json().get("access_token")
    except Exception as e:
        print(f"[reddit] OAuth token alınamadı: {e}")
        return None


class RedditCollector(BaseCollector):
    name = "reddit"

    def __init__(self, subs: list[str] | None = None, limit: int = 50):
        self.subs = subs or REDDIT_SUBS
        self.limit = limit

    def collect(self) -> list[Record]:
        import requests
        records: list[Record] = []
        token = _reddit_token()   # OAuth varsa BIST subreddit'leri açılır
        if token:
            base, headers = "https://oauth.reddit.com", {"User-Agent": UA, "Authorization": f"bearer {token}"}
        else:
            base, headers = "https://www.reddit.com", {"User-Agent": UA}
        for sub in self.subs:
            url = f"{base}/r/{sub}/new.json?limit={self.limit}"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[reddit] r/{sub} alınamadı ({'OAuth' if token else 'public'}): {e}")
                continue

            for child in data.get("data", {}).get("children", []):
                p = child.get("data", {})
                text = f"{p.get('title','')}. {p.get('selftext','')}".strip()
                if not text:
                    continue
                created = datetime.fromtimestamp(
                    p.get("created_utc", time.time()), tz=timezone.utc
                )
                # Reddit profil sinyalleri sınırlı; karma'yı vekil olarak kullan.
                author = Author(
                    handle=p.get("author", "deleted"),
                    source="reddit",
                    # author_fullname yoksa hesap silinmiş olabilir
                )
                records.append(Record(
                    source="reddit",
                    source_type=SourceType.SOCIAL,
                    text=text,
                    created_at=created,
                    author=author,
                    url="https://reddit.com" + p.get("permalink", ""),
                    engagement=int(p.get("score", 0)) + int(p.get("num_comments", 0)),
                ))
            time.sleep(1)  # nazik rate-limit
        return records


class StockTwitsCollector(BaseCollector):
    name = "stocktwits"

    def __init__(self, symbols: list[str] | None = None):
        # StockTwits sembol akışları; BIST sembolleri sınırlı, US iyi kapsanır.
        # TÜM ABD hisselerini çek (sadece 3 değil) — kesitsel duygu için tam kapsam.
        self.symbols = symbols or [s for s in TICKERS if TICKER_MARKET.get(s) == "US"]

    def collect(self) -> list[Record]:
        import requests
        records: list[Record] = []
        for sym in self.symbols:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{sym}.json"
            try:
                resp = requests.get(url, headers={"User-Agent": UA}, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[stocktwits] {sym} alınamadı: {e}")
                continue

            for msg in data.get("messages", []):
                text = msg.get("body", "")
                if not text:
                    continue
                created = _parse_st_time(msg.get("created_at"))
                u = msg.get("user", {})
                author = Author(
                    handle=u.get("username", "?"),
                    source="stocktwits",
                    followers=u.get("followers"),
                    following=u.get("following"),
                    post_count=u.get("ideas"),
                    has_avatar=not u.get("avatar_url", "").endswith("default.png"),
                )
                # StockTwits kendi sentiment etiketini verir — bonus sinyal.
                records.append(Record(
                    source="stocktwits",
                    source_type=SourceType.SOCIAL,
                    text=text,
                    created_at=created,
                    author=author,
                    url=f"https://stocktwits.com/message/{msg.get('id')}",
                    engagement=int(msg.get("likes", {}).get("total", 0)),
                ))
            time.sleep(1)
        return records


def _parse_st_time(s: str | None) -> datetime:
    if not s:
        return datetime.now(timezone.utc)
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
