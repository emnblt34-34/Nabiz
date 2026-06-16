# Nabız — Bilgisayarda Kurulum (Gerçek Veri)

Bu sürüm bilgisayarında çalışır, **gerçek kaynakları** (Reddit, StockTwits,
RSS haber, KAP) tarar, **ham yorumları** ve **bot/güven filtresini** uygular,
geçmişi saklar (gerçek momentum) ve telefonundakine benzer Nabız arayüzünü
kendi sunucusundan gösterir.

## 🔬 Geliştirme & araştırma (bilimsel hat)
Bu proje aynı zamanda iddialı bir araştırma çalışmasıdır: **teknik + duygu + haber +
psikoloji + makro + LLM sinyallerini tek motorda birleştirip, borsa hareketlerinin
öngörülebilir bir yapı taşıdığını bilimsel olarak ortaya koymak** (saatlik/günlük/uzun
vade; araç-agnostik, coin'e açık). Nihai hedef: yayınlanabilir bir makale + Claude Code
deneyi. Yöntem acımasızca dürüst: her edge iddiası OOS + null + çoklu-test'ten geçer.
Geliştiriciler buradan devam etsin: **→ [docs/README.md](docs/README.md)** (vizyon,
dürüst durum, yol haritası, nasıl devam edilir).

Şu anki dürüst durum: **Stage 0 tamam** — sızıntı kapatıldı; saatlik modelin gerçek
örnek-dışı sonucu IC≈0.005 / p=0.35 (henüz öngörü kanıtı yok; **üstüne inşa edilecek
sağlam baseline kuruldu**). Sıradaki: Stage 2 — gerçek kanıt bölgesi olan 1-12 ay momentum
ve mid-price sinyallerini ekleyip bu baseline'ı anlamlı geçmek. Dürüst ölçüm:
`python -m scripts.run_validation`.

## Kurulum — 3 adım

### 1) Python kur (bir kez)
Bilgisayarında Python yoksa: https://www.python.org/downloads → indir, kur.
Kurulumda Windows'ta **"Add Python to PATH"** kutusunu işaretle.

### 2) Başlat
- **Mac:** `basla-mac.command` dosyasına çift tıkla.
  (İlk seferde "geliştirici doğrulanamadı" derse: sağ tık → Aç.)
- **Windows:** `basla-windows.bat` dosyasına çift tıkla.

Script gerekli paketleri otomatik kurar ve sunucuyu başlatır.

### 3) Aç
Tarayıcıda:  **http://localhost:8000**

İlk veri toplama 1-2 dakika sürebilir; arayüz kendi kendine dolar ve dakikada
bir tazelenir. Durdurmak için terminal penceresinde **Ctrl + C**.

## Telefondan açmak (aynı wifi)
Bilgisayar ve telefon aynı wifideyse, telefonun tarayıcısına bilgisayarın yerel
IP'sini yaz: **http://BILGISAYAR-IP:8000**
- IP'yi bulmak — Mac: Sistem Ayarları → Wifi → Detaylar. Windows: `ipconfig` → IPv4.
- Örnek: `http://192.168.1.42:8000`

## Ne görürsün
- Hisse kartları: ağırlıklı duygu + momentum + içerik sayısı
- Karta dokun → **gerçek haberler ve yatırımcı yorumları**, kaynak türüne göre
  ayrı (📰 haber / 💬 retail), her yorumun **güven skoru** (bot ağırlığı)
- Günlük analiz özeti, piyasa nabzı göstergesi, BIST/ABD filtresi
- **Öngörü rozeti** (🔮): her hisse için gün içi (~3 saat) yön tahmini + güven

## Öngörü (gerçek öngörü katmanı)
Panel sadece geçmişi özetlemez; **gün içi yön öngörüsü** de üretir. "Gerçek"
olması için üç parça birlikte çalışır:
1. **Gerçek fiyat** — yfinance'ten saatlik barlar (US doğrudan, BIST `.IS` ile).
2. **Model** — duygu + momentum + fiyat-teknik özelliklerinden **şeffaf kural**
   (ağırlıklar fiyat geçmişiyle kalibre) + opsiyonel **ML** (scikit-learn) üst
   katmanı. İkisi blend'lenir; scikit-learn yoksa kural tek başına çalışır.
3. **Dürüst sicil** — model fiyat geçmişiyle **backtest** edilir (yön isabeti +
   IC) ve her canlı tahmin günlüğe yazılıp ufku dolunca **gerçek hareketle**
   eşlenir. İsabet oranı uydurma değil, ölçülüdür.

> Dürüstlük notu: gün içi yönü teknikten tahmin etmek zordur; backtest çoğu
> hissede ~%50 (yazı-tura) çıkar. Asıl beklenen değer **duygu sinyalinin**
> canlı sicilde zamanla kendini göstermesidir.

API uçları: `/api/forecast` (tümü), `/api/forecast/{sembol}` (detay + backtest +
canlı isabet), `/api/backtest` (tam döküm).

## Duygu kaynakları (sentiment)
Canlı yorum/haber toplanır; panelde her hisse momentum sinyalinin yanında **canlı duygu**
(💬 skor + içerik sayısı) gösterir. Kaynak durumu (bu ortamda ölçülen):
- **StockTwits** ✅ — ABD hisseleri iyi kapsanır (40–560 yorum/hisse).
- **RSS haber** (bloomberght/dunya/ntv/investing/cnbc) — ağırlıkla makro; spesifik BIST
  ticker'ını nadiren anar.
- **Reddit** ⚠️ — yetkisiz `.json` 403 bloklu. BIST duygusu (r/borsa, r/BorsaIstanbul) için
  **ücretsiz Reddit app** aç (reddit.com/prefs/apps → "script"), sonra ortam değişkenlerini ver:
  `set REDDIT_CLIENT_ID=...` ve `set REDDIT_CLIENT_SECRET=...` → collector otomatik OAuth'a geçer.
- **KAP** ❌ — kap.org.tr bu ortamdan ulaşılamadı (resmi BIST açıklamaları).

> Dürüst durum: **ABD duygu zengin; BIST ticker-düzeyi duygu ücretsiz kaynaklardan zayıf**
> (haber makro-odaklı, StockTwits ABD-only). BIST için Reddit OAuth en pratik yol.

## Ayarlar (server.py içinde)
- `REFRESH_MIN` — kaç dakikada bir toplansın (varsayılan 10)
- `RETRAIN_SEC` — öngörü modeli kaç saniyede bir yeniden eğitilsin (varsayılan 6 saat)
- İzlenen hisseler — `finsent/config.py` → `TICKERS`
- Öngörü ufku/aralığı — `finsent/config.py` → `HORIZON_BARS`, `PRICE_INTERVAL`
- İnternetsiz demo için başlat: ortam değişkeni `NABIZ_SAMPLE=1`
  (offline; fiyat/öngörü katmanı bu modda kapalıdır)

## Sık sorunlar
- **"python bulunamadı"** → Python kurulu değil ya da PATH'e eklenmemiş (adım 1).
- **Bir kaynak boş geliyor** → o sitenin ucu değişmiş olabilir; diğer kaynaklar
  çalışmaya devam eder. İlgili collector `finsent/collectors/` altında.
- **Port dolu** → `NABIZ_PORT=8090` ile başka port kullan.

## Mimari (özet)
`collectors/` (Reddit, StockTwits, RSS, KAP) → `pipeline.py` (ticker eşleme →
bot/güven skoru → sentiment → dedup) → `db.py` (SQLite, kalıcı) →
`aggregate.py` (ağırlıklı skor + momentum) → `server.py` (API + arayüz).

Öngörü kolu: `prices.py` (yfinance fiyat barları) → `features.py` (fiyat+duygu
özellikleri) → `backtest.py` (kalibrasyon + gerçek isabet) → `forecast.py`
(kural + ML blend; canlı tahmin günlüğü) → `server.py` (`/api/forecast`).

Detaylı modül açıklamaları için koddaki Türkçe yorumlara bak.

---
**Duygu sinyalidir, yatırım tavsiyesi değildir.**
