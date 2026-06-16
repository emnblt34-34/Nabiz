# Borsa Hareketleri Ne Kadar Öngörülebilir? Sızıntısız, Para-Nötr, Çoklu-Test-Düzeltmeli Bir Sınama

**Çalışma taslağı (v1) — 2026-06-15.** Bir Claude Code (Opus 4.8) deneyi. Tüm kod ve
sonuçlar tekrarlanabilir: github.com/emnblt34-34/Nabiz · ham günlük: [sonuclar.md](sonuclar.md) ·
önceden-kayıt: [on-kayit-protokol.md](on-kayit-protokol.md).

> **Not (taslak):** Bu, biriken dürüst sonuçların makale formuna ilk konsolidasyonudur.
> Sayılar `scripts/run_*` ile tekrar üretilebilir.

---

## Özet (Abstract)

BIST ve ABD hisselerinden oluşan bir evrende, kısa-orta vadeli getiri **öngörülebilirliğini**,
*kâr değil ölçüm* amacıyla, sızıntısız ve çoklu-test-düzeltmeli bir protokolle sınıyoruz.
Bulgularımız: **(1)** Saatlik yön tahmini etkin-piyasa ile uyumlu — örnek-dışı (OOS) öngörü
yok (IC≈0.005, p=0.35); naif bir kurguda görünen edge'in ~%80'i veri sızıntısıydı. **(2)**
Günlük/aylık ufukta **kesitsel momentum** ölçülebilir bilgi taşıyor (OOS IC≈0.069, p=0.001),
ama sinyal **yönsel değil görelidir** (tek-hisse yönü değil, sıralama). **(3)** Rejim koşullama
(Hurst/efficiency-ratio) edge'i güçlendiriyor. **(4) Metodolojik kritik bulgu:** TL-bazlı
"güçlü" sonuç büyük ölçüde **TRY enflasyonu artefaktıydı**; para-nötr (USD) denomine edilince
yakın-dönem edge kayboluyor — gerçek edge ZAYIF. **(5)** Bir haber/dikkat proxy'si (hacim-olay)
edge'i anlamlı iyileştiriyor (DSR 0.865→0.935). **(6)** Bu zayıf edge **27 yıl (1999-2026)
boyunca dayanıklı** (4/4 alt-dönem pozitif, bootstrap Sharpe alt-sınırı +0.26). **Sonuç: borsa
"yüksek oranda" değil; ZAYIF, KOŞULLU, para-nötr ve DAYANIKLI biçimde öngörülebilir.** Strict
çoklu-test eşiğinin (Deflated Sharpe>0.95) kıl payı altındayız (0.935). Asıl katkı, popüler
"öngörülebilirlik" iddialarının çoğunu çürüten ve kendi artefaktını yakalayan **metodolojidir**.

---

## 1. Giriş ve Tez

**Soru:** Borsa hareketleri öngörülebilir mi, ne ölçüde? İddiamız iddialı ama yöntemimiz
acımasızca dürüst: *"Profesyonel bir ekonomist gibi düşün, bir istatistikçi gibi kanıtla."*
Bu çalışma para/işlem amacı taşımaz; tek hedef öngörülebilirliğin **dürüst ölçümü** ve
çoğu sistemde gizli kalan yöntem hatalarının (sızıntı, çoklu-test, para-artefaktı,
overfit) açığa çıkarılmasıdır.

**Hipotezler (önceden-kayıtlı, falsifiable — [on-kayit-protokol.md](on-kayit-protokol.md)):**
- **H1.** Çok-ölçekli momentum (1-12 ay) forward-return ile permütasyon-null üstünde anlamlı IC taşır.
- **H2.** Rejim koşullama edge'i koşulsuzdan anlamlı güçlendirir.
- **H3.** Ham teknik indikatörler (MA/MACD/saatlik) baseline üstünde değer KATMAZ.
- **H4.** Sinyal yönsel-zamanlama değil KESİTSEL'dir.
- **H5.** Edge çoklu-test-düzeltmeli (Deflated Sharpe) ve otokorelasyon-dayanıklı (bootstrap) anlamlıdır.

## 2. Veri ve Evren

9 BIST + 7 ABD hissesi (canlı sistem); öngörülebilirlik backtest'i için ABD tarafında
yfinance ~1999'a kadar günlük veri sağlar. Fiyat: yfinance (saatlik 60m + günlük 1d).
Duygu/haber: Reddit/StockTwits/RSS/KAP (canlı toplanır — geçmişe dönük yok). Para-nötrleme:
BIST kapanışı USDTRY ile USD'ye çevrilir.

**Evren yapısı (gerçek ölçüm):** 16 araç efektif olarak **~5 bağımsız riske** denk (ENB≈4.9);
BIST içi tek baskın faktör (bankalar 0.7-0.92 korelasyon), TUPRS doğal hedge, çapraz-pazar
korelasyon düşük (~0.20). Bu, istatistiksel gücü ~3× abartmamak için kritik (efektif N=5).

## 3. Metodoloji

Her "edge" iddiası şu üçlüden geçmeden kabul edilmez:
1. **Örnek-dışı (OOS):** purged + embargoed walk-forward CV (`evaluation/validation.py`).
   Model her fold'un yalnız geçmiş diliminde fit edilir; etiket ufku kadar purge+embargo.
2. **Null'a karşı:** buy&hold, random-sign, permütasyon + **block-bootstrap** (otokorelasyon).
3. **Çoklu-test düzeltmeli:** **Deflated Sharpe Ratio** (Bailey-López de Prado), n_trials grid
   {3,7,22} şeffaf; önceden-kayıtlı n_trials=7.

