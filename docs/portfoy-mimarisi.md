# Portföy Mimarisi — Karar & Sentez

> Workflow (`portfoy-kurulumu-tasarim`) limit nedeniyle final sentezden önce durdu;
> tamamlanan 10 yöntem + 2 aday + evren analizi [portfoy-bulgulari.md](portfoy-bulgulari.md)'de
> kurtarıldı. Bu belge o bulgulardan **uzman sentezidir** (Claude, ajan açmadan). Tarih: 2026-06-15.

## Karar: "Portföy = Tahmin Gücü Ölçer" (Long-Short çekirdek + BL skill-gating graftı)

Amacımız kâr değil; **tahmin gücünü portföy düzeyinde dürüstçe ölçmek/ispatlamak.** Bu hedef
mimariyi belirler:

- **Çekirdek = Kesitsel Long-Short (dolar- + blok-beta-nötr, ters-vol ölçekli).** Tek-hisse
  mutlak tahmin neredeyse imkansız (idiyosenkratik gürültü), ama hisseleri **birbirine göre
  sıralamak** (cross-sectional rank) çok daha sağlam. forecast skoruna göre üstü long / altı
  short; dolar-nötr + beta-nötr → portföy getirisi piyasa yönünden **mekanik olarak izole**.
  Geriye kalan PnL = saf sıralama isabeti = öngörü gücünün **temiz, falsifiable** kanıtı.
