# Yorum Motoru Tasarımı

Bu belge, ham sinyalleri uzman yorumuna çevirecek katmanın ilk taslağıdır.

## Temel Fikir

Yorum motoru tahmin motoru değildir. Tahmin motoru sinyal üretir; yorum motoru sinyalin neden
önemli veya önemsiz olduğunu açıklar.

Yorum motorunun görevi:

- Sinyalin kaynağını parçalamak
- Destekleyen ve bozan bağlamları göstermek
- Endeks/sector beta etkisini ayırmak
- Haber ve hacim davranışını yorumlamak
- Kullanıcıya "neye dikkat etmeli?" sorusunun cevabını vermek

## Girdi Katmanları

### Teknik yapı

- Momentum hizalanması
- Trend rejimi
- Volatilite rejimi
- Destek/direnç konumu
- Kırılım veya sıkışma
- ATR / risk genişliği
- RSI veya osilatör konumu

### Piyasa bağlamı

- Endeks yönü
- Hisse-endeks relatif getirisi
- Sektör göreli gücü
- Beta etkisi
- BIST için USDTRY ve banka/sanayi ayrımı
- ABD için SPY/QQQ/sektör ETF bağlamı

### Hacim ve dikkat

- RVOL
- Hacim trendi
- Hacim-fiyat uyumu
- Hacimli yükseliş / hacimli düşüş
- Hacimsiz kırılım riski

### Haber ve anlatı

- Haber var/yok
- Haber tonu
- Haber sonrası fiyat tepkisi
- Fiyatlanmışlık belirtisi
- Sentiment-fiyat uyuşmazlığı

### Güven ve risk

- Sinyal güven kovası
- Risk/ödül
- Stop/invalidasyon seviyesi
- Beklenen volatilite
- Sinyalin hangi koşulda bozulacağı

## Yorum Atomları

Yorum motoru uzun metni doğrudan üretmez. Önce küçük yorum atomları üretir.

Örnek atomlar:

```text
technical_trend_positive:
Fiyat çoklu momentum pencerelerinde yukarı hizalanıyor.

relative_strength_positive:
Hisse, endekse göre bağımsız güç gösteriyor.

index_beta_warning:
Hareketin önemli kısmı endeks yönüyle açıklanabilir; hisseye özgü güç sınırlı.

volume_confirmation:
Hacim hareketi destekliyor; sinyalin ciddiyeti artıyor.

volume_divergence_warning:
Fiyat hareketi hacimle teyit edilmiyor; kırılımın sahte kalma riski var.

news_absent:
Belirgin haber katalizörü yok; hareket teknik/akış kaynaklı okunmalı.

news_price_mismatch:
Haber tonu ile fiyat tepkisi uyuşmuyor; beklenti/fiyatlanmışlık kontrol edilmeli.

risk_reward_only:
Kurulumun risk/ödül geometrisi iyi; fakat yön tahmini güçlü değil.
```

Bu atomlar daha sonra bir rapor cümlesine dönüştürülür.

## Karar Sırası

Yorum motoru şu sırayla düşünmelidir:

1. Hangi ufuktayız?
   30dk, 3s, günlük, haftalık aynı dille yorumlanmaz.

2. Sinyal yön mü, relatif güç mü, risk kurulumu mu?
   Kullanıcıya yanlış türde kesinlik verilmez.

3. Endeks aynı şeyi mi yapıyor?
   Endeksle taşınan hareket ile bağımsız hareket ayrılır.

4. Hacim teyit ediyor mu?
   Hacim yoksa sinyal zayıflatılır; yüksek hacimde yön değil dikkat yorumu yapılır.

5. Haber var mı?
   Haber yoksa teknik/akış yorumu; haber varsa fiyat tepkisiyle birlikte yorum.

6. Rejim uygun mu?
   Trend rejiminde momentum, yatay rejimde mean-reversion daha anlamlıdır.

7. İnvalidation nedir?
   Her yorum hangi durumda bozulacağını söylemelidir.

## Çıktı Biçimi

Her hisse için ideal çıktı dört parçalıdır:

```text
Özet:
Teknik yapı:
Bağlam:
Risk / dikkat:
```

Örnek:

```text
Özet:
Yukarı yönlü teknik baskı var; ancak sinyal henüz yüksek güven sınıfında değil.

Teknik yapı:
1/3/6 aylık momentum hizalı, kısa vadeli trend pozitif. Fiyat son sıkışma bölgesinin üstünde
tutunmaya çalışıyor.

Bağlam:
Endeks de aynı yönde olduğu için hareketin bir kısmı piyasa beta'sı olabilir. Hisse endekse göre
ayrışırsa sinyal güçlenir.

Risk / dikkat:
Hacim teyidi sınırlı. Kırılım seviyesi altına dönüş, bu yorumu zayıflatır.
```

## Yasaklı Dil

Yorum motoru şu dili kullanmamalıdır:

- Kesin yükselecek
- Garanti sinyal
- Al/sat tavsiyesi
- Haber iyi, o yüzden yükselir
- RSI düşük, kesin döner
- Hacim yüksek, kesin alım var

Yerine şu dil kullanılmalıdır:

- Sinyal güçleniyor
- Teyit sınırlı
- Hareket endeks kaynaklı olabilir
- Bu yapı izlemeye değer
- Yön kanıtı zayıf, risk/ödül geometrisi iyi
- Haber tepkisi beklenti/fiyatlanmışlık açısından kontrol edilmeli

## İlk Kodlanabilir Sözleşme

İleride yorum motoru şu veri yapısını üretebilir:

```json
{
  "ticker": "THYAO",
  "horizon": "daily",
  "summary_label": "relative_strength_watch",
  "direction_bias": "up",
  "confidence_bucket": "medium",
  "technical": {
    "momentum_alignment": "positive",
    "trend_regime": "trend",
    "breakout_state": "testing_resistance"
  },
  "context": {
    "index_dependency": "moderate",
    "relative_strength": "positive",
    "sector_support": "unknown"
  },
  "volume": {
    "confirmation": "limited",
    "rvol": 1.2
  },
  "news": {
    "catalyst": "absent",
    "interpretation": "technical_flow"
  },
  "risk": {
    "invalidation": "breakout_level_lost",
    "note": "Yön kanıtı hacim teyidi gelirse güçlenir."
  }
}
```

Bu sözleşme henüz nihai değil; araştırma belgeleri geliştikçe olgunlaştırılacaktır.