**Sinyalden portföye:** öngörü gücünü piyasa-yönünden izole etmek için **kesitsel long-short**
(rank → dolar-nötr + ters-vol; `portfolio/`). Para-nötrleme (USD) ile pazarlar ortak birimde.
**Dayanıklılık:** alt-dönem Sharpe + bootstrap Sharpe CI (`evaluation/robustness.py`).

## 4. Sonuçlar (aşamalı)

| Aşama | Soru | Sonuç |
|---|---|---|
| 0 | Saatlik teknik tahmin? | **Yok.** OOS IC=0.005, p=0.35. (Sızıntılı in-sample 0.0248'in ~%80'i sızıntı.) |
| 2 | Günlük momentum bilgi taşır mı? (H1) | **Evet.** OOS IC=0.069, **p=0.001**; yapı teori-tutarlı (1-ay reversal + 12-ay momentum). |
| 2 | Yönsel mi kesitsel mi? (H4) | **Kesitsel.** Yön buy&hold'u geçmez; market-nötr L/S Sharpe 0.78. |
| 3 | Rejim koşullama? (H2) | **Güçlendirir.** L/S DSR 0.51→0.79 (rejim-kör benchmark değişmez). |
| 6 | Para-artefaktı? | **KRİTİK:** TL-5y "DSR 0.912" büyük ölçüde TRY enflasyonu. USD-5y edge ~0; USD-16y Sharpe 0.45, p=0.006. |
| 7 | Haber/olay kanalı? | **Gerçek.** Hacim-olay proxy DSR 0.865→**0.935**, p 0.0065→0.0020. |
| 8 | Stabil mi / overfit mi? | **STABİL.** 4/4 alt-dönem pozitif (1999-2026); bootstrap Sharpe p05=+0.26. |
| 0/3 | Ham indikatörler değer katar mı? (H3) | **Hayır** (beklendiği gibi) — MA/MACD/saatlik baseline üstünde anlamsız. |

**Nihai konfigürasyon (para-nötr, USD, hacim-olay augmente):** yıllık Sharpe ≈ **0.52**,
bootstrap p=0.002, **DSR(7)=0.935** (n=3'te 0.980, n=22'de 0.828), 1536 örtüşmesiz rebalans.

## 5. Öne Çıkan Metodolojik Bulgu — Para Artefaktı

Çalışmanın en öğretici sonucu: çoklu-aşama boyunca "neredeyse-ispatlı" (DSR 0.912) görünen
5-yıllık edge, **doğru para birimine çevrilince çöktü.** Karışık (BIST-TL + ABD-USD) kesitte
TRY'nin değer kaybı BIST'i sistematik "kazanan" gösteriyor; momentum bunu skill sanıyordu.
**Para birimine dikkat etmeyen herhangi bir sistem bu sahte edge'i "gerçek" raporlardı.** Bu,
finansal öngörülebilirlik çalışmalarında denomine seçiminin kritikliğine dair somut bir uyarıdır.

## 6. Tartışma

Bulgular **zayıf-form etkin piyasa ile büyük ölçüde uyumlu**: işlem-edilebilir, güçlü bir
öngörü yok. AMA tam etkinlik de reddediliyor: para-nötr, rejim-koşullu, olay-augmente kesitsel
momentum, 27 yıl boyunca **dağılmış, zayıf ama sıfırdan farklı** bir öngörü taşıyor. Bu, "zayıf
ama gerçek ve dayanıklı öngörülebilirlik" tezini destekler; "yüksek oranda öngörülebilir"
popüler iddiasını reddeder. Edge'in zayıflığı (Sharpe ~0.5, IC ~0.05) literatürdeki momentum/
post-event-drift büyüklükleriyle uyumludur.

## 7. Kısıtlar

- **Gerçek duygu/haber geçmişe backtest EDİLEMEZ** (tarihsel veri yok); yalnız hacim-olay
  *proxy*'si ölçüldü. Gerçek duygu/LLM katkısı forward-only ölçülebilir (devam ediyor).
- Strict eşik (DSR>0.95) kıl payı geçilmedi (0.935).
- Tek evren (16 araç, efektif ~5 bağımsız); işlem-maliyeti varsayımları sentetik.
- yfinance veri kalitesi; BIST tarihsel kapsamı ABD'den kısa.

## 8. Sonuç

**Borsa hareketleri YÜKSEK oranda öngörülebilir değildir; ama ZAYIF, KOŞULLU, para-nötr ve
DAYANIKLI biçimde öngörülebilirdir.** Bu sonuca, çoğu sistemde gizli kalan dört tuzağı
(sızıntı, çoklu-test, para-artefaktı, overfit) tek tek ölçerek ulaştık. Asıl katkı, sayıdan
çok **yöntemdir** — ve sistemin kendi yanılgısını (TRY artefaktı) yakalayabilmesidir.

## 9. Tekrarlanabilirlik

```
python -m scripts.run_validation daily   # Stage 0/2: saatlik/günlük OOS
python -m scripts.run_ls_validation 5y   # market-nötr L/S
python -m scripts.run_stage4             # ensemble + DSR grid
python -m scripts.run_stage6 max         # TL vs USD (para artefaktı)
python -m scripts.run_robustness         # Stage 8: dayanıklılık
```

**Devam (forward):** Gerçek duygu/LLM katmanının (sürpriz/olay/nedensel-iletim — dip not #1)
fiyat-ötesi marjinal katkısı; canlı `predictions` günlüğünde A/B; edge'i 0.95 üstüne taşıma denemesi.
