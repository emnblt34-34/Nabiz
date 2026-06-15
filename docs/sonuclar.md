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
