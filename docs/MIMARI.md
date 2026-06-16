# Mimari — Paket Yapısı & Genişleme Rehberi

> İlke: akademik düzeyde bir çalışma; mühendisliği de o kadar sağlam olmalı. Düz/dağınık
> değil, **domain'lere ayrık, bağımlılığı tek yönlü, genişlemeye müsait** bir paket yapısı.
> Yeni modül eklerken **bu haritadaki doğru katmana** koy.

## Katmanlar (bağımlılık AŞAĞIDAN YUKARI akar)

```
finsent/
  # — Çekirdek (core): her şey buna bağlanır, kendisi hiçbir üst katmana bağlanmaz —
  config.py        # tüm ayarlar (TICKERS, ağırlıklar, ufuk, lookback'ler)
  models.py        # veri şemaları (Record, Sentiment, Author)
  tickers.py       # ticker eşleme
  db.py            # SQLite depolama (records, scores, prices, predictions)

  # — Veri katmanı —
  collectors/      # duygu kaynakları (Reddit, StockTwits, RSS, KAP) — base + her kaynak
  prices.py        # piyasa verisi (yfinance saatlik/günlük bar → db)

  # — Duygu hattı —
  sentiment.py     # lexicon / FinBERT skorlama
  credibility.py   # bot/yazar güven skoru
  aggregate.py     # ağırlıklı sentiment + momentum (pencere bazında)
  pipeline.py      # collect → process → dedupe → store → aggregate orkestrasyonu

  # — Tahmin katmanı —
  features.py      # özellik mühendisliği (fiyat + momentum + duygu); no-look-ahead
  forecast.py      # model: RuleForecaster + ML + Blend; fit_from_data; canlı tahmin/günlük

  # — Bilim katmanı (evaluation/) — tahmin katmanına bağlı, üstüne portföy gelir —
  evaluation/
    backtest.py    # in-sample kalibrasyon/ölçüm (calibrate_from, evaluate) — hızlı gösterge
    validation.py  # purged + embargoed walk-forward CV (DÜRÜST örnek-dışı)
    benchmarks.py  # null'lar (buy&hold, random-sign, permütasyon)
    stats.py       # Sharpe, PSR, Deflated Sharpe, blok-bootstrap, Benjamini-Hochberg

  # — Portföy katmanı (portfolio/) — en üst; bilim + tahmin katmanına bağlanır —
  portfolio/
    weights.py     # kesitsel rank → dolar-nötr + ters-vol ağırlık; 1/N-rank benchmark
    ls_backtest.py # kesitsel walk-forward → market-nötr long-short getiri serisi

  api.py           # (opsiyonel API yardımcıları)

scripts/           # çalıştırılabilir raporlar (python -m scripts.X)
  run_demo / run_batch / run_stream      # duygu hattı
  run_validation                         # Stage 0/2 dürüst OOS (hourly | daily)
  run_ls_validation                      # kesitsel L/S + istatistiksel sertleştirme
server.py          # web app (FastAPI + dashboard) — canlı panel
docs/              # dokümantasyon (bkz. docs/README.md)
```

## Bağımlılık kuralı
core ← veri ← duygu/tahmin ← **evaluation** ← **portfolio**. Üst katman alta bağlanır, ASLA
tersi. `forecast` yalnız `evaluation.backtest`'in saf fit yardımcılarını kullanır (kalibrasyon
matematiği); `evaluation.validation`/`benchmarks` `forecast`'ı tüketir. Döngü yok (alt-paket
`__init__`'leri eager re-export YAPMAZ; submodule'lar açıkça import edilir).

## Yeni modül nereye girer? (genişleme haritası)
- **Yeni sinyal/özellik** (rejim, mid-price reversal, etiketleme): `features.py` veya yeni
  `finsent/signals/` (regime.py, labeling.py) — tahmin katmanı.
- **Yeni model** (meta-model, kalibrasyon, sequence/ML): `forecast.py` veya `finsent/models_ml/`.
- **Yeni istatistik test** (PBO/CSCV, SPA, White Reality Check): `evaluation/stats.py`.
- **Yeni portföy yöntemi** (covariance, risk, Black-Litterman): `portfolio/` (covariance.py,
  risk.py, blacklitterman.py — docs/portfoy-mimarisi.md'de planlı).
- **LLM özellik katmanı** (haber→sürpriz/olay/kesitsel-sıra): `finsent/llm_features.py`
  (bkz. docs/fikirler-dipnotlar.md #1) → çıktısı `features.py`'a girer.
- **Yeni veri/araç** (coin): `config.py` (CRYPTO bölgesi) + `prices.py` (7/24 ızgara).
- **Yeni rapor**: `scripts/run_*.py` (mevcut desende; sys.path insert + `python -m`).

## Standartlar
- Kod içi yorumlar **Türkçe ve niyeti anlatır**; her modülün başında sorumluluk docstring'i.
- **Sıfır/az bağımlılık** ve **zarif fallback** (sklearn/yfinance opsiyonel-import deseni).
- **No-look-ahead** her özellik/etikette; her "edge" iddiası OOS + null + çoklu-test'ten geçer.
