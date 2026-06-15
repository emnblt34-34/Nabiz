"""
KAP (resmi BIST açıklamaları) toplayıcı + offline DEMO toplayıcı.

KAP: Sentiment değil EVENT kaynağıdır — temettü, bilanço, SPK kararı. Ayrı
ele alınır, yüksek güven (SOURCE_TRUST['kap']=1.5) verilir.

SampleCollector: İnternet erişimi olmadan tüm pipeline'ı uçtan uca çalıştırıp
görebilmen için sentetik kayıtlar üretir. Gerçek çalışmada kaldırılır.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import random
from .base import BaseCollector
from ..models import Record, Author, SourceType


class KAPCollector(BaseCollector):
    name = "kap"

    def collect(self) -> list[Record]:
        import requests
        # KAP'ın public açıklama akışı. Uç değişebilir; gerçek entegrasyonda
        # kap.org.tr üzerindeki güncel JSON ucunu doğrula.
        url = "https://www.kap.org.tr/tr/api/disclosures"
        try:
            resp = requests.get(url, timeout=15,
                                headers={"User-Agent": "finsent/0.1"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[kap] alınamadı: {e}")
            return []

        records: list[Record] = []
        for item in (data if isinstance(data, list) else data.get("disclosures", [])):
            title = item.get("title") or item.get("kapTitle") or ""
            company = item.get("companyName") or item.get("stockCodes") or ""
            text = f"{company}. {title}".strip()
            if not text:
                continue
            records.append(Record(
                source="kap",
                source_type=SourceType.DISCLOSURE,
                text=text,
                created_at=datetime.now(timezone.utc),
                author=Author(handle="KAP", source="kap", verified=True),
                url=item.get("disclosureUrl"),
            ))
        return records


class SampleCollector(BaseCollector):
    """Offline test için sentetik veri. Bot ve gerçek hesap karışımı içerir."""
    name = "sample"

    def collect(self) -> list[Record]:
        now = datetime.now(timezone.utc)
        rows = [
            # (metin, kaynak, tür, yazar, etkileşim, dakika önce)
            ("THYAO bugün uçtu, rekor kâr açıkladı! Güçlü alım var",
             "reddit", SourceType.SOCIAL,
             Author("yatirimci_ahmet", "reddit", followers=320, following=400,
                    account_age_days=1200, post_count=900, has_avatar=True, has_bio=True),
             45, 30),
            ("$THYAO short açtım, bu ralli sürmez bence düşüş gelir",
             "stocktwits", SourceType.SOCIAL,
             Author("birey1", "stocktwits", followers=58, following=210,
                    account_age_days=600, post_count=300, has_avatar=True, has_bio=True),
             8, 90),
            # Koordineli bot: aynı pozitif metin, şüpheli hesaplar
            ("THYAO MUHTEŞEM ALIM FIRSATI ROKET GİBİ GİDİYOR",
             "stocktwits", SourceType.SOCIAL,
             Author("bot_x91", "stocktwits", followers=11, following=4900,
                    account_age_days=8, post_count=2400, has_avatar=False, has_bio=False),
             0, 20),
            ("THYAO MUHTEŞEM ALIM FIRSATI ROKET GİBİ GİDİYOR",
             "stocktwits", SourceType.SOCIAL,
             Author("bot_y42", "stocktwits", followers=6, following=5100,
                    account_age_days=5, post_count=3000, has_avatar=False, has_bio=False),
             0, 18),
            ("Türk Hava Yolları çeyrek bilançosunda güçlü büyüme bekleniyor",
             "rss:bloomberght", SourceType.NEWS,
             Author("rss:bloomberght", "news", verified=True), 0, 120),
            ("Tesla çakıldı, büyük zarar açıkladı, satış baskısı sürüyor",
             "rss:cnbc", SourceType.NEWS,
             Author("rss:cnbc", "news", verified=True), 0, 60),
            ("$TSLA bearish, weak delivery numbers, downgrade geldi",
             "stocktwits", SourceType.SOCIAL,
             Author("trader_jane", "stocktwits", followers=2100, following=300,
                    account_age_days=1500, post_count=5000, has_avatar=True, has_bio=True),
             120, 75),
            ("$NVDA bullish breakout, strong buy, rekor gelir",
             "stocktwits", SourceType.SOCIAL,
             Author("techbull", "stocktwits", followers=800, following=250,
                    account_age_days=1100, post_count=2000, has_avatar=True, has_bio=True),
             90, 40),
            ("Garanti BBVA temettü açıkladı, hisse primli",
             "kap", SourceType.DISCLOSURE,
             Author("KAP", "kap", verified=True), 0, 200),
        ]
        records = []
        for text, source, stype, author, eng, mins in rows:
            records.append(Record(
                source=source, source_type=stype, text=text,
                created_at=now - timedelta(minutes=mins),
                author=author, engagement=eng,
                url=f"https://example.com/{random.randint(1000,9999)}",
            ))
        return records
