# Fikirler & Dip Notlar

Strateji geliştikçe biriken çalışma notları. Her dip not bir fikrin çekirdeğini,
neden yükseltildiğini ve finsent'e nasıl bağlandığını tutar.

---

## Dip Not #1 — LLM'in rolü: "tahminci" değil, **beklenti-farkı & nedensel-iletim motoru**
**Tarih:** 2026-06-15

### Kullanıcının çekirdek fikri
LLM ile geçmiş haberleri ve o haberlerin hisse etkilerini objektif yorumlamak;
doğru bağlam + içerikle haberin hissenin kırılmasına etkisini yapılandırmak.

### Neden "düz" versiyon yetersiz
1. **Sentiment ≠ fiyat hareketi.** Fiyat, haberin tonuna değil, haberin **zaten
   fiyatlanmış beklentiden farkına (sürpriz)** tepki verir. "İyi haber" zaten
   bekleniyorsa fiyat düşebilir. Ham ton gürültüdür.
2. **Hindsight/sızıntı tuzağı (BİLİMSEL OLARAK KRİTİK).** Bir LLM, geçmiş ünlü
   olayların sonrasında ne olduğunu eğitim verisinden **bilir**. Geçmiş haberlerde
   "bu hisseyi nasıl etkiledi" diye sorarsak, model geleceği ezberden sızdırır →
   sahte yüksek isabet. Yani LLM haber-edge'i geçmişe bakarak DÜRÜSTÇE ölçülemez.

### Yükseltilmiş fikir
**LLM'i tahmin ürettirmek için değil, düşük boyutlu YAPILANDIRILMIŞ ÖZELLİKLER
çıkarmak için kullan; sayısal eşlemeyi kuant model öğrensin. LLM dilde iyi,
sayıda kötü — işi buna göre böl.** Haber/filing başına LLM şunları üretir:

- **Surprise (sürpriz) skoru:** olay ne kadar beklenmedik / zaten fiyatlı mıydı.
- **Novelty (yenilik):** gerçekten yeni bilgi mi, eski haberin tekrarı mı
  (metin-hash değil, **anlamsal/naratif** dedup). Tepki yenilikle ölçeklenir.
- **Tipli olay (event taxonomy):** kazanç sürprizi / guidance / M&A / regülasyon /
  yönetim değişikliği / buyback / makro veri / analist aksiyonu... Her tipin
  **büyüklüğü ve ufku LLM'den değil, TARİHSEL event-study istatistiğinden** gelir.
- **Nedensel iletim (causal transmission):** olayı belirli araca **hangi zincirle**
  bağlar (tedarikçi/rakip/emtia/makro). Örn. ham petrol marjı haberi → rafineri
  spreadi → TUPRS. Anahtar-kelime sistemlerinin kaçırdığı **dolaylı** etkileri yakalar.
- **Naratif rejim:** hakim piyasa hikâyesi ("AI capex", "faiz indirimi umudu",
  "BIST dezenflasyon trade'i", "jeopolitik risk-off") ve hangi aracın ona kaldıraçlı
  olduğu. Naratif kayması akıştan önce gelir → yavaş ama güçlü özellik.
- **Kesitsel göreli etki:** "Bu makro haber 16 aracı en olumludan en olumsuza
  sırala." LLM **mutlaktan çok görelide** iyidir; bu çıktı doğrudan long-short
  portföyü besler (portföy workflow'una bağlanır).
- **Doküman-delta:** KAP açıklamaları, bilanço/transcript dili — yıldan yıla
  **dil değişimi** ( "Lazy Prices" etkisi) öngörücüdür. LLM uzun-doküman muhakemesinde
  benzersiz; ton/risk-faktörü/hedge dilindeki kaymayı çıkarır.

### En kritik bilimsel kısıt
LLM haber sinyali **yalnızca İLERİYE dönük (canlı) doğrulanabilir** — tıpkı bizim
`predictions` tahmin günlüğümüz gibi. Yapı: zaman T'de yalnız o an mevcut haberi ver,
ileriye dönük olasılıksal çıktı al, **logla**, ufku dolunca gerçek hareketle eşle.
Geçmiş haber üzerinde backtest **sızıntı yüzünden geçersizdir**; magnitude tarihten,
yön/sürpriz LLM'den, ispat forward-only.

### Ekstra kaldıraçlar (multi-agent ile)
- **Perspektif paneli:** bull / bear / makro / mikroyapı lensli birden çok LLM
  analisti → meta-model birleştirir. **Anlaşmazlık = belirsizlik sinyali** (çekişmeli
  naratif → yüksek volatilite beklentisi). Bizim alt-agent yeteneğimize birebir oturur.

### finsent'e bağlanışı (önerilen modüller)
- `llm_features.py` — haber/filing → yapılandırılmış özellik (surprise, novelty,
  event_type, causal_targets, narrative_tag, cross_sectional_rank). Çıktı `features.py`'a girer.
- `event_study.py` — tipli olayların tarihsel ortalama drift/ufuk tablosu (magnitude kaynağı).
- Forward değerlendirme zaten `predictions` günlüğüyle uyumlu; ayrı bir LLM-sinyal kanalı eklenir.

> Not: Bu fikir, çalışan araştırma workflow'undaki (`wzdnup9e1`) "Duygu & haber
> analitiği (NLP)" alanıyla örtüşüyor; sentez geldiğinde bu dip notla
> harmanlanacak.

---

## Dip Not #2 — Portföy/evren: gerçek korelasyon yapısı (workflow yarım kaldı)
**Tarih:** 2026-06-15

Portföy kurulumu workflow'u (`portfoy-kurulumu-tasarim`, run `wf_eb5828bc-c29`) limit
nedeniyle **tamamlanamadı** — gelecekte sıfırdan tekrar koşulabilir. Ama girdi olarak
hesaplanan **gerçek istatistikler** (16 araç, ~60g saatlik→günlük) değerli, kaybolmasın:

- **Ortalama ikili korelasyon 0.29** — ama dağılım aldatıcı.
- **BIST içi neredeyse tek bir "beta":** AKBNK|GARAN **0.92**, AKBNK|THYAO 0.86,
  KCHOL|THYAO 0.83, GARAN|THYAO 0.79; SISE/EREGL/BIMAS hepsi 0.5–0.8. → 9 BIST hissesi
  **efektif olarak ~2-3 bağımsız bahis.**
- **TUPRS tek gerçek çeşitlendirici:** BIST bankalarıyla NEGATİF (GARAN|TUPRS −0.22,
  AKBNK|TUPRS −0.19).
- **ABD/BIST arası korelasyon düşük (0.1–0.4)** → asıl çeşitlendirme iki pazar ayrımından.
- US kümeleri: AMZN/GOOGL/META ~0.55–0.62; NVDA/TSLA ~0.44.

**Çıkarım (portföy tasarımına):** naif eşit ağırlık portföyü **BIST beta'sına aşırı
yoğunlaştırır**; HRP/kümeleme veya faktör-nötrleştirme gerekir. Profesyonel portföy
mimarisi (HRP+vol-hedef / Black-Litterman / kesitsel long-short turnuvası) bir sonraki
oturumda yeniden ele alınacak — yöntem alanları ve şema `portfoy-kurulumu-tasarim`
workflow script'inde hazır duruyor.

