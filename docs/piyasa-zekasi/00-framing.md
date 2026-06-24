# Piyasa Zekası Framing

## Ana Tez

Nabız'ın yeni boyutu, teknik göstergeleri çoğaltmak değil; teknik göstergeleri, piyasa bağlamı ve
haber anlatısıyla birlikte yorumlanabilir hale getirmektir.

Bu çalışma şu iddiadan başlar:

> Bir teknik sinyal tek başına bilgi değildir. Bilgi, sinyalin hangi rejimde, hangi endeks
> koşulunda, hangi hacim yapısında, hangi haber akışı sonrasında ve hangi göreli güç davranışıyla
> ortaya çıktığını açıklayabildiğimizde oluşur.

Bu yüzden hedefimiz "RSI al verdi" veya "MACD kesişti" gibi ham kurallar değildir. Hedefimiz,
bir piyasa uzmanının zihinsel kontrol listesini sistematik hale getiren bir yorum katmanıdır.

## Ürünün Dönüşeceği Şey

Bugünkü sistem:

- Fiyat, hacim ve sentiment verisini toplar.
- Momentum ve rejim özellikleri üretir.
- Kesitsel sinyal ve bazı kısa vadeli risk görünümleri çıkarır.
- Sinyalleri dürüstçe ölçmeye çalışır.

Yeni hedef:

- Her sinyalin hangi piyasa hikayesine ait olduğunu sınıflandırmak.
- Endeks, sektör, kur, haber ve hacim etkisini ayrıştırmak.
- Teknik göstergeleri rol bazında kullanmak: sinyal, filtre, teyit, uyarı, açıklama veya risk aracı.
- Kullanıcıya sadece skor değil, neden-sonuç ilişkisi taşıyan yorum vermek.
- Aşırı iddialı durumları özellikle kovalamak: kırılım, başarısız kırılım, hacim patlaması,
  sıkışma, trend tükenmesi, relatif güç ayrışması, haber sonrası drift, endeks karşıtı hareket.

Bu sistemin nihai çıktısı şöyle bir dil olmalıdır:

> Hisse yukarı momentum gösteriyor; ancak hareketin büyük bölümü endeks beta'sından geliyor.
> Relatif güç zayıf, hacim teyidi sınırlı, haber katalizörü yok. Bu nedenle yön sinyali değil,
> endeksle birlikte taşınan izleme sinyali.

Ya da:

> Endeks yatayken hisse relatif güç üretiyor. 1/3/6/12 aylık momentum hizalı, hacim trendi artıyor,
> son haber akışı fiyat tarafından henüz tamamen sindirilmemiş görünüyor. Teknik sinyal bağımsız
> ve yorumlanabilir.

## Çalışmanın Sert İlkeleri

1. Gösterge kutsanmaz.
   Her indikatör önce rolüne indirgenir: ölçer mi, teyit eder mi, filtreler mi, risk mi gösterir?

2. Sinyal ile açıklama ayrılır.
   Bir gösterge fiyatı tahmin etmiyor olabilir ama yine de kullanıcıya piyasa yapısını açıklamada
   değerli olabilir. Örneğin ADX yön vermez; trend kalitesi anlatır.

3. Endeks bağımlılığı ayrıştırılmadan hisse yorumu yapılmaz.
   Bir hissenin yükselmesi tek başına alım baskısı değildir. Endeks de yükseliyorsa beta etkisi,
   endeks yatayken yükseliyorsa relatif güç, endeks düşerken yükseliyorsa özel talep ihtimali vardır.

4. Hacim, teknik sinyalin ciddiyet katsayısıdır.
   Hacimsiz kırılım, zayıf anlatıdır. Hacim patlaması tek başına yön değildir; dikkat, haber veya
   likidite rejimi değişimi göstergesidir.

5. Haber yorumu fiyat davranışından ayrı okunmaz.
   Haber iyi/kötü diye değil, fiyatın habere verdiği tepkiyle anlam kazanır. İyi habere düşen hisse,
   beklenti-üstü/altı ve fiyatlanmışlık açısından farklı yorumlanır.

6. Uç durumlar özellikle aranır.
   Ortalama piyasa davranışı çoğu zaman gürültüdür. En değerli içgörü; sıkışma sonrası genişleme,
   başarısız kırılım, climax volume, endeksten ayrışma, haber sonrası gecikmeli tepki gibi uç yapılarda
   çıkar.

7. Yorum ölçülebilir iz bırakır.
   Her açıklama daha sonra sınanabilir alanlara ayrılır: teknik yapı, endeks katkısı, hacim katkısı,
   haber katkısı, güven seviyesi, invalidation koşulu.

## Teknik Analize Bakışımız

Bu projede teknik analiz üç sınıfa ayrılır:

### 1. Kanıt taşıyan olgular

Bunlar akademik literatürde veya geniş ampirik tekrarlarla daha sağlam görünen yapılardır:

- Çapraz-kesit momentum ve relatif güç
- Orta vadeli trend/momentum
- Kısa vadeli reversal, özellikle doğru mikroyapı filtresiyle
- Volatilite kümelenmesi
- Hacim/dikkat artışı ve olay sonrası drift

Bunlar model girdisi veya çekirdek sinyal adayı olabilir.

### 2. Bağlam ve rejim ölçerler

Bunlar tek başına al-sat sinyali değildir; sinyalin hangi ortamda çalışabileceğini anlatır:

- ADX
- Hurst / efficiency ratio
- ATR ve realized volatility
- Hareketli ortalama eğimi
- Bollinger band genişliği / sıkışma
- Endeks ve sektör trendi

Bunlar filtre, yorum ve güven katmanında kullanılır.

### 3. Pratik piyasa dili araçları

Bunlar traderların ve analistlerin konuşma dilinde güçlüdür ama doğrudan edge iddiası zayıf olabilir:

- Destek/direnç
- Breakout / breakdown
- Gap
- RSI aşırı alım/satım
- MACD kesişimi
- Formasyonlar
- Divergence

Bunlar ham sinyal olarak değil, açıklama ve durum etiketleme katmanında kullanılacaktır. Mekanik
tanımı sızıntısız kurulmadan hiçbir formasyon üretime alınmaz.

## Başarı Tanımı

Bu çalışma başarılı olduğunda Nabız şunu yapabilir:

- "Bu hisse güçlü" demek yerine, gücün kaynağını ayırır: endeks, sektör, relatif güç, haber, hacim,
  momentum veya teknik sıkışma.
- "Tahmin" ile "risk/ödül kurulumu"nu karıştırmaz.
- Teknik analiz göstergelerini rastgele eklemez; her göstergeye rol, vade, kanıt gücü ve invalidation
  koşulu atar.
- Kullanıcıya profesyonel yorum üretir ama her yorumun ölçülebilir bileşenlerini saklar.
- Uç fırsatları arar fakat uç iddiaları ayrıca işaretler: yüksek potansiyel, düşük kanıt, ileriye
  dönük doğrulama gerekli.

## Çalışmanın İlk Büyük Çıktısı

İlk büyük çıktı bir kod modülü değil, şu çerçevenin tamamlanmasıdır:

> Teknik sinyal sözlüğü + endeks bağımlılığı haritası + haber/tepki yorumu + hacim teyidi +
> rejim filtresi + uzman açıklama şablonları.

Bu çerçeve tamamlandığında, sonraki aşamada kod tarafında "yorum motoru"na dönüştürülecektir.

