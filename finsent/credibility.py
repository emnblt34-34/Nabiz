"""
Hesap kredibilite / bot skorlayıcı.

Tasarım ilkesi: "100 takipçiden az" ile "bot" AYNI ŞEY DEĞİL.
  - Botlar takipçi satın alabilir → düşük takipçi zayıf bir sinyaldir, tek başına yetmez.
  - Gerçek bireysel yatırımcıların çoğu zaten <100 takipçilidir ve ölçmek
    istediğimiz "retail sentiment" tam olarak onlardır.

Bu yüzden hard-cut yapmıyoruz. Her yazara 0..1 arası bir GÜVEN skoru veriyoruz;
düşük skorlu hesap silinmez, sentiment'teki AĞIRLIĞI düşer. Skor, birden çok
sinyalin ağırlıklı birleşimidir. Her sinyal "bot olma ihtimali"ni (0=insan,
1=bot) tahmin eder; sonda 1 - bot_olasılığı = kredibilite.

Sinyaller kasıtlı olarak şeffaf ve ayarlanabilir — kara kutu ML değil. İleride
etiketli veriyle bir sınıflandırıcıya geçebilirsin; arayüz aynı kalır.
"""
from __future__ import annotations

from dataclasses import dataclass
from .models import Author


@dataclass
class CredibilitySignals:
    """Açıklanabilirlik için: her sinyalin katkısını ayrı ayrı tutar."""
    follower_ratio: float = 0.0      # takip/takipçi dengesizliği
    low_followers: float = 0.0       # düşük takipçi (zayıf sinyal, düşük ağırlık)
    young_account: float = 0.0       # yeni hesap
    high_frequency: float = 0.0      # aşırı paylaşım frekansı
    empty_profile: float = 0.0       # avatar/bio yok
    bot_probability: float = 0.0     # birleşik
    credibility: float = 1.0         # 1 - bot_probability, sınırlandırılmış

    def explain(self) -> str:
        parts = []
        if self.follower_ratio > 0.3: parts.append("takip/takipçi dengesiz")
        if self.young_account > 0.3:  parts.append("yeni hesap")
        if self.high_frequency > 0.3: parts.append("aşırı paylaşım")
        if self.empty_profile > 0.3:  parts.append("boş profil")
        if self.low_followers > 0.3:  parts.append("düşük takipçi")
        return ", ".join(parts) if parts else "temiz"


# Her sinyalin birleşik bot olasılığına katkı ağırlığı. Toplamları ~1.
# "low_followers" bilerek DÜŞÜK ağırlıklı: retail yatırımcıyı cezalandırmamak için.
WEIGHTS = {
    "follower_ratio": 0.30,
    "young_account":  0.25,
    "high_frequency": 0.25,
    "empty_profile":  0.12,
    "low_followers":  0.08,   # en zayıf sinyal
}


def _follower_ratio_signal(a: Author) -> float:
    """5000 takip / 30 takipçi → klasik bot. Oran yükseldikçe sinyal artar."""
    if a.followers is None or a.following is None:
        return 0.0
    if a.following < 50:
        return 0.0
    ratio = a.following / max(a.followers, 1)
    # ratio 1 civarı normal; 10+ güçlü bot sinyali. 1..10 arasını 0..1'e ölçekle.
    return min(max((ratio - 1) / 9, 0.0), 1.0)


def _low_followers_signal(a: Author) -> float:
    """<100 takipçi: zayıf sinyal. Lineer, 0 takipçide max 1, 100'de 0."""
    if a.followers is None:
        return 0.0
    if a.followers >= 100:
        return 0.0
    return (100 - a.followers) / 100


def _young_account_signal(a: Author) -> float:
    """Yeni + aktif hesap şüpheli. <30 gün güçlü, 30-180 azalan sinyal."""
    if a.account_age_days is None:
        return 0.0
    if a.account_age_days >= 180:
        return 0.0
    if a.account_age_days < 30:
        return 1.0
    return (180 - a.account_age_days) / 150


def _high_frequency_signal(a: Author) -> float:
    """Günde çok yüksek post ortalaması = otomasyon. >50/gün max."""
    if a.post_count is None or a.account_age_days is None or a.account_age_days < 1:
        return 0.0
    per_day = a.post_count / a.account_age_days
    if per_day <= 10:
        return 0.0
    return min((per_day - 10) / 40, 1.0)


def _empty_profile_signal(a: Author) -> float:
    """Avatar yok + bio yok = bot eğilimi. Her biri 0.5 katkı."""
    score = 0.0
    if a.has_avatar is False:
        score += 0.5
    if a.has_bio is False:
        score += 0.5
    return score


def score_author(a: Author) -> CredibilitySignals:
    """
    Bir yazarın kredibilitesini hesaplar.
    Doğrulanmış (verified) hesap için bot olasılığını sıfırlamaya yakın indirir.
    """
    s = CredibilitySignals()
    s.follower_ratio = _follower_ratio_signal(a)
    s.low_followers  = _low_followers_signal(a)
    s.young_account  = _young_account_signal(a)
    s.high_frequency = _high_frequency_signal(a)
    s.empty_profile  = _empty_profile_signal(a)

    bot_p = (
        WEIGHTS["follower_ratio"] * s.follower_ratio +
        WEIGHTS["young_account"]  * s.young_account +
        WEIGHTS["high_frequency"] * s.high_frequency +
        WEIGHTS["empty_profile"]  * s.empty_profile +
        WEIGHTS["low_followers"]  * s.low_followers
    )

    if a.verified:
        bot_p *= 0.2   # doğrulanmış hesap büyük olasılıkla gerçek

    s.bot_probability = min(max(bot_p, 0.0), 1.0)
    # Kredibilite tabanı 0.1: hiçbir hesabı tamamen 0'a indirme (ağırlığı kalsın).
    s.credibility = max(0.1, 1.0 - s.bot_probability)
    return s


if __name__ == "__main__":
    samples = {
        "klasik bot":   Author("bot1", "x", followers=12, following=4800,
                               account_age_days=9, post_count=2200,
                               has_avatar=False, has_bio=False),
        "retail birey": Author("ahmet", "x", followers=43, following=180,
                               account_age_days=900, post_count=600,
                               has_avatar=True, has_bio=True),
        "kurumsal":     Author("haberajansi", "x", followers=50000, following=120,
                               account_age_days=3000, post_count=40000,
                               has_avatar=True, has_bio=True, verified=True),
    }
    for name, a in samples.items():
        s = score_author(a)
        print(f"{name:14} cred={s.credibility:.2f}  bot_p={s.bot_probability:.2f}  [{s.explain()}]")
