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

