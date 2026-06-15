"""
RSS haber toplayıcı — tamamen ücretsiz, API anahtarı gerekmez.

Borsa/ekonomi haber sitelerinin RSS akışlarını çeker. RSS yapılandırılmış ve
kararlıdır; scraping'e göre çok daha sürdürülebilir. "Bütün haberleri al"
hedefinin sıfır-maliyetli ve sürdürülebilir karşılığı budur.

Bağımlılık: feedparser  (pip install feedparser)
"""
from __future__ import annotations

from datetime import datetime, timezone
from .base import BaseCollector
from ..models import Record, Author, SourceType
from ..config import RSS_FEEDS


class RSSNewsCollector(BaseCollector):
    name = "rss"

    def __init__(self, feeds: dict[str, str] | None = None):
        self.feeds = feeds or RSS_FEEDS

    def collect(self) -> list[Record]:
        try:
            import feedparser
        except ImportError:
            print("[rss] feedparser kurulu değil: pip install feedparser")
            return []

        records: list[Record] = []
        for source_name, url in self.feeds.items():
            try:
                feed = feedparser.parse(url)
            except Exception as e:
                print(f"[rss] {source_name} alınamadı: {e}")
                continue

            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                text = f"{title}. {summary}".strip()
                if not text:
                    continue

                # Yayın zamanı
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    created = datetime(*published[:6], tzinfo=timezone.utc)
                else:
                    created = datetime.now(timezone.utc)

                # Haberde yazar = kaynak; kredibilite kaynak güvenine bırakılır.
                author = Author(handle=source_name, source="news", verified=True)

                records.append(Record(
                    source=source_name,
                    source_type=SourceType.NEWS,
                    text=text,
                    created_at=created,
                    author=author,
                    url=entry.get("link"),
                ))
        return records
