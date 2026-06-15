# Geliştirme Rehberi & Dokümantasyon İndeksi

> **Buradan başla.** Bu belge, projenin hedefini, şu anki dürüst durumunu, yol
> haritasını ve nasıl devam edileceğini özetler. Detaylar alt belgelerde.

## Amaç (tek cümle)
Para/yatırım değil: **borsa hareketlerinin ne ölçüde öngörülebilir olduğunu bilimsel,
sızıntısız, çoklu-test-düzeltmeli bir kurguyla ölçmek ve raporlamak** (saatlik/günlük/
uzun vade; 9 BIST + 7 ABD hissesi, ileride coin). Aynı zamanda bir Claude Code deneyi.

## Temel ilke — DÜRÜSTLÜK
Ham "backtest kârlı" **kanıt değildir.** Her sayı şu üçlüden geçmeden iddia edilmez:
1. **Örnek-dışı (OOS)** — purged + embargoed walk-forward CV (`finsent/validation.py`).
2. **Null'a karşı** — buy&hold / random-sign / permütasyon (`finsent/benchmarks.py`).
3. **Çoklu-test düzeltmeli** — Deflated Sharpe / PBO / SPA-FDR (Stage 1, henüz yok).

## Şu anki dürüst durum (2026-06-15)
- **Stage 0 tamam.** Mevcut modelin sızıntısız OOS sonucu: **IC ≈ 0.005, hit ≈ %50.1,
  permütasyon p = 0.35** → saatlik fiyat-teknik özelliklerle **öngörü kanıtı YOK** (eski
  raporlanan IC 0.0248'in ~%80'i sızıntıydı). Bu, üstüne inşa edeceğimiz **dürüst
  baseline.** Detay: [sonuclar.md](sonuclar.md).
- Çalışan ürün: gerçek-zamanlı duygu + saatlik fiyat + (zayıf) öngörü paneli — `server.py`.

## Dokümanlar
| Belge | İçerik |
|---|---|
| [strateji-arastirma.md](strateji-arastirma.md) | **Ana strateji.** 10 sinyal ailesi sentezi: taksonomi (strong/mixed/weak), tek-tahmin-motoru mimarisi, ufuk oyun kitapları, bilimsel metodoloji, modül planı, makale taslağı, 8-aşamalı yol haritası, riskler + uzman yorumu. |
| [arastirma-bulgulari.md](arastirma-bulgulari.md) | 10 alanın derin araştırma + adversarial doğrulama detayı (referans, ~160 KB). |
| [sonuclar.md](sonuclar.md) | **Bilimsel günlük.** Her aşamanın dürüst OOS ölçümü. Şu an: Stage 0. |
| [fikirler-dipnotlar.md](fikirler-dipnotlar.md) | Dip notlar: LLM'in rolü (beklenti/nedensel-iletim motoru), portföy korelasyon bulguları. |

## Yol haritası (nerede kaldık)
Tam liste: [strateji-arastirma.md › Yol Haritası](strateji-arastirma.md). Özet:

- **Stage 0 — Temel dürüstlük** ✅ `validation.py` (WF-CV) + `benchmarks.py`. Sızıntı kapandı, baseline kuruldu.
- **Stage 1 — İstatistiksel geçerlik** ⏭️ `stats.py`: blok-bootstrap, Deflated Sharpe, PBO, SPA/FDR. (sıradaki)
- **Stage 2 — Doğru sinyaller** ⏭️ **EN YÜKSEK BEKLENEN-DEĞER.** `features.py` genişletme: 1-12 ay momentum (vol-ölçekli/ölçeksiz ayrı), mid-price reversal, gün-içi/overnight. `labeling.py` triple-barrier. Hedef: baseline IC≈0.005 / p=0.35'i **anlamlı geçmek.**
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
**Duygu kolu:** `collectors/` → `pipeline.py` → `sentiment.py` / `credibility.py` →
`aggregate.py` → `db.py`.
**Öngörü kolu:** `prices.py` (yfinance) → `features.py` → `forecast.py` (kural+ML blend)
→ `db.py` (predictions log).
**Bilim kolu (Stage 0):** `validation.py` (purged+embargoed WF-CV) + `benchmarks.py`
(null'lar) → `scripts/run_validation.py`.
**Arayüz:** `server.py` + `web/dashboard.html`.

Kod içi yorumlar Türkçe ve ayrıntılıdır; her modülün başındaki docstring sorumluluğu anlatır.