- **Graft = Black-Litterman'ın skill-gating'i.** Forecast'ı `mu` olarak doğrudan `Σ⁻¹`'e
  vermek saf Markowitz/error-maximization (kanıtın en kötü senaryosu, N≈T'de `Σ` tekil). BL'nin
  değeri: sinyali bir "görüş" olarak prior'a Bayesçi karıştırır; görüş güveni (Ω) **OOS-skill'den**
  türetilir → skill yoksa portföy **otomatik 1/N'e/HRP-prior'a çöker.** Bu "auto-throttle" finsent'in
  BUGÜNKÜ durumuna (IC≈0.005, p=0.35: edge yok) tam oturur: garbage-in → tilt yok.

**Neden ikisi birden:** L/S çekirdek ölçümün kendisini (net sıralama edge'i) verir; BL skill-gating'i
ağırlıkların aşırı-güvenle patlamasını engeller. Kanıt zorunlu kılıyor (DeMiguel-Garlappi-Uppal 2009:
skill-siz girdiyle hiçbir optimizasyon 1/N'i yenmez; Bessler-Opfer-Wolff 2017: BL ancak görüşler
gerçek OOS skill taşırsa 1/N'i yener).

## Evren & seçim (gerçek veriden — kritik)
Kümeleme analizi: **16 araç ≈ ~5 bağımsız bahis** (ENB 4.9; PC1 varyansın %39'u). Yani araç-bazında
16 backtest'i bağımsız sayarsanız istatistiksel gücü **~3× abartırsınız** → çoklu-test düzeltmesinde
(Benjamini-Hochberg) efektif N=16 değil **~5** alınmalı.

5 küme: **BIST Cyclical Core** (THYAO/GARAN/AKBNK/KCHOL/SISE/EREGL/BIMAS — ENB sadece 1.86, GARAN≈AKBNK
0.92 ikiz), **ASELS** (savunma, idiosyncratic), **TUPRS** (enerji, BIST'e **negatif** — en güçlü hedge),
**US AI-Growth** (NVDA/META/AMZN/GOOGL/TSLA), **US Defensive** (AAPL/MSFT).

**Seçim (bilimsel):**
- **Çekirdek test seti (~7, bağımsız faktörleri kapsar):** GARAN, KCHOL, TUPRS, ASELS, NVDA, AAPL, GOOGL.
- **Out-of-sample hold-out (çekirdekle yüksek korele kardeşler):** AKBNK, THYAO, SISE, EREGL, BIMAS, META,
  AMZN, TSLA, MSFT. Mantık: çekirdekte sinyal/IC kalibre et, **korelasyonlu kardeşinde doğrula** — aynı
  gizli faktörde genelleşiyor mu? Tek araçta anlamlı çıkıp kardeşinde çökerse sinyal gürültüdür.

## Tahsis motoru (mekanik)
`rank → kesitsel-demean → ters-vol → blok-dolar-nötr → blok-beta-nötr → cap → kaldıraç-normalize`
- Ham skor `s_i = signal_i · confidence_iᵞ`; kesitsel demean (piyasa view'ını çıkar); rank (outlier'a
  bağışık); `/σ_i` (ters-vol — AAPL %25 vs AKBNK %57 vol farkı ölçümü yanlılamasın); blok-içi dolar-nötr;
  beta-nötr projeksiyon (`w ← w − (Σwβ/Σβ²)β`); `|w_i|≤0.20` + banka-çekirdek net cap ≤0.30 (çifte-sayım);
  `Σ|w|=1` (birim-bahis).
- **Kovaryans:** ağırlıkta tam `Σ` KULLANILMAZ (N≈T tekil) — sadece **diagonal vol + tek-faktör beta**.
  Ölçüm/raporlamada **Ledoit-Wolf shrinkage + Marchenko-Pastur denoising**. Vol = EWMA(λ=0.94); DCC-GARCH
  reddedildi (turnover/maliyet getirisi negatif).

## Risk & dengeleme
Vol-hedef (~%10 yıllık → ufuklar/rejimler karşılaştırılabilir); pozisyon/blok cap; **turnover freni
zorunlu** (no-trade bandı |Δw|<0.03, ağırlık-yumuşatma, rank-histeri) — yüksek turnover ölçüm-edge'ini
maliyet-sonrası siler. Drawdown'da pozisyon kesilmez (sansür ölçümü yanlılar) ama **alarm/flag** loglanır.

## Bilimsel ölçüm
L/S getiri serisi üzerinde: **spread-permütasyon p** (martingale-null), **Deflated Sharpe** (denenen
deneme sayısına göre), **1/N-rank benchmark** (aynı turnover freniyle), efektif N=5 ile t-istatistiği.
Her ufuk (intraday/günlük/uzun) **AYRI defter** — tek skora harmanlanmaz (ufuk-spesifik IC bulanmasın).

## Modül planı (önerilen)
- `finsent/portfolio.py` — `cross_sectional_weights(preds, betas, vols, blocks)` + saf yardımcılar
  (`neutralize_beta`, `block_dollar_neutral`, `inverse_vol_scale`).
- `finsent/risk.py` — `ewma_vol`, `block_beta`, `ledoit_wolf_cov`, `marchenko_pastur_denoise`,
  `effective_bets`.
- `finsent/ls_backtest.py` — `validation.py`'nin purge/embargo walk-forward'ını YENİDEN KULLANIR;
  her fold'da L/S getiri serisi + turnover + beta-kalıntısı üretir.
- `benchmarks.py` genişlet — `spread_permutation_pvalue`, `deflated_sharpe`, 1/N-rank null.
- `db.py` — `portfolio_weights`, `ls_returns` tabloları (predictions deseni, canlı-loglu).
- `scripts/run_ls_validation.py` — `run_validation.py`'nin L/S muadili.
- `config.py` — BLOCKS, CAP'ler, VOL_TARGET, TURNOVER_LAMBDA, çekirdek/hold-out setleri.

## Yol haritasındaki yeri — DÜRÜST sıra
Bu katman **anlamlı olması için önce bir edge gerektirir.** Bugün L/S ölçer **~0 okur** (forecast OOS
IC≈0.005) — ve bu doğru davranış. Bu yüzden sıra: **önce Stage 2 (1-12 ay momentum + mid-price) ile
çekirdek bir edge bul**, sonra bu portföy katmanı o edge'i piyasa-beta'sından arındırılmış halde
ölçsün/ispatlasın (Stage 5 civarı). Portföy önce kurulursa boş bir ölçer olur.

## Coin genişlemesi
Coin = **3. büyük ölçüde bağımsız faktör bloğu** → efektif bahis için en yüksek marjinal getiri. Ama
coin'ler kendi içinde yüksek korele (ETH/altcoin BTC betası) → "5 coin" ~1-2 efektif bahis. Altyapı:
`prices.py` 7/24 + ortak UTC ızgaraya resample (hizasız bar sahte korelasyon üretmesin), `config` CRYPTO
bölgesi (`BTC-USD`), vol-ölçekleme kritik (coin vol 2-4×). İspat fırsatı: aynı modelin **bağımsız bir
varlık sınıfında** da öngörü göstermesi tezin en güçlü out-of-sample doğrulamasıdır.
