"""
Hisse-bazlı haber toplayıcı — yfinance per-ticker news (her şirketin güncel haberleri).

Ticker başına yfinance haber akışı çeker. RSS/Reddit'in aksine BIST'i de kapsar
(THYAO.IS, GARAN.IS... haberleri geliyor) → BIST haber/sentiment açığını kapatır.
Headline'a kanonik sembol eklenir ki ticker eşleyici (tickers.py) doğru hisseye atasın.

"Bir haber hissenin seyrini değiştirir mi?" sorusunun veri tabanı budur: güncel başlıklar
sentiment'tan geçer, yüksek-skorlu olaylar panelde öne çıkar.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from .base import BaseCollector
from ..models import Record, Author, SourceType
from ..config import TICKERS, yf_symbol


def _parse(item: dict):
    """yfinance haber öğesini ayrıştır (hem eski düz hem yeni 'content' formatı)."""
    try:
        c = item.get("content") if isinstance(item.get("content"), dict) else item
        title = c.get("title") or item.get("title") or ""
        summary = c.get("summary") or c.get("description") or ""
        prov = c.get("provider")
        publisher = (prov.get("displayName") if isinstance(prov, dict)
                     else (item.get("publisher") or "yfnews"))
        url = ""
        for k in ("canonicalUrl", "clickThroughUrl"):
            v = c.get(k)
            if isinstance(v, dict) and v.get("url"):
                url = v["url"]
                break
        url = url or item.get("link", "")
        created = None
        ep = item.get("providerPublishTime")
        if ep:
            created = datetime.fromtimestamp(ep, tz=timezone.utc)
        else:
            ds = c.get("pubDate") or c.get("displayTime")
            if ds:
                try:
                    created = datetime.fromisoformat(str(ds).replace("Z", "+00:00"))
                except Exception:
                    created = None
        return title, summary, publisher, url, created or datetime.now(timezone.utc)
    except Exception:
        return None


class YFNewsCollector(BaseCollector):
    """Her izlenen hisse için yfinance güncel haberleri (US + BIST)."""
    name = "yfnews"

    def __init__(self, tickers: list[str] | None = None, limit: int = 10,
                 max_age_days: int = 21):
        self.tickers = tickers or list(TICKERS)
        self.limit = limit
        self.max_age_days = max_age_days   # eski (bayat) haberi alma

    def collect(self) -> list[Record]:
        try:
            import yfinance as yf  # tembel import
        except Exception as e:  # pragma: no cover
            print(f"[yfnews] yfinance yok: {e}")
            return []
        records: list[Record] = []
        seen: set[str] = set()
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        for t in self.tickers:
            sym = yf_symbol(t)
            try:
                items = yf.Ticker(sym).news or []
            except Exception as e:  # pragma: no cover
                print(f"[yfnews] {sym} alınamadı: {e}")
                continue
            for it in items[: self.limit]:
                parsed = _parse(it)
                if not parsed:
                    continue
                title, summary, publisher, url, created = parsed
                if not title or created < cutoff:   # boş/bayat haberi atla
                    continue
                key = (url or title)[:120]
                if key in seen:
                    continue
                seen.add(key)
                # Kanonik sembolü başa ekle → resolve_tickers bu hisseye atasın.
                text = f"{t}: {title}. {summary}".strip()
                records.append(Record(
                    source="yf:news",
                    source_type=SourceType.NEWS,
                    text=text,
                    created_at=created,
                    author=Author(handle=publisher or "yfnews", source="yf:news", verified=True),
                    url=url or None,
                    tickers=[t],   # bu hisse için çekildi → doğrudan ata (pipeline union eder)
                ))
        return records
