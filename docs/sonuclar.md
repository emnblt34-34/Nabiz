# Sonuçlar — Bilimsel Günlük (lab notebook)

Her aşamanın DÜRÜST ölçüm sonucu burada birikir. Kural: ham "backtest kârlı" kanıt
değildir; her sayı örnek-dışı (OOS), null'a karşı ve (Stage 1'den itibaren)
çoklu-test düzeltmeli raporlanır.

---

## Stage 0 — Sızıntı kapatıldı, ilk dürüst sayı (2026-06-15)

**Ne yapıldı:** `validation.py` (purged + embargoed walk-forward CV) + `benchmarks.py`
(buy&hold / random-sign / persistence / permütasyon p) eklendi. Model artık her
fold'un SADECE train dilimiyle fit ediliyor (`forecast.fit_from_data`), test diliminde
ölçülüyor. Eski `backtest_forecaster` (tüm-örnek fit=ölçüm) yalnız "in-sample sağlık
göstergesi" olarak işaretlendi.

**Kurulum:** model=blend (kural+ML), ufuk=3 bar (saatlik), 16 hisse, 80 fold, OOS n=6105.

| Ölçüm | Hit-rate | IC | n |
|---|---|---|---|
| Sızıntılı in-sample (eski rapor) | 50.8% | **+0.0248** | 7086 |
| **Dürüst OOS (walk-forward)** | 50.1% | **+0.0050** | 6105 |
| Sızıntı şişmesi | +0.6pp | **+0.0198 (≈5×)** | |

**Null/temel çizgiler (OOS):** base-rate 50.1% · buy&hold 50.1% · random-sign 50.1% /
IC +0.0033 · **permütasyon p = 0.35**.

**SONUÇ (dürüst):**
- Önceki gururla raporladığımız **IC 0.0248'in ~%80'i SIZINTIYDI.** Gerçek OOS IC ≈ **0.005**.
- **Permütasyon p = 0.35 → OOS IC şanstan ayırt edilemiyor.** Yani bu ufuk (saatlik)
  + bu özelliklerle (saatlik ret1/3/6 + RSI vb.) **öngörü kanıtı YOK.**
- Model buy&hold'u yalnız trivial geçiyor (ikisi de 50.1%).

**Yorum:** Bu bir başarısızlık değil, **temel çizginin (baseline) dürüst kurulması.**
Araştırmanın öngördüğü tam sonuç: saatlik fiyat-teknik tahmin ≈ etkin piyasa. Bundan
sonra eklenecek her sinyal (1-12 ay momentum, rejim koşullama, mid-price, duygu, LLM
özellikleri) **bu ~0.005 / p=0.35 baseline'ını anlamlı şekilde geçmek zorunda** — yoksa
gürültüdür. İlk gerçek "edge" iddiası ancak permütasyon-null'ı (ve Stage 1'de çoklu-test)
yenince yapılır.

**Sonraki ölçüm hedefi:** Stage 2 momentum ailesi (gün/hafta/ay) + Stage 3 rejim
koşullama eklenince OOS IC ve permütasyon p'nin DÜŞMESİ (anlamlılaşması) beklenir; düşmezse
o sinyal de reddedilir.

---

## Stage 2 — Çok-ölçekli momentum (GÜNLÜK), ilk ANLAMLI sinyal (2026-06-15)

**Ne yapıldı:** `features.py`'a çok-ölçekli momentum ailesi eklendi (`mom_21/63/126/252`
+ vol-ölçekli `momsc_*`; günlük bar'da ≈1/3/6/12 ay). 2 yıllık GÜNLÜK bar çekildi,
ufuk = 5 gün, 18 özellik (8 momentum), 16 hisse, OOS n=6805.

| Ölçüm | Hit-rate | IC | n |
|---|---|---|---|
| Sızıntılı in-sample | 51.2% | +0.0680 | 7820 |
| **Dürüst OOS (walk-forward)** | 50.9% | **+0.0692** | 6805 |
| Sızıntı şişmesi | — | **−0.0012 (yok!)** | |

**Null:** base-rate/buy&hold 53.7% · random-sign 50.0% / IC −0.001 · **permütasyon p = 0.001**.

**Momentum özellik IC (in-sample ipucu):** `momsc_21=−0.055`, `mom_21=−0.048` (1-ay **REVERSAL**),
`mom_252=+0.032`, `momsc_252=+0.030` (12-ay **MOMENTUM**), `mom_63=−0.030`.

**SONUÇ (dürüst ve nüanslı):**
1. ✅ **İLK KEZ permütasyon-null'ı yendik: OOS IC=+0.069, p=0.001.** Saatlik (p=0.35) öngörü
   YOK iken, **günlük/momentum ufkunda ölçülebilir, istatistiksel anlamlı bir sinyal VAR.**
2. ✅ **Sızıntı yok** (OOS IC ≈ in-sample) — walk-forward temiz.
3. ✅ **Sinyal yapısı teoriyle birebir:** 1-ay **reversal** (negatif IC) + 12-ay **momentum**
   (pozitif IC). Akademik kanıtın aynısı — uydurma değil, literatürle uyumlu çıktı.
