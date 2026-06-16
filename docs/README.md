# Geliştirme Rehberi & Dokümantasyon İndeksi

> **Buradan başla.** Bu belge, projenin hedefini, şu anki dürüst durumunu, yol
> haritasını ve nasıl devam edileceğini özetler. Detaylar alt belgelerde.

## Amaç — vizyon ve yöntem

**Vizyon (iddialı).** Teknik göstergelerden **duygu, haber, piyasa psikolojisi ve
makroya**; **ML ve LLM muhakemesine** kadar tüm sinyalleri tek bir motorda birleştiren,
**borsa hareketlerinin öngörülebilir bir yapı taşıdığını bilimsel düzeyde ortaya koyan
uçtan uca bir tahmin mimarisi** kurmak. Saatlik, günlük ve uzun vadede; 9 BIST + 7 ABD
hissesinde, mimari **araç-agnostik** (coin ve yeni enstrümanlar eklenebilir). Profesyonel
bir ekonomistin günlük/aylık/yıllık bakışını, Opus 4.8'in yorumlama gücüyle ölçeklemek.
Nihai çıktı: **yayınlanabilir bir bilimsel makale** ve bir **Claude Code (Opus 4.8) yetenek
deneyi.** Para/işlem hedefi YOK — odak tamamen öngörülebilirliğin kendisinde.

**Yöntem (acımasızca dürüst).** Bu kadar iddialı bir tezin değeri, ancak ispatı kurşun
geçirmezse vardır. "Profesyonel bir ekonomist gibi düşün, bir istatistikçi gibi kanıtla."
Sızıntılı bir kurguda her şey "çalışır" görünür; biz gerçekten ölçüyoruz — çünkü amaç
kendimizi kandırmak değil, **dünyaya ispat etmek.** Her sayı aşağıdaki üçlüden geçmeden
"edge" sayılmaz.

> Not: "TradingView yorumlayan ekonomist" bu mimarinin yalnızca **en temel parçasıdır**;
> üstüne LLM, psikoloji, haber-etkisi ve portföy katmanları gelir. Uçları kovalıyoruz —
> ama her adımı ölçerek.

## Temel ilke — DÜRÜSTLÜK
Ham "backtest kârlı" **kanıt değildir.** Her sayı şu üçlüden geçmeden iddia edilmez:
1. **Örnek-dışı (OOS)** — purged + embargoed walk-forward CV (`finsent/validation.py`).
2. **Null'a karşı** — buy&hold / random-sign / permütasyon (`finsent/benchmarks.py`).
3. **Çoklu-test düzeltmeli** — Deflated Sharpe / PBO / SPA-FDR (Stage 1, henüz yok).

## Şu anki dürüst durum (2026-06-15)
- **Stage 0 tamam.** Sızıntı kapatıldı (`backtest._pool` in-sample optimizmi). Saatlik model
  dürüst OOS: **IC≈0.005, p=0.35 → saatlik öngörü YOK** (eski IC 0.0248'in ~%80'i sızıntıydı).
- **Stage 2 tamam — İLK ANLAMLI SİNYAL.** Çok-ölçekli momentum (günlük, 1-12 ay) ile dürüst OOS:
  **IC=+0.069, permütasyon p=0.001 → günlük/momentum ufkunda ölçülebilir, teori-tutarlı (1-ay
  reversal + 12-ay momentum) öngörülebilirlik VAR.** Ama yön isabeti drift'i (buy&hold %53.7)
  geçmiyor → sinyal **kesitsel/rank** nitelikli; market-nötr long-short ile hasat edilmeli.
  Nüans + dürüstlük uyarıları: [sonuclar.md](sonuclar.md).
- **Stage 1 + Kesitsel L/S tamam.** Sinyali market-nötr hasat ettik: 5y'de **L/S Sharpe=0.78,
  p=0.032, DSR=0.51** (<0.95) → robust ispat eksikti.
- **Stage 3 tamam — REJİM KOŞULLAMA edge'i GÜÇLENDİRDİ.** Trend-geçitli momentum (`signals/regime.py`:
  Hurst/Efficiency-Ratio) ile aynı 5y veride L/S: **Sharpe 0.78→1.14, p 0.032→0.0055, DSR 0.51→0.79**
  (rejim-kör benchmark değişmedi → fark gerçek model katkısı). **Hâlâ <0.95 ama ispat eşiğine en çok
  yaklaştığımız nokta.** (Per-ticker yönsel IC kötüleşti → sinyal kesitsel, yönsel değil.)
