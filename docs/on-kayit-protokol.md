# Önceden-Kayıt (Pre-Registration) Protokolü

> Akademik dürüstlüğün omurgası: hipotez, özellik seti, denenecek konfigürasyonlar ve
> **kabul/red kriterleri SONUÇTAN ÖNCE sabitlenir.** HARKing (sonucu görüp hipotezi
> değiştirme) ve n_trials'ı edge'i geçirecek şekilde seçmek (p-hacking) YASAK. Bu belge
> nihai (makale) değerlendirmesinin kurallarını sabitler; bugüne kadar denenen konfigürasyonlar
> n_trials'a DAHİL edilir.

## Tez (ana)
Borsa kısa-orta vadeli yön/sıralama hareketleri, **rejim-koşullu kesitsel momentum** ile
martingale-üstü ve çoklu-test-düzeltmeli anlamlı şekilde öngörülebilir. (Para/işlem değil;
ölçü = öngörü gücü.)

## Hipotezler (sabit)
- **H1:** Çok-ölçekli momentum (günlük 1-12 ay) forward-return ile permütasyon-null üstünde
  anlamlı IC taşır. — *Durum: Stage 2'de DESTEKLENDİ (OOS IC=0.069, p=0.001).*
- **H2:** Rejim koşullama (Hurst/Efficiency-Ratio) edge'i koşulsuzdan anlamlı güçlendirir.
  — *Durum: Stage 3'te DESTEKLENDİ (L/S DSR 0.51→0.79, benchmark değişmedi).*
- **H3:** Ham teknik indikatörler (MA/MACD/saatlik) baseline üstünde artı-değer VERMEZ.
  — *Durum: Stage 0'da DESTEKLENDİ (saatlik OOS IC=0.005, p=0.35).*
- **H4:** Sinyal yönsel-zamanlama değil KESİTSEL'dir (drift'i geçmez, market-nötr hasat edilir).
  — *Durum: Stage 2-3'te DESTEKLENDİ (yön buy&hold'u geçmez; L/S Sharpe>0).*
- **H5 (ana karar):** Rejim-koşullu kesitsel momentum L/S, **çoklu-test-düzeltilmiş (Deflated
  Sharpe) ve otokorelasyon-dayanıklı (blok-bootstrap)** olarak anlamlı bir getiri üretir.

## Sabit özellik seti (no further search)
Teori-türevli, önceden sabit: çok-ölçekli momentum (`mom_/momsc_ 21/63/126/252`), kısa-vade
reversal (mom_21 negatif), rejim göstergeleri (`er`, `hurst`), trend-geçitli momentum
(`mom63_reg`, `momX_reg`). Taban fiyat özellikleri (`ret1/3/6, vol, sma_dist, rsi`) kontrol.
**Yeni özellik araması yapılmayacak;** strateji = kesitsel rank → dolar-nötr + ters-vol L/S.

## n_trials muhasebesi (DÜRÜST)
Deflated Sharpe n_trials'a çok duyarlı. Bugüne dek denenen **bağımsız strateji ailesi/konfig**:
1. Saatlik fiyat-teknik (Stage 0). 2. Günlük çok-ölçekli momentum (Stage 2). 3. + rejim
koşullama (Stage 3). 4. + çok-ufuk ensemble (Stage 4, **reddedildi**). + ufuk/lookback
seçimleri. **Önceden-kayıtlı n_trials = 7** (bu aileleri + birkaç tasarım seçimini kapsayan,
makul-muhafazakâr sayı). DSR her zaman **n_trials ∈ {3, 7, 22}** grid'inde şeffaf raporlanır;
tek bir sayı seçilip "kazandık" denmez.

## Kabul/Red kriteri (H5 için, SABİT)
**"Robust edge ispatlandı"** ancak şu İKİSİ birden sağlanırsa:
- blok-bootstrap p < 0.05, **VE**
- Deflated Sharpe (n_trials = 7) > 0.95.

Aksi halde sonuç "edge var ama robust ispat eksik / sınırda" olarak raporlanır. Tez ŞU
durumlarda REDDEDİLİR: OOS L/S Sharpe ≤ 0; veya bootstrap p ≥ 0.05; veya 1/N-rank benchmark'ı
geçemiyor; veya daha uzun OOS'ta edge sıfırlanıyor.

## Güncel durum (2026-06-15)
- blok-bootstrap p = **0.0055** ✓ (kriteri geçiyor)
- Deflated Sharpe: n_trials=3 → **0.970** (✓), **n_trials=7 → 0.912** (✗, kıl payı), n_trials=22 → 0.789 (✗)
- 1/N-rank benchmark'ı geçiyor ✓

**Karar:** **SINIRDA — robust ispat HENÜZ TAM DEĞİL.** Edge gerçek ve güçlü (p=0.0055, n=3'te DSR>0.95),
ama önceden-kayıtlı n_trials=7 eşiğinde 0.912 ile **kıl payı altında.** Dürüst konum: "güçlü,
tutarlı, neredeyse-ispatlı" — ama kriteri tam karşılamadığı için **"ispatlandı" DEMİYORUZ.**

**Eşiği muhafazakâr geçmek için (kriter değiştirmeden):** daha uzun geçmiş + daha fazla araç/coin
→ rebalans sayısı (n) artar, SR* düşer, Sharpe stabilize olur → n_trials=7'de DSR>0.95 hedeflenir.