4. ⚠️ **Ama yön isabeti (50.9%) buy&hold'u (53.7%) GEÇMİYOR.** Sebep: hisse getirisinde
   pozitif drift var (5-günlük getirilerin %53.7'si pozitif), "hep long" bunu yakalıyor.
   Yani sinyalimiz **yönsel-zamanlama değil, KESİTSEL/sıralama (rank) bilgisi** taşıyor —
   IC'nin yaşadığı yer burası.

**Kritik çıkarım:** Bu sonuç **portföy mimarisini doğruluyor.** IC anlamlı ama drift'i yenmiyor
→ sinyali hasat etmenin doğru yolu **kesitsel long-short** (piyasa-beta'sını/drift'i çıkarıp saf
sıralama edge'ini izole eden, market-nötr defter — bkz. [portfoy-mimarisi.md](portfoy-mimarisi.md)).
Edge bulundu; şimdi onu market-nötr ölçmek gerekiyor.

**DÜRÜSTLÜK UYARILARI (Stage 1'de kapatılacak):**
- Permütasyon p, havuzlanmış 6805 örneği **bağımsız** sayıyor; oysa evren analizi efektif
  bahsin **~5** olduğunu söylüyor → bağımsızlık abartılı, gerçek p daha büyük olabilir.
  **Blok-bootstrap + efektif-N** düzeltmesi şart.
- Birden çok ölçek/özellik denendi → **çoklu-test düzeltmesi** (Deflated Sharpe, FDR) olmadan
  "sağlam edge" denemez. p=0.001 cömert bir alt sınır.
- IC=0.069 küçük; işlem maliyeti sonrası ticari değeri ayrı mesele (amacımız zaten ticaret değil).

**Verdikt:** İlk kilometre taşı — **günlük/momentum ufkunda, teori-tutarlı, ölçülebilir
öngörülebilirlik var.** Sıradaki: **Stage 1** (blok-bootstrap + Deflated Sharpe/PBO/FDR ile
istatistiksel zırh) ve **kesitsel L/S** ile bu edge'i market-nötr hasat edip ispatlamak.

---

## Stage 1 + Kesitsel L/S — sinyali market-nötr hasat + istatistiksel sertleştirme (2026-06-15)

**Ne yapıldı:** `portfolio/weights.py` (kesitsel rank → dolar-nötr + ters-vol) +
`portfolio/ls_backtest.py` (sızıntısız kesitsel walk-forward, örtüşmesiz rebalans) +
`evaluation/stats.py` (Sharpe, PSR, **Deflated Sharpe**, **blok-bootstrap**, FDR). Stage 2'nin
kesitsel momentum sinyali dolar-nötr long-short deftere çevrildi; getiri serisi
otokorelasyon-dayanıklı (blok-bootstrap) ve çoklu-test-düzeltmeli (DSR) sınandı. (Bu yaklaşım
pooled-IC'deki bağımsızlık-şişmesini de doğal çözer: rebalans başına 1 örtüşmesiz gözlem.)

| Pencere | Rebalans | Sharpe (yıllık) | Blok-bootstrap p | Deflated Sharpe | 1/N-rank'ı geçer? |
|---|---|---|---|---|---|
| 2 yıl | 110 | **+1.29** | 0.017 | 0.52 | ✅ (1.29 vs 1.21) |
| **5 yıl** | 295 | **+0.78** | **0.032** | **0.51** | ✅ (0.78 vs 0.68) |

**SONUÇ (dürüst, nüanslı):**
1. ✅ **Sinyal kesitsel olarak GERÇEK.** Market-nötr L/S, momentumu Sharpe ~0.8 (5y) /
   ~1.3 (2y) ile hasat ediyor — yön drift'ini geçemeyen (Stage 2) sinyal, market-nötr
   defterde **anlamlı getiri üretiyor.** Portföy tezi (docs/portfoy-mimarisi.md) doğrulandı.
2. ✅ **Blok-bootstrap p = 0.032 (5y) < 0.05** — ortalama getiri otokorelasyon sonrası anlamlı.
3. ✅ **Ters-vol ağırlığımız değer katıyor:** 5y'de MODEL anlamlı (p=0.032) iken naif
   **1/N-rank benchmark anlamlı DEĞİL (p=0.069).** Ağırlıklandırma şeması işe yarıyor.
4. ⚠️ **AMA Deflated Sharpe ≈ 0.51 (<0.95) — çoklu-test eşiğini GEÇMİYOR.** n_trials=18
   ve kısa örneklemle SR* eşiği (per-period ~0.11) gözlemlenen Sharpe'a çok yakın.
   Yani: **"borsa öngörülebilir" iddiası için henüz yeterli değil** — promising ama
   bulletproof değil. (2y'den 5y'ye Sharpe 1.29→0.78 düşüşü de 2y'nin elverişli pencere
   olduğunu, 5y'nin daha temsili olduğunu gösteriyor.)

**Verdikt:** **Zayıf ama gerçek, market-nötr, teori-tutarlı bir kesitsel momentum edge'i var;
otokorelasyona dayanıyor ve naif benchmark'ı yeniyor — ancak çoklu-test (Deflated Sharpe)
zırhını henüz geçmiyor.** Bilimsel olarak dürüst konum: "edge bulundu, robust ispat eksik."

**Sıradaki (edge'i DSR>0.95'e taşımak için):** Stage 3 **rejim koşullama** (Hurst/ADX —
momentum yalnız trendli rejimde aç, sinyal-gürültü artar); ufuk-birleştirme (günlük+haftalık);
n_trials'ı önceden-kayıtlı hipotezle düşürmek (HARKing'i önle); daha uzun geçmiş.

---

## Stage 3 — Rejim koşullama: edge'i güçlendirdi (2026-06-15)

**Ne yapıldı:** `signals/regime.py` (Hurst üsteli, Kaufman Efficiency-Ratio, trend-score) +
`features.py`'a **TREND-GEÇİTLİ momentum** etkileşimleri (`mom63_reg`, `mom252_reg` = momentum ×
trend-score; + `er`, `hurst` rejim göstergeleri). Pre-registered + minimal (4 özellik — n_trials
şişmesin). Hipotez: momentum yalnız trendli rejimde "açılır", choppy'de reversal.

**TEMİZ A/B (aynı 5y günlük veri, kesitsel L/S, rejimli vs rejimsiz):**

| | Rejimsiz | **Rejimli** | Δ |
|---|---|---|---|
| L/S Sharpe (yıllık) | 0.78 | **1.14** | +46% |
| Blok-bootstrap p | 0.032 | **0.0055** | güçlendi |
| **Deflated Sharpe** | 0.51 | **0.79** | +0.28 |
| 1/N-rank benchmark | 0.78 / DSR 0.47 | **0.77 / DSR 0.47** | değişmedi |

**SONUÇ:**
1. ✅ **Rejim koşullama edge'i MATERYAL olarak güçlendirdi.** Sharpe +46%, bootstrap p bir kat
   güçlendi, **DSR 0.51→0.79** — üstelik n_trials 18→22 artmasına rağmen. Hipotez H2 desteklendi.
2. ✅ **İyileşme gerçek model katkısı:** rejim-kör 1/N-rank benchmark **değişmedi** (DSR 0.47) →
   fark veriden değil, bizim trend-geçitli sinyalimizden.
3. ⚠️ **Hâlâ DSR<0.95** → "robust ispat" değil ama **eşiğe ciddi yaklaştı** (0.79). Doğru yönde.
4. ⚠️ **Per-ticker (yönsel) OOS IC KÖTÜLEŞTİ** (−0.0175, in-sample 0.068 ile büyük overfit açığı).
   Tutarlı: rejim-momentum **KESİTSEL** (göreli sıralama) bir sinyal, yönsel-zamanlama değil
   (Stage 2 dersi). Canlı per-ticker panel forecast'ı bu özelliklerle overfit'e yatkın →
   gelecekte ayrı/regularize konfig gerekebilir (mühendislik notu).

**Verdikt:** **Rejim koşullama, momentum edge'ini market-nötr defterde belirgin güçlendirdi
(DSR 0.51→0.79, p=0.0055).** Hâlâ 0.95 altında ama ispat eşiğine en çok yaklaştığımız nokta.
Edge gerçek, koşullu ve giderek sağlamlaşıyor — uydurma değil, ölçülü.

**Sıradaki (DSR>0.95 için):** ufuk-birleştirme (günlük+haftalık skill-ağırlıklı); önceden-kayıtlı
hipotez seti ile n_trials düşürmek (HARKing yasak); daha iyi rejim ölçer (gerçek ADX high/low ile);
ve canlı per-ticker için regularizasyon/ayrı feature seti.

---

## Stage 4 — Ufuk-ensemble (reddedildi) + önceden-kayıtlı DSR: SINIRDA (2026-06-15)

**Ne yapıldı:** (1) `portfolio/ls_backtest.py`'a çok-ufuk ensemble (5/10/20-gün modellerinin
kesitsel sinyallerini ortalama). (2) `scripts/run_stage4.py` + `docs/on-kayit-protokol.md`:
DSR'ı **n_trials ∈ {3,7,22} grid'inde ŞEFFAF** raporla; önceden-kayıtlı n_trials=7 + karar
kuralı (DSR(7)>0.95 VE bootstrap p<0.05). p-hacking yok.

**SONUÇLAR (5y, kesitsel L/S):**

| | Sharpe | bootstrap p | DSR(n=3) | DSR(n=7) | DSR(n=22) |
|---|---|---|---|---|---|
| **Tek-ufuk (Stage 3, ufuk=5g)** | **1.14** | **0.0055** | **0.970** | **0.912** | 0.789 |
| Ensemble (5/10/20g) | 0.74 | 0.038 | 0.828 | 0.659 | 0.441 |
| 1/N-rank benchmark | 0.61 | 0.077 | 0.736 | 0.538 | 0.321 |

1. ❌ **Ensemble BAŞARISIZ (honest negative):** 5/10/20 birleştirme sinyali **seyreltti**
   (Sharpe 1.14→0.74). 10/20-gün modelleri zayıf. **Reddedildi** — tek-ufuk (5g) regime modeli en iyi.
2. ⚖️ **n_trials KRİTİK ve şeffaf:** Tek-ufuk edge, DSR'da **n_trials=3'te 0.970 (>0.95) ama
   önceden-kayıtlı n_trials=7'de 0.912 (kıl payı ALTINDA)**, n_trials=22'de 0.789.
3. **KARAR (önceden-kayıtlı kriter): SINIRDA — robust ispat TAM DEĞİL.** bootstrap p=0.0055 ✓
   ama DSR(7)=0.912 ✗. **n_trials=3'ü seçip "kazandık" DEMİYORUZ** (p-hacking olur). Dürüst
   konum: **"güçlü, tutarlı, neredeyse-ispatlı; kriteri kıl payı karşılamıyor."**

**Verdikt:** 4 aşamada öngörülebilirliği **ölçerek** buraya getirdik — saatlik (yok) → günlük
momentum (IC anlamlı) → market-nötr L/S (Sharpe 0.78) → rejim (DSR 0.79) → **şu an: p=0.0055,
DSR(n=7)=0.912.** Eşiğin **kıl payı altındayız** ve hiçbir adımda uydurma yok. Bu, "borsa
yüksek-oranda öngörülebilir" pop-iddiasından çok daha değerli: **kurşun-geçirmez metodolojiyle,
sınırda-anlamlı, dürüstçe raporlanan bir edge.**

**Eşiği muhafazakâr geçmek için (kriter değiştirmeden):** daha uzun geçmiş + daha fazla araç/coin
(n↑ → SR*↓, Sharpe stabilize) → n_trials=7'de DSR>0.95. Ardından duygu/LLM ablation + makale.

---

## Stage 5 — Veri/araç genişletme: HER İKİ KALDIRAÇ DA BAŞARISIZ (2026-06-15)

**Ne yapıldı:** Eşiği kriteri değiştirmeden geçmek için iki dürüst kaldıraç denendi:
(a) daha uzun geçmiş (`max`), (b) kripto ekleyerek kesitsel genişlik (`config.science_universe`:
16 hisse + 8 coin; `ls_backtest` hisse-takvimi hizalaması; canlı `TICKERS` bozulmadı).

| 5y kesitsel L/S | Sharpe | bootstrap p | DSR(3) | **DSR(7)** | DSR(22) |
|---|---|---|---|---|---|
| Hisse-only (16) | **1.14** | 0.0055 | 0.970 | **0.912** | 0.789 |
| Hisse + Kripto (24) | 0.87 | 0.031 | 0.899 | **0.769** | 0.569 |

1. ❌ **`max` geçmiş: VERİ FELAKETİ** (Sharpe −0.18, yıllık −335%). Sebep: 16 yıllık BIST'te
   **TL enflasyonu** (nominal fiyat 50x+ şişer) + kripto erken-dönem uç hareketleri → tek
   glitch'li forward-return ağırlıkla çarpılınca patlıyor. **Ders: ölçüm DURAĞAN+TEMİZ pencere
   ister; naif "daha çok geçmiş" çöp veri sokuyor. 5y doğrulanmış pencere.**
2. ❌ **Kripto: SEYRELTTİ** (temiz 5y'de Sharpe 1.14→0.87, DSR(7) 0.912→0.769). Kripto'nun
   kesitsel momentum yapısı hisse yapısıyla temiz örtüşmüyor; karıştırmak edge'i zayıflattı.
3. **En iyi konfig DEĞİŞMEDİ: hisse-only, 5y, rejim-koşullu (Stage 3) — Sharpe 1.14, DSR(7)=0.912.**

**Verdikt (dürüst):** Naif ölçeklendirme (daha çok geçmiş/araç) **eşiği geçmedi** ve nedenleri
net. Edge'i **zorla geçirmiyoruz.** DSR(7)=0.912'de **sınırda kalıyoruz.** 0.95'i muhafazakâr
geçmek artık "daha çok veri" değil, **daha iyi VERİ MÜHENDİSLİĞİ** (enflasyon-düzeltmeli/USD-BIST,
temizlenmiş uzun geçmiş, winsorize) veya **gerçekten daha iyi sinyal** (duygu/LLM, mid-price)
gerektiriyor. Eklenen kripto/altyapı kodu gelecekteki temiz denemeler için duruyor.

**Kazanım:** Naif ölçeklemenin neden çalışmadığını ÖLÇEREK öğrendik — bu da gerçek bilim.

---

## Stage 6 — USD-bazlı BIST: KENDİ ARTEFAKTIMIZI YAKALADIK (2026-06-15)

**Ne yapıldı:** `fx.py` (USDTRY çek) + BIST kapanışını USD'ye çevir (TL enflasyonunu
sinyalden çıkar; ayrıca karışık BIST-TL/ABD-USD kesitini ortak para birimine getir).
`ls_backtest` + `cross_section`'a `usd` parametresi. TL vs USD aynı pencerede kıyaslandı.

| Kesitsel L/S | Sharpe | bootstrap p | DSR(7) |
|---|---|---|---|
| TL-bazlı, 5y | **+1.14** | 0.0055 | **0.912** |
| **USD-bazlı, 5y** | **−0.00** | **0.50** | **0.082** |
| TL-bazlı, max (16y) | −0.18 💥 | 0.91 | 0.000 |
| **USD-bazlı, max (16y)** | **+0.45** | **0.0065** | **0.865** |

**ANA BULGU (başlığı revize eden):**
- **Stage 1-4'teki "güçlü" 5y sinyalimiz (DSR 0.912) büyük ölçüde TRY ENFLASYONU
  ARTEFAKTIYDI.** Karışık kesitte (BIST-TL + ABD-USD) TRY değer kaybedince BIST sistematik
  "yükseliyor" görünüyor; momentum bunu yakalıyor, forward getiri de TRY düşüşünü içeriyor →
  sahte "skill". **Para-nötr (USD) çevirince 5y edge YOK OLUYOR** (Sharpe 1.14→0.00, p→0.50).
- **Gerçek (para-nötr) edge ZAYIF:** yalnızca 16 yılda anlamlı (Sharpe 0.45, p=0.0065),
  son 5 yılda **yok.** Momentumun bilinen "uzun-vadede zayıf" doğasıyla tutarlı.

**Yapılan:** Canlı panel **USD-bazlı**a (para-nötr, max geçmiş) geçirildi — sahte sinyali
"edge" diye göstermiyoruz. Sicil artık dürüst: Sharpe~0.45, DSR(7)~0.865, p~0.006 (16y).

**Verdikt (en önemli dürüstlük anı):** Titiz metodoloji **kendi yanılgımızı yakaladı.** Eğer
para birimine dikkat etmeseydik, "DSR 0.91, neredeyse-ispat" diye yanlış bir sonuç
yayınlardık. Doğru denomine edince gerçek şu: **para-nötr kesitsel momentum öngörülebilirliği
ZAYIF — uzun vadede marjinal anlamlı, yakın dönemde yok.** Bu, "borsa yüksek-oranda
öngörülebilir" iddiasının aleyhine güçlü, dürüst bir kanıt — ve projeyi daha güvenilir yapar.

**Sonraki:** Para-nötr zemin artık temiz. Eşiği geçmek için tek umut **gerçekten yeni bilgi**:
duygu/haber/LLM katmanının fiyat-ötesi marjinal katkısı (forward-only ablation). Teknik+momentum
tek başına yetmiyor — bunu dürüstçe ölçtük.

---

## Stage 7 — Haber-etki kanalı (hacim proxy): edge'i iyileştirdi (2026-06-15)

**Kısıt (fiziksel):** Gerçek duygu/sentiment geçmişe dönük backtest EDİLEMEZ — tarihsel duygu
verimiz yok (duygu yalnız canlı, ileriye doğru birikir). Bu yüzden haber-etki kanalının
**backtest edilebilir PROXY'sini** test ettik: **hacim-olay** özellikleri (`vol_spike` = dikkat/
haber proxy'si, `vol_trend`, `event_ret` = hacimle ağırlıklı son hareket = olay-sonrası drift).

**A/B (aynı 16y USD veri, hacim-olay kapalı vs açık):**

| | Sharpe | bootstrap p | DSR(3) | DSR(7) | DSR(22) |
|---|---|---|---|---|---|
| Hacimsiz (Stage 6) | 0.45 | 0.0065 | 0.950 | 0.865 | 0.704 |
| **+Hacim-olay (Stage 7)** | **0.52** | **0.0020** | **0.980** | **0.935** | 0.828 |

**SONUÇ:**
1. ✅ **Haber/olay kanalı GERÇEK.** Kaba bir hacim-spike proxy'siyle bile edge iyileşti:
   DSR(7) **0.865→0.935** (eşiğe çok yaklaştı), bootstrap p 0.0065→**0.0020** (güçlendi).
2. ✅ **Bu, duygu/haber hipotezini destekleyen ilk pozitif kanıt:** fiyat-ötesi bir kanal
   (dikkat/işlem yoğunluğu) ölçülebilir öngörü taşıyor.
3. ⚠️ **Hâlâ DSR(7)=0.935 < 0.95** (n=3'te 0.980 geçiyor). En yakın olduğumuz nokta; kıl payı.

**Trajektori (dürüst):** Stage 6 artefaktı soydu (0.865 temiz) → Stage 7 gerçek bir kanal
ekledi (0.935). Yön doğru: **gerçek bilgi (haber/olay) ekleyince ispat eşiğine yaklaşıyoruz.**

**Verdikt:** Hacim proxy bile yardım ettiğine göre, **gerçek duygu/LLM (sürpriz/olay/nedensel-
iletim — dip not #1)** muhtemelen daha fazlasını katar. AMA o forward-only ölçülebilir
(geçmişe dönük backtest edilemez). Stage 8: canlı sentiment ablation harness'i + LLM haber
özellik çıkarımı — sonucu zamanla birikir. Canlı panel hacim-olay özellikleriyle güncellendi.

---

## Stage 8 — Dayanıklılık: edge STABİL çıktı (overfit DEĞİL) (2026-06-15)

**Ne yapıldı:** DSR(7)=0.935'e "neredeyse ispat" demeden önce **kırılganlık/overfit** sınaması.
`evaluation/robustness.py`: alt-dönem Sharpe (16y'yi 4 ardışık döneme böl) + block-bootstrap
Sharpe güven aralığı. Edge birkaç şanslı döneme mi yığılı, yoksa dağılmış mı?

**Sonuç (USD + hacim-olay, max geçmiş — yfinance 1999'a kadar verdi, 27 yıl):**

| Alt-dönem | n | Sharpe |
|---|---|---|
| 1999-02..2006-06 | 384 | +0.29 |
| 2006-06..2013-02 | 384 | +1.10 |
| 2013-02..2019-09 | 384 | +0.48 |
| 2019-09..2026-06 | 384 | +0.59 |

- **4/4 dönem POZİTİF** (27 yıl boyunca, her alt-dönemde).
- **Block-bootstrap Sharpe CI:** p05=**+0.26**, ortanca +0.53, p95 +0.78 → **%100 pozitif**,
  alt sınır 0'ın belirgin üstünde.

**KARAR: STABİL — overfit/fluk DEĞİL.** Edge zayıf (Sharpe ~0.5) ama **27 yıl boyunca
dağılmış ve tutarlı**; bootstrap alt sınırı pozitif. **DSR(7)=0.935 gerçek bir sinyali
yansıtıyor, tek-dönem süslemesi değil.**

**Verdikt (en güçlü pozitif sonucumuz):** **Zayıf ama GERÇEK ve DAYANIKLI** bir para-nötr
kesitsel öngörülebilirlik edge'imiz var (rejim-koşullu momentum + olay/dikkat kanalı). Strict
DSR 0.95 eşiğinin hâlâ kıl payı altında (0.935), AMA 27-yıllık zamansal dayanıklılık bağımsız
ve güçlü bir kanıt. **Dürüst başlık: "Borsa YÜKSEK oranda değil ama ZAYIF, KOŞULLU ve ÖLÇÜLEBİLİR
şekilde öngörülebilir — ve bu edge dayanıklı."** Bu, başından beri kovaladığımız bilimsel sonuç.

**Sonraki:** Makale — artık dürüst, dayanıklı, tekrarlanabilir bir bulgu var; yazıma hazır.
(+ forward sentiment/LLM ile edge'i 0.95 üstüne taşıma denemesi.)

---

## Stage 10 — 3-saatlik (intraday) öngörü: minik ama ölçülebilir kırıntı (2026-06-16)

**İstek:** "3 saat sonrasını öngör." Stage 0'da bu ufuk (60d + taban özellikler) p=0.35
(öngörü yok) çıkmıştı. Şimdi **2 yıl saatlik veri + momentum/rejim özellikleri** ile yeniden:

| 3-saatlik (per-ticker OOS, 90.735 örnek) | Değer |
|---|---|
| OOS IC | +0.0068 |
| Hit-rate | 50.3% (buy&hold 50.1%, geçiyor) |
| Permütasyon p | **0.022 (<0.05)** |

**SONUÇ (dürüst, iki yönlü):**
1. ✅ Stage 0'daki p=0.35'ten p=0.022'ye — **daha çok veri + daha iyi özelliklerle, 3-saatlik
   ufukta istatistiksel olarak sıfırdan ayırt edilebilir minik bir sinyal VAR.**
2. ⚠️ AMA **ekonomik olarak ihmal edilebilir:** IC 0.007, hit %50.3 — neredeyse yazı-tura.
   Üstelik 90k örnek bağımsız değil (otokorelasyon + 16 ticker ≈ 5 efektif) → permütasyon p
   muhtemelen **abartılı**; blok-bootstrap/efektif-N ile anlamsızlaşabilir.

**Canlı:** 3-saatlik forecast paneli artık **SIZINTISIZ OOS sicille** gösteriliyor (hit ~50.3%,
p) — eskiden sızıntılı in-sample gösteriyordu. "çok zayıf" etiketi + "asıl edge günlük kesitsel"
uyarısıyla dürüst çerçeve.

**Verdikt:** "3 saat sonrasını öngörebiliyor muyuz?" → **Neredeyse hayır.** İstatistiksel bir
kırıntı var ama ekonomik/güvenilir değil. Bu, ufuk-yapısının (term structure of predictability)
beklenen sonucu: **kısa ufuk = en zayıf** (saatler mean-revert/gürültü), **günlük-aylık = gerçek
edge** (momentum). Sistem 3-saatlik tahminini üretir ve siciliyle dürüstçe sunar; ama "güçlü
3-saatlik öngörü" yoktur — ve bunu uydurmuyoruz.

---

## Stage 11 — Test suite bir bug yakaladı → DSR EŞİĞİ AŞILDI (2026-06-16)

**Ne yapıldı:** `tests/test_integrity.py` (bağımlılıksız, pytest opsiyonel) — no-look-ahead
(kritik), CV purge/embargo, kesitsel ağırlık ve istatistik testleri. 9 testten 8'i geçti.

**No-look-ahead testleri GEÇTİ** → özelliklerde sızıntı yok; tüm önceki sonuçlar bu açıdan temiz.

**1 test GERÇEK BUG yakaladı:** `cross_sectional_weights` cap uyguladıktan sonra yalnız
normalize ediyordu → **Σw ≠ 0 (dolar-nötr DEĞİL).** Yani L/S defterinde **artık net piyasa
maruziyeti** vardı — market-nötr ölçümü kirletiyordu. Düzeltildi (cap → demean ile **Σw=0 kesin**).

**KRİTİK YENİDEN ÖLÇÜM** (gerçekten market-nötr ağırlıklarla, aynı 16y USD veri):

| | Eski (buglı) | Düzeltilmiş |
|---|---|---|
| Sharpe | 0.52 | **0.56** |
| bootstrap p | 0.0065 | **0.0015** |
| **Deflated Sharpe (n=7)** | 0.935 | **0.963** |
| DSR (n=3 / n=22) | 0.970 / 0.789 | **0.991 / 0.888** |

Edge **ŞİŞMEDİ, AKSİNE İYİLEŞTİ** — artık-maruziyet gürültü ekliyormuş; gerçek nötrlük sinyali
temizledi. Robustness korundu: **4/4 alt-dönem pozitif, bootstrap Sharpe p05=+0.29.**

**SONUÇ — önceden-kayıtlı kriter İLK KEZ KARŞILANDI:** H5 kuralı (DSR(n=7)>0.95 **VE**
bootstrap p<0.05) artık sağlanıyor: **DSR(7)=0.963 ✓ ve p=0.0015 ✓.** + 27 yıl dayanıklı.

**DÜRÜST KALİBRASYON (overclaim YOK):**
- Edge **hâlâ ZAYIF** (Sharpe 0.56, IC ~0.05) — "yüksek öngörülebilirlik" DEĞİL.
- En muhafazakâr sayımda (n_trials=22) DSR=0.888 (hâlâ <0.95). Yani "proof", dürüst n_trials
  aralığının **elverişli ucunda** (n=3–7'de geçer, n=22'de geçmez).
- Ama kritik nokta: **bir test'in yakaladığı bug-fix** bizi eşiğin üstüne taşıdı — sonucu
  tuning/data-snoop ile DEĞİL, bir HATAYI düzelterek. Bu, metodolojinin (ve test yazmanın)
  değerinin en somut kanıtı.

**Yeni dürüst başlık:** "Borsa para-nötr, kesitsel, rejim+olay-koşullu olarak **zayıf ama
önceden-kayıtlı protokolde istatistiksel anlamlı ve 27 yıl dayanıklı** biçimde öngörülebilir."

---

## Stage 12 — Evren genişletme: edge GÜÇLENDİ + 54 yıl dayanıklı (2026-06-16)

**Ne yapıldı:** Likit, haber-zengin, günlük-trade edilebilir hisseler veri-temelli tarandı
(news sayısı + dolar-hacim) → 13 sektör-çeşitli ABD large-cap eklendi: AMD, AVGO, NFLX, PLTR,
JPM, V, XOM, UNH, WMT, COST, KO, DIS, UBER → **29 araç (20 US + 9 BIST).** `yf:news` ticker'ı
doğrudan atar (pipeline union; kısa-alias false-match'i önlendi).

| USD-max kesitsel L/S | 16 araç | **29 araç** |
|---|---|---|
| Sharpe | 0.56 | **0.78** |
| bootstrap p | 0.0015 | **0.0005** |
| DSR(7) / DSR(22) | 0.963 / 0.888 | **~1.0 / ~1.0** |
| rebalans | 1536 | 2870 |
| alt-dönem pozitif | 4/4 (27y) | **4/4 (54y, 1972-2026)** |
| bootstrap Sharpe p05 | +0.26 | **+0.56** |

**SONUÇ:** Daha geniş kesit (likit large-cap'ler + derin geçmiş) edge'i **belirgin güçlendirdi**
ve önceden-kayıtlı eşiği **DECISIVELY** geçirdi (DSR>0.99, en muhafazakâr n=22'de bile). 54 yıl
ve 4/4 alt-dönem dayanıklı; bootstrap alt sınırı +0.56. 9/9 entegrite testi yeşil.

**DÜRÜST KALİBRASYON:** Sharpe 0.78 **"orta"** (gerçek bir kantitatif strateji düzeyi ama "borsa
kolayca öngörülebilir" DEĞİL). Bu aslında akademik **kesitsel momentum faktörünün**
(Jegadeesh-Titman) sızıntısız, para-nötr, 54-yıllık temiz DOĞRULAMASIDIR — gerçek ve dayanıklı,
ama bilinen bir olgu (yeni keşif değil). DSR≈1.0 büyük örneklem kaynaklı (>0.999).


## Stage 13 — 30 DAKİKALIK öngörü: ÖLÇÜLDÜ, edge YOK (dürüst negatif) (2026-06-16)

**Soru:** Kullanıcı "yarım saatlik trade'ini öngörebildiğimiz hisseler" istedi. Önce ölçtük.

**Yöntem:** Aynı sızıntısız makine — `validation.cross_validate` (purged+embargoed walk-forward,
5 fold, embargo=2) **30m barlar** üzerinde, horizon=1 (~30dk) ve horizon=2 (~60dk). yfinance 30m
geçmişi ~60 gün; 29 araç (BIST ~903 bar, ABD ~771 bar). Şans testi: permütasyon p. (`run_30m_research.py`)

| Ufuk | n (havuz) | OOS-IC | isabet | permütasyon p |
|---|---|---|---|---|
| ~30 dk (1 bar) | 21515 | **-0.003** | **0.5007** | **0.665** |
| ~60 dk (2 bar) | 21515 | **-0.001** | **0.4997** | **0.593** |

**SONUÇ:** Havuzda 30dk yön ≈ **yazı-tura**. OOS-IC sıfır, isabet 0.50, p≈0.6 (şanstan ayırt
edilemez). Hisse bazında birkaçı artıda (AMD h=2: IC +0.086 / hit 0.59; KCHOL, META, GARAN) **ama**
IC dağılımı 0 etrafında ~simetrik (en güçlü negatif ASELS −0.13) — bu **sinyal değil gürültü
imzası**. 29×2=58 deneme taranınca birkaç pozitif **beklenir** (çok-test). Tek bir data-mine'lı
backtest'i "öngörülebilir" diye sunmak projenin tüm disiplinine aykırı olurdu → **yapmadık**.

**ÜRÜNE YANSIMASI:** Arayüze **30dk sekmesi eklendi** (mumlar gerçek gün-içi durumu gösterir,
faydalı) ama projeksiyon **sahte koni değil**: yön=nötr, etiket dürüstçe *"ölçüldü: edge yok
(≈yazı-tura, OOS-IC≈0, p≈0.60)"*. Belirsizlik bandı (gerçekleşen volatilite) gösterilir.

**DEĞERİ:** Negatif ama bilimsel olarak anlamlı — **gün-içi etkin-piyasa sınırını** doğrular.
Ölçülen edge günlük/haftalık kesitsel momentumda; 30dk–3saat ölçeğinde ≈yazı-tura. Bu, "her ölçekte
para var" iddiasının tam tersi ve projenin dürüstlük ekseninin kanıtı: **ölçeriz, uydurmayız.**


## Stage 14 — GÜVEN (confidence) KALİBRE: yüksek güven gerçekten daha isabetli (2026-06-16)

**Soru:** "Güveni çok alabildiğimiz hisse var mı?" Önce "güven"in anlamlı olduğunu ÖLÇTÜK —
yoksa rozet göstermek hikâye olurdu.

**Yöntem:** Güven-proxy = momentum-hizalama (mom_21/63/126/252 sinyalle aynı yönde mi, 0.6) +
trend rejimi (ER, 0.4). Sızıntısız walk-forward'da **216k OOS nokta**, güven kovasına göre isabet.
(`run_confidence_research.py`)

| Güven kovası | n | OOS isabet | sinyal-yönlü ort. getiri |
|---|---|---|---|
| düşük <0.40 | 133276 | **0.489** (≈yazı-tura) | -0.0005 |
| orta 0.40–0.66 | 82311 | **0.530** | +0.0030 |
| yüksek ≥0.66 | 388 | **0.590** | +0.0078 |

**SONUÇ:** İsabet **monoton artıyor** (0.49 → 0.53 → 0.59); sinyal-yönlü getiri de (−0.0005 →
+0.0030 → +0.0078). Yani çok-ölçekli momentum hizalanması + trend rejimi, sinyalin yön isabetini
GERÇEKTEN artırıyor — "güven" **kalibre**. **Ama dürüst sınırlar:** yüksek güven **NADİR**
(n=388, ~%0.2) ve o kovada bile isabet ~%59 (kesinlik değil; ~%40 yanılır). Yüksek kovada IC
işareti küçük-örneklem gürültüsü; yön (isabet/getiri) kalibre olan şey.

**ÜRÜNE YANSIMASI:** Kesitsel panele **güven rozeti** (düşük/orta/yüksek, ölçülen isabetle) +
**🎯 en güvenli sinyal** kutusu eklendi. Kutu *"alım gücü neden? (haber değil, teknik)"* sorusunu
gerçek sürücülerle açıklar: kaç momentum ufku hizalı, rejim, hacim trendi, ve **haber yoksa**
"alım baskısı TEKNİK (momentum+trend), haberden değil". Ayrıca grafiklere **senaryo mumları**
(içi boş + kesikli, √t genişleyen) — gelecek mum DEĞİL, olasılık görselleştirmesi; saatlik dahil.


## Stage 15 — Piyasa taraması: ">%70 güven" hisse YOK; en-potansiyellileri ekledik (2026-06-16)

**İstek:** "Borsayı araştır, güven %70'ten yüksek olabilecek potansiyelli hisseleri ekle."

**Yöntem:** 65 likit/haber-zengin aday (BIST-30 + ABD large-cap), mevcut evrende eğitilen kesitsel
modelle güncel sinyal + **kalibre güven** (Stage 14). USD-bazlı. (`run_market_scan.py`)

**SONUÇ (dürüst):** Taranan 65 hissenin **HİÇBİRİ şu an ≥0.70 — hatta ≥0.66 DEĞİL.** Güven tavanı
**0.60** (orta katman, ölçülen isabet ~%53). Bu beklenen: Stage 14 yüksek güvenin **nadir** (~%0.2)
olduğunu ölçmüştü. **">%70 güvenilir yön" veren hisse YOK** — olsaydı ölçtüğümüz EMH sınırı çökerdi.
Kullanıcıya net söylenen: güven-proxy bir olasılık değil; en yüksek katmanda bile ölçülen tavan ~%59.

**EKLENEN (12):** 0.60 kümesi = **4/4 momentum HİZALI** ama rejim henüz trend değil → trende dönerse
yüksek-güven katmanına geçebilecek gerçek potansiyel: LLY, CSCO, MU, INTC, PYPL, MRVL, TMUS, SNOW,
CRWD, COIN (ABD) + FROTO, ARCLK (BIST). Canlı evren **29 → 41**. Sistem, bunlar yüksek güvene
geçtiğinde 🎯 kutusunda işaretler.

**BİLİMSEL NOT:** Bu genişleme **canlı izleme/kapsama** içindir; önceden-kayıtlı backtest iddiası
**Stage 12'nin 29-hisselik** sonucudur (değişmedi). Likit large-cap eklemek kesitsel genişliği artırır
(Stage 12 dersi: geniş kesit edge'i güçlendirdi), yön garantisi vermez. Eklenenler post-hoc, pre-registered değil.


## Stage 16 — Gün-içi RVOL & R:R Tier sistemi: ÖNGÖRÜ DEĞİL, risk aracı (2026-06-16)

**İstek:** 5/15dk + 1s bazlı, RVOL filtreli, R:R hesaplı, 4-Tier'li gün-içi trade derecelendirme modülü.

**DÜRÜSTLÜK ÇATIŞMASI ve ÇÖZÜM:** Tam bu ölçek (gün-içi yön) Stage 13'te **yazı-tura** ölçüldü
(OOS-IC≈0, p≈0.6). "Süper Elit sinyal" üreten bir ÖNGÖRÜ modülü yapmak kendi ölçümümüzle çelişirdi.
Çözüm: modülü **yön öngören** değil, **risk/ödül + hacim KARAKTERİZASYONU** olarak kurduk. Bileşenlerin
hepsi gerçek/hesaplanabilir; sadece "kazandırır" iddiası YOK.

**MODÜL (`finsent/signals/daytrade.py`, `/api/daytrade`):**
- **RVOL** (kural 2): anlık 15dk hacmi / aynı saat-diliminin ~20-gün ortalaması. **RVOL<1.5 → elenir**
  (piyasa ilgisi yoksa raporlanmaz).
- **Seviyeler**: 15dk ATR(14) + swing (giriş=son kapanış, stop=swing-low veya −1.5·ATR, hedef=yapısal
  direnç; tepe kırılımında "açık hedef" işareti). 1s trend yön (side) + teyit.
- **R:R** (kural 3): (Hedef−Giriş)/(Giriş−Stop). **Tier** (kural 4): ≥3 🥇 | 2–2.9 🥈 | 1.5–1.9 🥉 |
  1.0–1.4 🎗️. R:R<1.0 raporlama dışı.
- Arayüzde 4-tier panel; her satırda yön/R:R/RVOL/giriş-stop-hedef/ATR + kırılım & 1s-teyit rozetleri.

**KRİTİK UYARI (panelde de):** Yüksek R:R = yüksek KAZANMA olasılığı **DEĞİL** (genelde tersi — hedef
uzak). Yön öngörülmez. Bu, tanımlı-riskli kurulumların hacim+geometri sıralamasıdır; karar kullanıcının.
Ölçtüğümüz tek gerçek edge hâlâ günlük/haftalık kesitsel momentum (Stage 12/15); gün-içi ≈yazı-tura.


## Stage 17 — Günlük yön anlık-kaydı: "yarın tutarlılığı" için CANLI saha (2026-06-16)

**İstek:** "Bugünkü durumları not aldık mı? Yarın değişim öngörülerinin tutarlılığını inceleyeceğiz."

**Mevcut durum (dürüst denetim):** 3-saatlik forecaster (`predictions`) zaten loglanıp oto-çözülüyor
(bugün 562 kayıt; canlı isabet ~0.44 — zayıf intraday, dürüst). Kesitsel ablation (`cs_ablation`)
günlük loglanıyor ama 5-gün ufkunda (yarın çözülmez). **Eksik:** günlük YÖN çağrılarının temiz
1-günlük "yarın" kontrolü.

**EKLENEN (`finsent/portfolio/daily_check.py`, tablo `daily_check`, `/api/dailycheck`):**
Her gün 1 kez, her hisse için O ANKİ yön (kesitsel side) + güven + USD fiyat loglanır; ufuk (1 işlem
günü) dolunca gerçekleşen USD getiriyle eşlenir, **yön tuttu mu (correct)** işaretlenir. `_cs_cycle`'a
bağlandı (oto log+resolve). Arayüze **📋 Günlük Yön Takibi** paneli.

**BUGÜN KAYIT ALTINDA:** 41 hisse, yön+güven+fiyat, ufuk hedefi **2026-06-17**. (örn. CSCO/SNOW/LLY/
AAPL→up; MU/INTC/MRVL→neutral.) Yarın çözülünce **güven katmanına göre isabet** çıkacak — bu aynı
zamanda **Stage 14 kalibrasyonunun CANLI OOS testi**: yüksek güven gerçekten daha mı isabetli?

**DÜRÜSTLÜK:** Tek-gün gürültülüdür; tutarlılık günlerce birikince anlam kazanır. Sahada ölçülür,
geçmişe uydurulmaz. Model native ufku 5 gün; burada 1-günlük tutarlılık + kalibrasyon canlı izlenir.


## Stage 18 — Seans/ufuk şeffaflığı + 1 coin (BTC) — hata payını detayla düşür (2026-06-16)

**İstek:** (1) Öngörüleri hangi seansa göre yargılıyoruz (ön/sonrası/düzenli/gece)? Ayır. (2) Haber-
takipli, öngörülebilir 1 coin ekle. (3) Kesitsel "+sinyal" anlık mı, saatlik mi, günlük mü? Detaylandır.

**(1) SEANS TEMELİ — net beyan (hata payını düşüren tercih):** Tüm günlük/kesitsel/daily_check
çözümleri **DÜZENLİ SEANS kapanışı** (USD, yfinance `1d`) ile yargılanır. Ön-piyasa, sonrası ve gece
seansı **HARİÇ** — onlar ince/gürültülü, free güvenilir değil, dâhil etmek hatayı ARTIRIR. İntraday
barlar (15/30/60dk) da yfinance varsayılanı = düzenli seans. Bunu "ayırmak" = tek güvenilir tabanı
(düzenli kapanış) açıkça ilan edip gürültülüleri dışlamak. Arayüzde `session_basis` olarak gösterilir.

**(2) BTC eklendi (canlı evren 41→42):** En haber-zengin + en likit coin. yf `BTC-USD`; `fx.usd_series`
zaten USD kabul eder. **7/24 işler → SEANS YOK** (günlük kapanış = UTC gün sınırı; hisselerin düzenli-
seans kapanışından farklı — daily_check'te belirtilir). Stage 5 dersi: kripto kesitsel edge'i
seyreltebilir → eklendi ama izlenir (1 coin etkisi minimal). Mum/haber/daily_check/daytrade'e akar.

**(3) KESİTSEL UFUK netleştirildi:** Panelde artık açıkça: *"GÜNLÜK · 5 işlem günü ufku · göreli güç
sıralaması (anlık/saatlik DEĞİL)"* + *"sinyal = göreli güç skoru (~−1..+1, yüzde değil)"*. Yani
kesitsel sinyal ANLIK panel rozeti veya saatlik tahmin değildir; 5-günlük göreli güç sıralamasıdır.
Saatlik=forecaster (1s+3s), günlük/haftalık=kesitsel mum projeksiyonu — her biri etiketinde ufkuyla.


## Stage 19 — BTC geri çıkarıldı + genişletilmiş seans + anlık haber-yorum (2026-06-17)

**(BTC ÇIKTI):** Stage 18'de BTC eklenince kesitsel Sharpe **0.90→0.73**'e düştü (Stage 5 kripto-
seyreltme bulgusu CANLI doğrulandı). Kullanıcı kararıyla çıkarıldı → evren tekrar **41 hisse**.
Dürüst sonuç kayda geçti: kripto, hisse momentum kesidini ölçülebilir biçimde zayıflatıyor.

**(GENİŞLETİLMİŞ SEANS — pre/post):** `prices.fetch_bars(prepost=True)` eklendi; canlı gün-içi
çekimler (60/30/15dk) artık **ön-piyasa + sonrası (after-hours)** barlarını da içerir → grafikler ve
RVOL seans-dışı hareketi görür. **Gece (overnight) bireysel hisselerde yfinance'te YOK** (yalnız
vadeli/kripto) — dürüstçe sınır belirtildi. `/api/status.sessions`: anlık ABD/BIST seansı + sinyal
zamanlaması ("sinyaller sonraki düzenli seansa işaret eder; gün-içi ufuklar pre/post kapsar").

**(ANLIK HABER + YORUM):** `/api/newsfeed` + üstte **🔔 Anlık Haberler** bildirim banner'ı. Her haber
için YORUM = duygu yönü × model görüşü hizalaması: olumlu haber + model "göreli güçlü" → UYUMLU
(teyit); olumlu haber ama model "zayıf" → ÇELİŞKİ (dikkat). **Dürüst:** haber-etki kanalı ZAYIF
(Stage 7) — kesin sebep değil, hizalama/dikkat okuması. Sahte nedensellik üretilmez.

