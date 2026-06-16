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
- Çalışan ürün: gerçek-zamanlı duygu + saatlik fiyat + öngörü paneli — `server.py`.

## Dokümanlar
| Belge | İçerik |
|---|---|
| [strateji-arastirma.md](strateji-arastirma.md) | **Ana strateji.** 10 sinyal ailesi sentezi: taksonomi (strong/mixed/weak), tek-tahmin-motoru mimarisi, ufuk oyun kitapları, bilimsel metodoloji, modül planı, makale taslağı, 8-aşamalı yol haritası, riskler + uzman yorumu. |
| [arastirma-bulgulari.md](arastirma-bulgulari.md) | 10 alanın derin araştırma + adversarial doğrulama detayı (referans, ~160 KB). |
| [sonuclar.md](sonuclar.md) | **Bilimsel günlük.** Her aşamanın dürüst OOS ölçümü. Şu an: Stage 0. |
| [fikirler-dipnotlar.md](fikirler-dipnotlar.md) | Dip notlar: LLM'in rolü (beklenti/nedensel-iletim motoru), portföy korelasyon bulguları. |

## Yol haritası (nerede kaldık)
Tam liste: [strateji-arastirma.md › Yol Haritası](strateji-arastirma.md). Özet:

- **Stage 0 — Temel dürüstlük** ✅ `evaluation/validation.py` (WF-CV) + `benchmarks.py`. Sızıntı kapandı, baseline kuruldu.
- **Stage 2 — Doğru sinyaller (momentum)** ✅ `features.py` çok-ölçekli momentum. Günlük OOS **IC=0.069, p=0.001** — baseline aşıldı. (Kalan: mid-price reversal, gün-içi/overnight, triple-barrier — sonraki tur.)
- **Stage 1 + Kesitsel L/S** ✅ `evaluation/stats.py` + `portfolio/weights.py` + `portfolio/ls_backtest.py`. Market-nötr hasat: Sharpe 0.78, p=0.032, DSR=0.51.
- **Stage 3 — Rejim koşullama** ✅ `signals/regime.py` (Hurst/Efficiency-Ratio) + trend-geçitli momentum. **L/S DSR 0.51→0.79, Sharpe 1.14, p=0.0055** — edge belirgin güçlendi, ispat eşiğine yaklaştı (hâlâ <0.95).
- **Stage 4 — Ufuk-birleştirme** ⏭️ **SIRADAKİ.** Günlük+haftalık skill-ağırlıklı; önceden-kayıtlı hipotezle n_trials düşür → DSR>0.95 hedefi.
- **Sonraki:** meta-model/kalibrasyon, çapraz-kesit genişletme, LLM özellik katmanı, coin. (Tam liste + [strateji-arastirma.md](strateji-arastirma.md).)
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
```

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
