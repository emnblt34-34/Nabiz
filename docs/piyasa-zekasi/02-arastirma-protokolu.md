# Araştırma Protokolü

Bu protokol, teknik analiz eğitimlerinden, uzman piyasa yorumlarından, akademik makalelerden ve
pratik trading kaynaklarından gelen bilgiyi projeye dağınık not olarak değil, kodlanabilir ve
sınanabilir bilgi olarak almak için kullanılır.

## Kaynak Tipleri

### Akademik kaynak

Örnek: momentum, reversal, post-earnings drift, volatility clustering, market beta, factor models.

Rolü:

- Kanıt gücü belirler.
- Model girdisi veya validasyon hipotezi üretir.
- Popüler teknik yorumların ne kadar gerçek olduğunu denetler.

### Kurumsal/profesyonel kaynak

Örnek: CFA eğitimleri, yatırım bankası notları, portföy yönetimi materyalleri, piyasa mikro yapısı
dersleri.

Rolü:

- Uzman yorum dilini verir.
- Risk, sektör, makro ve portföy bağlamını güçlendirir.
- Akademik teori ile pratik piyasa okuması arasında köprü kurar.

### Trader eğitimi ve piyasa yorumu

Örnek: teknik analiz eğitimleri, profesyonel trader röportajları, piyasa bültenleri, chart review.

Rolü:

- Sahada kullanılan kavramları toplar.
- Breakout, squeeze, gap, failed move, climax volume gibi uç yapıları sınıflandırır.
- Açıklama motorunun insan gibi konuşmasını sağlar.

Risk:

- Geriye dönük hikaye anlatımı çok yüksektir.
- Mekanik tanım yoksa yanıltıcıdır.
- "Her grafikte çalışan" gibi sunulan şeyler çoğu zaman seçilmiş örnektir.

### Canlı piyasa gözlemi

Örnek: sistemin ürettiği sinyaller, sonrasında oluşan fiyat ve haber tepkisi.

Rolü:

- Yorum şablonlarını gerçek örneklerle rafine eder.
- Forward-only doğrulama sağlar.
- Sentiment ve haber yorumunun en dürüst test alanıdır.

## Her İddia İçin Zorunlu Kart

Her teknik/finansal iddia şu formata indirgenir:

```text
İddia:
Kaynak tipi:
Kanıt gücü:
Geçerli vade:
Geçerli piyasa/rejim:
Yanlış kullanım:
Projede rol:
Gerekli veri:
Ölçüm yöntemi:
Yorum dili:
İnvalidation:
```

Örnek:

```text
İddia:
Hacimli kırılım, hacimsiz kırılıma göre daha ciddidir.

Kaynak tipi:
Pratik teknik analiz + hacim/dikkat literatürü.

Kanıt gücü:
Karışık. Doğrudan "kazandırır" iddiası zayıf; dikkat/haber rejimi göstergesi olarak daha güçlü.

Geçerli vade:
Gün içi ile birkaç günlük aralık.

Geçerli piyasa/rejim:
Likiditesi yeterli hisseler; haber veya volatilite genişlemesi dönemleri.

Yanlış kullanım:
Her yüksek hacmi alış sanmak. Yüksek hacim satış baskısı veya dağıtım da olabilir.

Projede rol:
Yön sinyali değil; kırılımın ciddiyet katsayısı ve yorum gerekçesi.

Gerekli veri:
Fiyat, hacim, ATR, son direnç, endeks getirisi, haber akışı.

Ölçüm yöntemi:
RVOL kovalarına göre kırılım sonrası forward return / failed breakout oranı.

Yorum dili:
"Kırılım hacimle destekleniyor; hareket izlenebilir ama yön teyidi endeks ayrışmasıyla güçlenir."

İnvalidation:
Kırılan seviyenin altına dönüş, hacmin sönmesi, endeks desteklememesi.
```

## Kanıt Seviyeleri

### A: Çekirdek kanıt

Akademik olarak tekrar edilmiş, farklı piyasalarda gözlenmiş, projede doğrudan test edilebilir.

Örnek:

- Çapraz-kesit momentum
- Orta vadeli momentum
- Kısa vadeli reversal
- Volatilite kümelenmesi

### B: Bağlam kanıtı

Doğrudan yön tahmini zayıf olabilir ama rejim, risk veya açıklama için faydalıdır.

Örnek:

- ADX
- ATR
- Bollinger band genişliği
- Hacim artışı
- Endeks beta ayrıştırması

### C: Pratik anlatı

Trader dilinde önemlidir; mekanik tanımı ve OOS testi kurulmadan sinyal olamaz.

Örnek:

- Breakout
- Destek/direnç
- Gap
- Squeeze
- Failed breakout
- Divergence

### D: Spekülatif/uç hipotez

Çalışmaya değer ama kanıtı zayıf veya veri gereksinimi ağırdır.

Örnek:

- LLM ile haber beklenti farkı
- Kurumsal birikim/dağıtım tespiti
- Sosyal medya anlatı dönüşü
- Regime flip erken uyarısı

Bu sınıf özellikle kovalanacaktır; fakat çıktıları "kanıtlandı" diye değil, "yüksek potansiyelli
hipotez" diye etiketlenecektir.

## Araştırma Çıktısının Projeye Giriş Kapıları

Her araştırma bulgusu projeye şu kapılardan biriyle girer:

1. Model girdisi
   Fiyatla ölçülebilir ilişki taşıyan, OOS test edilebilecek özellik.

2. Rejim filtresi
   Sinyalin hangi ortamda geçerli olabileceğini belirleyen koşul.

3. Teyit katsayısı
   Ana sinyalin ciddiyetini artıran veya azaltan bağlam.

4. Risk aracı
   Yön tahmini yapmayan ama stop, hedef, volatilite, risk/ödül veya belirsizlik anlatan yapı.

5. Açıklama etiketi
   Kullanıcıya insan-okur yorum üreten ama doğrudan model ağırlığı almayan kavram.

6. Red listesi
   Sızıntılı, çok belirsiz, mekanik tanımı olmayan veya test edilemeyen kavram.

## Özellikle Kovalanacak Uç Noktalar

Bu çalışma çekingen olmayacak. Aşağıdaki yapılar ayrı ayrı araştırılacak:

- Endeks düşerken güçlü kalan hisse
- Endeks yükselirken geride kalan hisse
- Hacimli kırılım
- Hacimsiz kırılım ve sahte hareket
- Failed breakout
- Volatilite sıkışması sonrası genişleme
- Gap sonrası devam veya kapanma
- Climax volume ve trend tükenmesi
- Haber iyi ama fiyat düşüyor
- Haber kötü ama fiyat yükseliyor
- Yüksek sentiment ama fiyat tepkisiz
- Düşük sentiment ama relatif güç pozitif
- Sektör lideri ve sektör sürüklenen ayrımı
- BIST'te kur etkisiyle sahte güç
- ABD'de endeks/mega-cap beta kaynaklı sahte güç

Bu uç yapılar ürünün en ayırt edici tarafı olacaktır.

