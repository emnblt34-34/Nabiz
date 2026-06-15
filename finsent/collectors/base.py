"""
Toplayıcı arayüzü. Her kaynak BaseCollector'dan türer ve collect() ile
ham Record listesi döner. Pipeline kaynak detayını bilmez, sadece bu arayüzü
çağırır — yeni kaynak eklemek = yeni bir alt sınıf yazmak.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from ..models import Record


class BaseCollector(ABC):
    name: str = "base"

    @abstractmethod
    def collect(self) -> list[Record]:
        """Kaynaktan ham kayıtları çeker. Hata durumunda boş liste döndürmeli."""
        raise NotImplementedError
