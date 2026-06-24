# Dokümantasyon Mimarisi

Bu klasör, mevcut bilimsel ölçüm dokümanlarından bağımsız ilerler. Mevcut belgeler sonuçları ve
validasyonu anlatır; bu alan ise teknik/piyasa bilgisinin nasıl yorumlanabilir ürüne dönüşeceğini
tasarlar.

## Ana Belgeler

### 00-framing.md

Projenin yeni boyutunu tanımlar:

- Neden sadece indikatör eklemiyoruz?
- Teknik analiz projede hangi role sahip?
- Sinyal, filtre, teyit, risk ve açıklama ayrımı nedir?
- Endeks, hacim ve haber bağlamı neden zorunlu?
- Başarı nasıl anlaşılır?

Bu belge sabit pusuladır. Sonraki tüm belgeler buna bağlanır.

### 02-arastirma-protokolu.md

Finans eğitimleri, uzman yorumları, akademik kaynaklar ve piyasa pratikleri bu projeye nasıl
alınacak sorusunu yanıtlar.

Her kaynak şu şablona zorlanır:

- İddia nedir?
- Hangi vadede geçerli?
- Hangi piyasada anlatılıyor?
- Kanıt tipi nedir: akademik, kurumsal, pratik, anekdotal?
- Sızıntı veya geriye dönük yorum riski var mı?
- Projede rolü ne: sinyal, filtre, açıklama, risk, izleme?
- Nasıl test edilebilir?

### 03-yorum-motoru-tasarimi.md

Ham teknik ve haber verisini kullanıcıya anlatılabilir hale getiren yapıyı tasarlar.

Bu belge şunları tanımlar:

- Yorum atomları
- Karar ağacı
- Endeks bağımlılığı ayrıştırması
- Hacim teyidi
- Haber-tepki matrisi
- Güven ve invalidation dili
- Çıktı formatları

### 04-teknik-sinyal-sozlugu.md

Sonraki aşamada üretilecek ana referans belgedir. Her teknik kavram bir kart olarak yazılır:

- Tanım
- Kullanım rolü
- Vade
- Kanıt gücü
- Yanlış kullanım
- BIST/ABD farkı
- Projede kullanılacağı alan
- Ölçüm önerisi
- Yorum cümlesi örnekleri

Örnek kartlar:

- Relatif güç
- Çoklu momentum hizalanması
- Breakout
- Failed breakout
- Gap
- Squeeze
- Climax volume
- RSI trend rejiminde
- RSI range rejiminde
- MACD histogram ivmesi
- ATR genişlemesi
- Endeks beta ayrıştırması

### 05-endeks-ve-sektor-bagimliligi.md

Hisse yorumunun endeksten ayrıştırılmasını tasarlar:

- Hisse getirisi = endeks beta + sektör etkisi + idiosyncratic hareket
- BIST için XU100/XU030 ve banka/sanayi ayrımı
- ABD için SPY/QQQ/sektör ETF eşleşmeleri
- Relatif güç skorları
- Endekse karşı kırılım
- Endeks düşerken dayanan hisseler
- Endeks yükselirken geri kalan hisseler

Bu belge, yorum motorunun omurgalarından biri olacaktır.

### 06-haber-tepki-matrisi.md

Haberin metinsel yönünden çok, fiyatın habere verdiği tepkiyi yorumlamayı tasarlar.

Temel matris:

| Haber tonu | Fiyat tepkisi | Hacim | Olası yorum |
|---|---|---|---|
| Pozitif | Yükseliş | Yüksek | Haber fiyatlanıyor veya beklenti üstü |
| Pozitif | Düşüş | Yüksek | Haber önceden fiyatlanmış / beklenti altı |
| Negatif | Düşüş | Yüksek | Risk fiyatlanıyor |
| Negatif | Yükseliş | Yüksek | Kötü haber sindirilmiş / short-covering |
| Nötr | Sert hareket | Yüksek | Haber dışı teknik/likidite olayı |

### 07-uzman-yorum-sablonlari.md

Sistemin üreteceği insan-okur yorum kalıplarını toplar.

Amaç "otomatik rapor dili" kurmaktır:

- Güçlü teknik yapı ama zayıf haber teyidi
- Endeks kaynaklı hareket
- Bağımsız relatif güç
- Hacimli kırılım
- Hacimsiz sahte kırılım riski
- Trend devamı
- Trend tükenmesi
- Risk/ödül iyi ama yön kanıtı zayıf
- Haber sonrası bekle-gör

## Çalışma Sırası

1. Framing sabitlenir.
2. Araştırma protokolü yazılır.
3. Teknik sinyal sözlüğü için kaynak toplama başlar.
4. Endeks bağımlılığı ayrı belge olarak açılır.
5. Haber-tepki matrisi ayrı belge olarak açılır.
6. Yorum motoru çıktıları şablonlanır.
7. Bunlardan kod modülü tasarımı çıkarılır.

## Belge Standardı

Her belge şu kurala uyacak:

- Net iddia
- Kullanım rolü
- Kanıt düzeyi
- Yanlış kullanım uyarısı
- Projedeki karşılığı
- Test edilebilirlik

Bu sayede dokümantasyon sadece fikir havuzu değil, ileride kodlanabilir bir ürün sözleşmesi olur.