- **Stage 4 tamam — SINIRDA.** Çok-ufuk ensemble **reddedildi** (seyreltti: Sharpe 1.14→0.74). Önceden-kayıtlı
  protokol ([on-kayit-protokol.md](on-kayit-protokol.md)) + şeffaf DSR grid: tek-ufuk edge **bootstrap p=0.0055 ✓**,
  ama **DSR(n_trials=7)=0.912 ✗** (n=3'te 0.970). **Karar: güçlü ama robust ispat kıl payı eksik — "ispatlandı"
  DEMİYORUZ** (n_trials cherry-pick = p-hacking, yapmıyoruz).
- **Stage 5-6 — KRİTİK DÜRÜSTLÜK DÜZELTMESİ.** Kripto/uzun-geçmiş eşiği geçmedi; ve **Stage 6
  ANA bulgu: yukarıdaki "DSR 0.912" büyük ölçüde TRY ENFLASYONU ARTEFAKTIYDI.** BIST USD'ye
  çevrilince (para-nötr) 5y edge YOK OLUYOR (Sharpe 1.14→0.00, p→0.50). Gerçek para-nötr edge
  ZAYIF: yalnız 16y'de marjinal anlamlı (Sharpe 0.45, p=0.006), son 5y'de yok. Titiz denomine
  **kendi artefaktımızı yakaladı** → projeyi daha güvenilir yapar. [sonuclar.md](sonuclar.md).
- **Stage 7+11 — HABER KANALI + TEST → EŞİK AŞILDI.** Hacim-olay (haber proxy) edge'i güçlendirdi.
  **Stage 11: `tests/` bir ağırlık bug'ı (dolar-nötr DEĞİL) yakaladı; düzeltince edge İYİLEŞTİ ve
  önceden-kayıtlı eşiği AŞTI: DSR(7)=0.963>0.95, p=0.0015, 27y dayanıklı.** İlk kez H5 kriteri
  karşılandı — **zayıf ama önceden-kayıtlı protokolde anlamlı** (n=22'de 0.888, hâlâ sınırda).
  (3-saatlik ufuk ~yazı-tura; dürüst.)
- Çalışan ürün: duygu paneli + **USD-bazlı kesitsel öngörü** (para-nötr, dürüst sicil) +
  3-saatlik rozet (zayıf) — `server.py`.

## Dokümanlar
| Belge | İçerik |
|---|---|
| [**makale.md**](makale.md) | **📄 BİLİMSEL MAKALE taslağı (v1).** 8 aşamanın konsolide bulgusu: "borsa zayıf-koşullu-dayanıklı öngörülebilir; yüksek değil" + para-artefaktı metodolojisi. |
| [strateji-arastirma.md](strateji-arastirma.md) | **Ana strateji.** 10 sinyal ailesi sentezi: taksonomi (strong/mixed/weak), tek-tahmin-motoru mimarisi, ufuk oyun kitapları, bilimsel metodoloji, modül planı, makale taslağı, 8-aşamalı yol haritası, riskler + uzman yorumu. |
| [arastirma-bulgulari.md](arastirma-bulgulari.md) | 10 alanın derin araştırma + adversarial doğrulama detayı (referans, ~160 KB). |
| [sonuclar.md](sonuclar.md) | **Bilimsel günlük.** Her aşamanın dürüst OOS ölçümü (Stage 0→4). |
| [on-kayit-protokol.md](on-kayit-protokol.md) | **Önceden-kayıt (pre-registration).** Hipotezler, sabit özellik seti, n_trials muhasebesi, kabul/red kriteri (DSR(7)>0.95 ∧ p<0.05). |
| [fikirler-dipnotlar.md](fikirler-dipnotlar.md) | Dip notlar: LLM'in rolü (beklenti/nedensel-iletim motoru), portföy korelasyon bulguları. |

## Yol haritası (nerede kaldık)
Tam liste: [strateji-arastirma.md › Yol Haritası](strateji-arastirma.md). Özet:

- **Stage 0 — Temel dürüstlük** ✅ `evaluation/validation.py` (WF-CV) + `benchmarks.py`. Sızıntı kapandı, baseline kuruldu.
- **Stage 2 — Doğru sinyaller (momentum)** ✅ `features.py` çok-ölçekli momentum. Günlük OOS **IC=0.069, p=0.001** — baseline aşıldı. (Kalan: mid-price reversal, gün-içi/overnight, triple-barrier — sonraki tur.)
- **Stage 1 + Kesitsel L/S** ✅ `evaluation/stats.py` + `portfolio/weights.py` + `portfolio/ls_backtest.py`. Market-nötr hasat: Sharpe 0.78, p=0.032, DSR=0.51.
- **Stage 3 — Rejim koşullama** ✅ `signals/regime.py` + trend-geçitli momentum. L/S DSR 0.51→0.79, Sharpe 1.14, p=0.0055.
- **Stage 4 — Ufuk-ensemble + önceden-kayıt** ✅ Ensemble reddedildi (seyreltti). Şeffaf DSR: **p=0.0055 ✓, DSR(n=7)=0.912 ✗ → SINIRDA.** Protokol: [on-kayit-protokol.md](on-kayit-protokol.md).
- **Stage 5 — Veri/araç genişletme** ✅ Kripto seyreltti, `max` TL veri felaketi → naif ölçekleme eşiği geçmedi.
- **Stage 6 — USD-bazlı BIST** ✅ **ANA BULGU:** 5y "DSR 0.912" büyük ölçüde **TRY enflasyonu artefaktıydı**; para-nötr (USD) edge ZAYIF (16y Sharpe 0.45 / p=0.006; son 5y ~0). Titiz denomine kendi artefaktımızı yakaladı. Canlı panel USD'ye geçti.
- **Stage 7 — Haber-etki kanalı (hacim proxy)** ✅ Gerçek sentiment backtest edilemez; ama hacim-olay proxy'si (dikkat/haber) **edge'i iyileştirdi: DSR(7) 0.865→0.935, p 0.0065→0.0020.** Haber/olay kanalı gerçek → duygu hipotezini destekler. Hâlâ <0.95 ama en yakın nokta.
- **Stage 8 — Dayanıklılık** ✅ DSR(7)=0.935 overfit mi? `evaluation/robustness.py`: **4/4 alt-dönem pozitif (27 yıl 1999-2026), bootstrap Sharpe p05=+0.26>0.** **STABİL — fluk değil.** Zayıf-ama-GERÇEK ve dayanıklı edge.
- **Stage 9 — MAKALE** ⏭️ **SIRADAKİ.** Artık dürüst, dayanıklı, tekrarlanabilir bir bulgu var: "borsa zayıf-koşullu-ölçülebilir öngörülebilir; güçlü değil" + artefakt-yakalama metodolojisi + haber-kanalı kanıtı. Yazıma hazır.
- **Paralel:** forward sentiment/LLM ablation (dip not #1) — edge'i 0.95 üstüne taşıma denemesi (ileriye-dönük ölçülür).
- **Stage 3** — Rejim koşullama (`regime.py`: Hurst/ADX/vol).
- **Stage 4** — Meta-model + kalibre confidence (Platt/isotonic, Brier).
- **Stage 5** — Çok-ufuk (günlük/haftalık bar) + çapraz-kesit rank-momentum (`cross_section.py`).
- **Stage 6** — Canlı doğrulama + duygu ablation; LLM özellik katmanı (`llm_features.py`, bkz. dip not #1).
- **Stage 7** — Profesyonel: coin evreni, otomatik re-kalibrasyon, tam dashboard, makale.

## Açık iş kalemleri
- **Stage 2** — sıradaki kodlama (kurulan çizgi: önce geçilecek bir edge bul, sonra Stage 1 ile istatistiksel zırha sok).
- **Portföy mimarisi** — workflow (`portfoy-kurulumu-tasarim`) limit nedeniyle yarım kaldı; gerçek korelasyon bulguları [fikirler-dipnotlar.md › #2](fikirler-dipnotlar.md)'de saklı. Yeniden koşulabilir.

## Nasıl çalıştırılır
```bash
pip install -r requirements.txt

# 1) Canlı panel (duygu + fiyat + öngörü) — http://localhost:8000
python server.py            # Windows'ta UTF-8 için: set PYTHONIOENCODING=utf-8

# 2) DÜRÜST değerlendirme raporu (sızıntılı in-sample vs OOS + null'lar)
python -m scripts.run_validation

# 3) Bilimsel ENTEGRİTE testleri (no-look-ahead, CV purge, ağırlık nötrlüğü)
python tests/test_integrity.py          # ya da: python -m pytest tests/
```

> Entegrite testleri kritiktir: bir kez `cross_sectional_weights`'te dolar-nötrlük bug'ı
> yakalayıp düzeltti — düzeltme edge'i 0.95 eşiğinin üstüne taşıdı (bkz. sonuclar.md Stage 11).

## Mimari (modül haritası)
Domain'lere ayrık, bağımlılığı tek yönlü paket yapısı — **tam harita + yeni modül nereye
girer: [MIMARI.md](MIMARI.md).** Özet katmanlar:
- **Çekirdek:** `config / models / tickers / db`.
- **Veri:** `collectors/` (duygu kaynakları), `prices.py` (yfinance).
- **Duygu hattı:** `sentiment / credibility / aggregate / pipeline`.
- **Tahmin:** `features.py` (fiyat+momentum+duygu), `forecast.py` (kural+ML blend).
- **Bilim — `evaluation/`:** `backtest / validation (WF-CV) / benchmarks / stats (DSR, bootstrap, FDR)`.
- **Portföy — `portfolio/`:** `weights (kesitsel L/S) / ls_backtest`.
- **Arayüz/rapor:** `server.py` + `web/dashboard.html`; `scripts/run_*`.

Kod içi yorumlar Türkçe ve ayrıntılıdır; her modülün başındaki docstring sorumluluğu anlatır.
