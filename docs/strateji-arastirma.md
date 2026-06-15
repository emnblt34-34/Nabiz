# Borsa Öngörülebilirliği — Strateji Sentezi

_Kaynak: `borsa-ongorulebilirlik-arastirma` workflow'u (10 sinyal ailesi, adversarial doğrulama). Tarih: 2026-06-15. Uzman yorumu en sonda._


## Yönetici Özeti

EN KRİTİK ÇIKARIMLAR (kanıt gücüyle, finsent'e bağlı):

1) İNDİKATÖRLERİN KENDİSİ SİNYAL DEĞİL, GÜRÜLTÜLÜ ÖLÇERDİR. MA/EMA crossover, MACD, ADX, Ichimoku, SuperTrend tek başına maliyet-sonrası örnek-dışı öngörü taşımaz (Sullivan-Timmermann-White 1999: BLL'in DJIA üstünlüğü 1987-1996'da kaybolur). finsent'in mevcut RSI(6) özelliği de bu kategoride: ham eşik kuralı değil, REJİM-KOŞULLU özellik olarak tutulmalı. Bu indikatörleri "sihirli sinyal" sanan her yaklaşım REDDEDİLİR.

2) GERÇEK ÖNGÖRÜ TAŞIYAN OLGU: ZAMAN-SERİSİ + ÇAPRAZ-KESİT MOMENTUM (3-12 ay). Strong kanıt (MOP 2012, JT 1993/2001/2023) AMA İKİ ÇEKİNCE: (a) kanıt çoğunlukla çeşitlendirilmiş FUTURES portföyünden gelir, tek-hisse/saatlik/BIST'e doğrudan taşınmaz; (b) Sharpe'ın büyük kısmı vol-ölçeklemeden gelebilir (Kim-Tse-Wald 2016). Bu yüzden "strong" değil OPERASYONEL OLARAK "conditional" muamelesi yapılmalı. finsent şu an sadece ret1/ret3/ret6 (saatlik) kullanıyor — momentumun gerçek kanıt bölgesi olan 1-12 AYLIK getiri özelliği EKSİK; eklenmesi en yüksek beklenen-değerli iş.

3) KISA-VADE REVERSAL GERÇEK AMA MİKROYAPI KAYNAKLI. Haftalık/aylık reversal (Lehmann/Jegadeesh 1990) bağımsız doğrulanır ama büyük kısmı bid-ask bounce + likidite primidir ve modern dönemde "çoğu bölgede kaybolmuş"tur (Blitz 2024). BIST'te geniş spread bunu SAHTE öngörü olarak şişirir; mid-price kullanılmazsa finsent'in saatlik IC'si yapay yükselir.

4) UFUK × REJİM MATRİSİ EN ÖNEMLİ PRATİK ÇIKARIM (Hurst): dakikalar=mean-revert, saatler-birkaç yıl=trend, on yıllar=revert. finsent'in 3 ufku (saatlik/günlük/uzun) bu haritaya oturtulmalı; SAATLİK ufukta saf trend-takip riskli, gün-içi momentum (Gao ve ark.: ilk-yarım-saat→son-yarım-saat) + reversal birlikte test edilmeli.

5) GÜN-İÇİ MOMENTUM finsent'in saatlik hedefine EN YAKIN akademik kanıt (mixed). S&P ETF'lerde anlamlı ama R²~%1.6 — maliyet/spread bunu kolayca yutar; tek-hisse/BIST'e taşınması DOĞRULANMALI.

6) DIVERGENCE REDDEDİLİR. Tek başına güvenilirliği "çöküyor"; pivot ancak gelecek barlarla kesinleştiği için en sinsi LOOK-AHEAD kaynağı. Mekanik, gelecek-sızdırmaz tanım olmadan finsent'e GİRMEMELİ.

7) ADX/Hurst SİNYAL DEĞİL FİLTRE. ADX'in bağımsız öngörü kanıtı yok (anecdotal); değeri yalnızca trend-takibi koşullamasında. finsent'e meta-filtre olarak girer, doğrudan ağırlık almaz.

8) MEVCUT finsent BACKTEST'İ SIZINTILI. backtest._pool tüm barları HAVUZLAR; scaler tüm örnekte fit edilir, ML tüm havuzda eğitilip AYNI havuzda "backtest" edilir → in-sample optimizm. Purged/embargoed walk-forward CV YOK. Bu, raporlanan IC/hit-rate'i yukarı yanlı yapar; ilk düzeltilecek BİLİMSEL kusur budur.

9) ÇOKLU-TEST DÜZELTMESİ YOK. Birden çok indikatör/eşik/parametre denendiğinde "en iyi" şans eseri çıkar. Deflated Sharpe (Bailey-López de Prado), White Reality Check / Hansen SPA, PBO eklenmeden hiçbir "edge" iddiası bilimsel değildir.

10) DUYGU KATKISI HENÜZ KANITSIZ. SENT_PRIORS elle konmuş; geçmiş duygu verisi olmadığı için backtest edilemiyor, yalnız canlı predictions günlüğünde doğrulanabilir. Duygunun fiyat-ötesi MARJİNAL katkısı (ablation) ölçülmeden duygu "öngörü taşıyor" denemez.

11) CONFIDENCE KALİBRE DEĞİL. forecast._Base.predict'teki güven bir formül; gerçek olasılık kalibrasyonu (reliability diagram, Brier) yok. "Güven %80" iddiası şu an doğrulanamaz.

12) BENCHMARK = RANDOM WALK + BUY&HOLD. "Borsa öngörülebilir" tezi ancak martingale/permütasyon null'ı ÇOKLU-TEST düzeltmesiyle yenildiğinde kanıtlanır. Ham "backtest kârlı" KANIT DEĞİLDİR.

## Sinyal Taksonomisi (kanıt gücüyle)

SİNYAL AİLELERİ (kanıt gücü / ufuk / finsent katkısı):

=== STRONG (gerçek, çok-replikasyonlu olgu) ===
• Çapraz-kesit momentum (Jegadeesh-Titman, göreli güç sıralaması). Ufuk: 3-12 ay formasyon+tutma. Katkı: finsent'in 16 hisselik evreninde rank-momentum özelliği + cross-sectional rank-IC. UYARI: yayın-sonrası ~%50 decay (McLean-Pontiff), momentum-crash kuyruk riski (Daniel-Moskowitz). BIST küçük-hisse likidite uyarısı.
• Zaman-serisi momentum (12-ay kendi getirisi). Ufuk: 1-12 ay. Katkı: en taşınabilir feature = ölçeklenmiş 1/3/6/12-ay getiri + işareti. UYARI: "strong" etiketi cömert — vol-ölçekleme artefaktı (Kim-Tse-Wald) ve 2011-2019 yatay dönem; tek-hisse'de zayıf. OPERASYONEL: conditional.
• Kısa-vade reversal anomalisi (haftalık/aylık). Ufuk: 1 hafta-1 ay (uzun vade DEĞİL). Katkı: günlük ufukta reversal feature. UYARI: mikroyapı/likidite kaynaklı, modern dönemde büyük ölçüde aşınmış (Blitz 2024); BIST spread'inde SAHTE şişme.

=== MIXED (gerçek ama kırılgan/bağlama duyarlı) ===
• Gün-içi momentum (ilk→son yarım-saat, Gao ve ark.). Ufuk: intraday/saatlik. Katkı: finsent'in saatlik hedefine en yakın test edilebilir kalıp. UYARI: R²~%1.6, ETF-merkezli, tek-hisse/BIST doğrulanmamış; gün-içi reversal ile karışır.
• Intraday vs overnight reversal. Ufuk: intraday. Katkı: saatlik sinyalin neden "çalışıp" temel yön vermediğini açıklar; overnight kalıcı, intraday geçici. UYARI: bid-ask bounce, temiz saatlik veri şart.
• Hurst rejim üsteli. Ufuk: ölçek-bağımlı meta. Katkı: ufuk×rejim koşullamasının istatistiksel motoru. UYARI: tahmin gürültülü/yönteme duyarlı, kısa pencerede güvenilmez; tek başına yön vermez.
• ROC / saf momentum osilatörü. Ufuk: n'e bağlı (kısa=reversal, orta=momentum). Katkı: ham momentum ölçer. UYARI: n seçimi yönü ters çevirir — data-mining daveti.

=== WEAK (tek başına öngörü kanıtı yok; sadece özellik/filtre) ===
• MA/EMA crossover (50/200 golden/death cross). Ufuk: uzun vade. Katkı: getiri-öngörüsü DEĞİL drawdown/rejim göstergesi; kendini-doğrulayan+kalabalık eşik.
• MACD. Katkı: alttaki momentumun gürültülü proxy'si; ham crossover sinyali girmesin.
• RSI / Stochastic / Williams %R / CCI. Katkı: rejim-koşullu özellik. UYARI: %R≡Fast Stochastic (özdeş — ikisini birlikte koyma, multikolinearite). Eşikler (30/70, 20/80, ±100) serbest parametre → çoklu-test düzeltmesi şart. Kripto'da RSI ters çalışıyor (trend-persistans, Mukherjee).

=== ANECDOTAL (kanıt yok, varsayılan güvenme) ===
• ADX. Yalnız trend-filtresi olarak (sinyal değil); döngüsel mantık (trend-takibin kendi kanıtına bağımlı).
• Ichimoku. Çok-parametreli; DJ-30 testinde ~%10 kazanma, buy-hold altı. Yalnız MA-baseline üstünde ablation ile test.
• SuperTrend. (ATR,çarpan) klasik overfit; bağımsız OOS yok. Baseline üstünde ablation.
• Divergence. REDDEDİLDİ — look-ahead tuzağı.

## Strateji Çerçevesi — Tek Tahmin Motoru

TEK TAHMİN MOTORU MİMARİSİ (finsent'e bağlı):

1) ÖZELLİK KATMANI (features.py genişletmesi). Mevcut 10 özelliğe ek aileler, hepsi closes[:i+1] disiplinli:
   - MOMENTUM ailesi (en kritik eksik): çok-ölçekli ölçeklenmiş getiri ret_5/ret_20/ret_120/ret_500 bar (~gün/hafta/ay/çeyrek) ve İŞARETLERİ; her biri rolling-vol ile normalize (vol-ölçekli + ölçeksiz AYRI tutulur — Kim-Tse-Wald artefaktını izole etmek için).
   - REVERSAL ailesi: 5/20-bar reversal (geçmiş getirinin negatifi), mid-price tabanlı (BIST bid-ask bounce'ı önlemek için close yerine (high+low)/2 proxy).
   - GÜN-İÇİ ailesi (saatlik): seans-içi konum, ilk-bar getirisi, overnight-vs-intraday ayrımı.
   - REJİM ailesi: Hurst(H), ADX, realized-vol rejimi, uzun-MA eğimi — bunlar SİNYAL değil KOŞULLAMA değişkeni.
   - OSİLATÖR ailesi: RSI(14) standardı + ROC; Stochastic VEYA %R (ikisi değil). Ham eşik değil z-skor.
   - TEKNİK indikatör proxy'leri: MACD, MA-distance — ham crossover değil, sürekli değer.

2) SİNYAL AĞIRLIKLANDIRMA / ÖĞRENME. Mevcut backtest.calibrate IC-ağırlıklı kural iyi başlangıç ama tüm-örnek IC sızıntılıdır. Yeni: ağırlıklar SADECE her CV-fold'un in-sample diliminde öğrenilir, OOS'ta dondurulur. Rule (şeffaf, IC-ağırlıklı) tabanı korunur; üstüne regularize lineer/ağaç ML.

3) REJİM KOŞULLANDIRMA (ana fikir). Tahmin = f(özellik | rejim). H>0.5 / ADX>25 → trend-takip özelliklerine ağırlık; H<0.5 → reversal özelliklerine. Rejim sınıflandırması ONLINE (look-ahead'siz) ve kendisi bir serbest parametre olarak çoklu-test'e dahil. Her rejim hücresinde ayrı IC/hit-rate raporlanır.

4) ENSEMBLE. Ufuk-uzmanı modeller (intraday/daily/long) + rejim-uzmanı modeller; çıktılar olasılık düzeyinde harmanlanır. Mevcut BlendForecaster (rule+ml 50/50) bunun çekirdeği; rejim/ufuk-koşullu ağırlığa genişletilir.

5) META-MODEL (López de Prado tarzı). Birincil model YÖN üretir; meta-model "bu sinyale güvenilir mi" (büyüklük/conf) öğrenir — predictions tablosundaki gerçekleşmiş isabetle eğitilir. Bu, forecast.predict'teki uydurma confidence'ı KALİBRE olasılıkla değiştirir (Platt/isotonic + reliability diagram + Brier).

6) DUYGU ENTEGRASYONU. Sentiment özellikleri (sent/mom/posneg/logvol) fiyat-özellikleri ÜZERİNE marjinal katkı olarak ablation ile test edilir (fiyat-only vs fiyat+duygu IC farkı). SENT_PRIORS elle değil, canlı predictions verisi biriktikçe ÖĞRENİLİR. Duygu en çok haber-günü/yüksek-hacim rejiminde katkı bekleniyor.

7) HABER/MAKRO/MİKROYAPI. Haber: KAP disclosure event-flag (sentiment değil olay) + haber-yoğunluğu rejim değişkeni. Makro: ufuk-uzun modelde rejim koşullayıcı (faiz/USDTRY/VIX proxy). Mikroyapı: spread/likidite filtresi — BIST illikit hisselerde reversal "kanıtı" filtrelenir.

ÇIKTI: yön + KALİBRE olasılık + beklenen hareket + rejim etiketi + hangi sinyal ailesinin katkı verdiği (yorumlanabilirlik). Her tahmin predictions tablosuna rejim/ufuk/aile-katkısıyla loglanır.

## Ufuk Oyun Kitapları


### Intraday (saatlik / gün içi)

INTRADAY (saatlik, finsent PRICE_INTERVAL=60m, HORIZON_BARS=3): SİNYALLER — gün-içi momentum (ilk→son blok, Gao), intraday-vs-overnight ayrımı, kısa-vade reversal (mikroyapı), RSI(14)/Stochastic rejim-koşullu. Saf trend-takip RİSKLİ (Hurst: çok kısa ölçek mean-revert). MODEL — rejim-koşullu lojistik/ağaç; H<0.5'te reversal-ağırlık, H>0.5'te momentum-ağırlık. ETİKETLEME — kısa-ufuk triple-barrier (üst/alt bariyer = k×saatlik-vol, dikey bariyer = 1-6 bar) VEYA basit forward-return işareti (mevcut). ZORUNLU: mid-price (bid-ask bounce), kapanış-teyitli sinyal (t+1 uygulanabilir), R²~%1.6 olduğu için spread/maliyet modele dahil. UYARI: bu ufukta 'öngörü'nün çoğu geçici likidite baskısı — temel yön değil; rapor bunu açıkça ayırmalı.

### Günlük / swing

DAILY/SWING (günlük bar — yeni interval='1d' eklenmeli): SİNYALLER — MA/MACD/SuperTrend en anlamlı bölge AMA örnek-dışı doğrulanmalı; çapraz-kesit reversal (haftalık/aylık) ve kısa-orta momentum. MODEL — rule (IC-ağırlıklı) + regularize ML blend; ADX/Hurst filtresi. ETİKETLEME — triple-barrier (López de Prado): üst/alt = k×günlük-ATR, dikey = 5-20 gün; meta-labeling ile büyüklük. CV — purged+embargoed walk-forward (etiket ufku kadar embargo). En sağlam reversal olgusu (RSI(2)/haftalık) burada; ama maliyet/aşınma ile net ölç.

### Uzun vade

LONG_TERM (haftalık/aylık — interval='1wk'/'1mo' eklenmeli): SİNYALLER — 12-ay TSMOM + çapraz-kesit momentum (EN GÜÇLÜ kanıt), 50/200 cross (getiri değil DRAWDOWN/rejim göstergesi olarak). Osilatör mean-reversion uzun vadede ZAYIF — kullanma. MODEL — basit, şeffaf, az-parametreli (parsimony; overfit'e karşı). Cross-sectional rank-momentum 16-hisse evreninde. ETİKETLEME — n-ay forward return + rank. UYARILAR: tek-hisse + yayın-sonrası decay (McLean-Pontiff ~%58); vol-ölçekli vs ölçeksiz AYRI raporla (Kim-Tse-Wald); momentum-crash kuyruk riski (V-dönüşü); BIST küçük-hisse işlem-edilemez edge. >1 yıl ve ~1 ayda momentum TERSİNE döner — pencere seçimi kritik.


## Bilimsel Metodoloji

BİLİMSEL DOĞRULAMA PROTOKOLÜ (finsent'in mevcut backtest.py'sini bilimsel standarda çıkarır):

1) ETİKETLEME. Mevcut forward_return işaretini koru AMA TRIPLE-BARRIER ekle (López de Prado): her gözlem için üst bariyer (+k×vol), alt bariyer (-k×vol), dikey bariyer (ufuk). Etiket = ilk dokunulan bariyer. Bu, sabit-ufuk getirinin keyfiliğini giderir ve volatilite-koşullu hedef sağlar. META-LABELING: birincil model yön, ikincil model "işlem yap/yapma" (büyüklük) öğrenir → kalibre güven.

2) PURGED + EMBARGOED WALK-FORWARD CV (en kritik düzeltme). Mevcut _pool tüm barları havuzlar = SIZINTI. Yeni: zaman-sıralı fold'lar; test fold'undan önceki/sonrası ETİKET UFKU kadar bar PURGE+EMBARGO edilir (örtüşen etiketler train↔test sızıntısını önler). Scaler ve ML SADECE train-fold'da fit; OOS'ta dondurulur. Per-fold IC/hit-rate, sonra fold-ortalaması + standart hata.

3) SIZINTI ÖNLEME (checklist). (a) Özellik closes[:i+1] — finsent zaten uyguluyor, koru. (b) Scaler/IC sadece in-sample fit. (c) Divergence pivot'u gelecek-sızdırır → YASAK. (d) Sinyal bar-kapanışıyla, işlem t+1. (e) Ichimoku ileri-kaydırma 'gelecek bilgisi' değil. (f) İlk-yarım-saat bloğu tam kapanmadan kullanılmaz. (g) Survivorship: delist olmuş hisse yok (BIST/US evreni sabit — küçük risk).

4) METRİKLER. Birincil: IC ve rank-IC (Pearson/Spearman, finsent'te zaten pearson var), hit-rate (var), yön AUC, Brier (kalibrasyon). Strateji düzeyi: DEFLATED SHARPE RATIO (Bailey-López de Prado — denenen deneme sayısına göre düzeltilmiş), PBO (Probability of Backtest Overfitting — combinatorially-symmetric CV). HER metrik üç-katmanlı: ham vs maliyet-sonrası, in-sample vs OOS, ve çoklu-test-düzeltilmiş.

5) İSTATİSTİKSEL TESTLER. (a) RANDOM-WALK/MARTINGALE NULL: IC'nin sıfırdan farkı için blok-bootstrap/permütasyon testi (zaman yapısını koruyan). (b) ÇOKLU-TEST DÜZELTMESİ: birden çok indikatör/eşik/ufuk denendiğinde White Reality Check veya Hansen SPA; çok-hipotez için FDR (Benjamini-Hochberg) veya Bonferroni. (c) Vol-ölçekli vs ölçeksiz TSMOM ayrı test (artefakt izolasyonu). (d) Rejim-koşullu IC'nin koşulsuzdan farkı (rejim gerçekten bilgi katıyor mu).

6) BENCHMARK SEÇİMİ. (a) Random-walk/martingale (öngörülemezlik null'ı). (b) Buy-and-hold (mevcut evaluate'e ekle). (c) Rastgele-işaret sinyali (skill vs şans). (d) Naif persistence (son getiriyi devam ettir). Tez ancak bunların TÜMÜNÜ çoklu-test-düzeltilmiş OOS'ta yenince desteklenir.

7) CANLI DOĞRULAMA. predictions tablosu = gerçek ileriye-dönük test (geçmiş-uydurmaya karşı bağışık). Rejim/ufuk/aile-katkısı kaydedilir; reliability diagram ile confidence kalibre edilir. Canlı hit-rate, backtest hit-rate'in ALTINDA çıkarsa (beklenir) — bu overfit/decay teşhisidir.

## Modül Planı (finsent)

finsent'e EKLENECEK MODÜLLER (ÖNCELİK SIRASIYLA):

ÖNCELİK 1 — BİLİMSEL TEMELİ DÜZELT (mevcut sızıntıyı kapat):
• finsent/validation.py (YENİ): purged+embargoed walk-forward CV iskeleti. backtest._pool'u SARAR; fold'lara böler, scaler/ML'i SADECE train-fold'da fit eder, OOS metrik toplar. backtest.calibrate ve forecast._train_ml bu CV'den çağrılır. SIZINTIYI bu kapatır — ilk iş.
• finsent/stats.py (YENİ): deflated_sharpe(), pbo(), permutation_test() (blok-bootstrap), white_reality_check()/spa(), benjamini_hochberg(). backtest.evaluate çıktısını bu testlerden geçirir. "edge gerçek mi" kararı burada.
• finsent/benchmarks.py (YENİ): random_walk, buy_and_hold, random_sign, persistence null'ları. backtest_forecaster bunlara karşı raporlar.

ÖNCELİK 2 — DOĞRU SİNYALLERİ EKLE (gerçek öngörü bölgesi):
• features.py (GENİŞLET): momentum ailesi (ret_20/120/500 + işaret, vol-ölçekli/ölçeksiz), reversal ailesi (mid-price), gün-içi/overnight ayrımı, RSI(14)+ROC. Mevcut MIN_BARS ve no-look-ahead disiplinini koru. FEATURES listesini büyüt ama düşük-korelasyonlu set seç (%R+Stochastic ikisini birden KOYMA).
• finsent/regime.py (YENİ): hurst_exponent() (online, look-ahead'siz), adx(), realized_vol_regime(). SİNYAL değil KOŞULLAMA değişkeni döndürür. forecast bunları rejim-ağırlığı için kullanır.
• finsent/labeling.py (YENİ): triple_barrier(), meta_label(). features.forward_return'e alternatif; volatilite-koşullu etiket.

ÖNCELİK 3 — MODELİ ZENGİNLEŞTİR:
• forecast.py (GENİŞLET): RegimeConditionalForecaster (rejim hücresine göre ağırlık), MetaForecaster (kalibre confidence — predictions verisinden Platt/isotonic). BlendForecaster'ı ensemble'a genişlet.
• config.py (GENİŞLET): interval='1d'/'1wk' destekleri (HORIZON_BARS ufka göre), triple-barrier k/dikey-bariyer ayarları, CV fold/embargo parametreleri.

ÖNCELİK 4 — ÇOK-UFUK + ÇAPRAZ-KESİT:
• prices.py (GENİŞLET): günlük/haftalık bar çekimi (PRICE_PERIOD_BACKTEST uzat), mid-price (high+low)/2 desteği.
• finsent/cross_section.py (YENİ): 16-hisse evreninde rank-momentum, rank-IC, çapraz-kesit reversal. db'ye cross-sectional skor tablosu.

ÖNCELİK 5 — RAPORLAMA + DÜRÜSTLÜK:
• db.py (GENİŞLET): predictions'a regime/horizon/family_contribution kolonları; cv_results, benchmark_results tabloları.
• backtest.py (GENİŞLET): evaluate'e ham-vs-maliyet, IS-vs-OOS, düzeltilmiş-metrik ÜÇLÜSÜ; buy-hold karşılaştırması; reliability diagram verisi.
• server.py/api.py: rejim-koşullu IC, deflated Sharpe, PBO, canlı-vs-backtest hit-rate paneli.

## Makale Taslağı

MAKALE TASLAĞI: "Borsa Hareketleri Yüksek Oranda Öngörülebilir mi? BIST ve ABD Hisselerinde Çok-Ufuklu, Rejim-Koşullu, Sızıntısız Bir Sınama"

1) GİRİŞ & TEZ. Güçlü iddia: "kısa-orta vadeli yön, rejim-koşullu özelliklerle martingale-üstü ve çoklu-test-düzeltilmiş anlamlı şekilde öngörülebilir." Karşı-tez (EMH semi-strong): lagging indikatörlerin maliyet-sonrası OOS edge'i yok.

2) HİPOTEZLER (önceden-kayıtlı, falsifiable):
   H1: Çok-ölçekli momentum özellikleri (1-12 ay) forward-return ile martingale-null üstünde anlamlı IC taşır (OOS, çoklu-test-düzeltilmiş).
   H2: Rejim-koşullu (Hurst/ADX) tahmin, koşulsuzdan anlamlı daha yüksek IC verir.
   H3: Ham teknik indikatör sinyalleri (MA/MACD/SuperTrend/Ichimoku/divergence) baseline üstünde anlamlı artı-değer VERMEZ (null'ı destekleme bekleniyor).
   H4: Saatlik öngörünün büyük kısmı mikroyapı (intraday reversal) kaynaklıdır; mid-price'ta küçülür.
   H5: Duygu özellikleri fiyat-only üstünde marjinal IC katkısı yapar (canlı doğrulama).

3) VERİ. 9 BIST + 7 US hisse (yakında coin); saatlik/günlük/haftalık bar (yfinance). Duygu: Reddit/StockTwits/RSS/KAP → finsent pipeline. Dönem + örneklem boyutu, mid-price, spread/maliyet varsayımları açık.

4) YÖNTEM. Triple-barrier etiketleme; purged+embargoed walk-forward CV; rejim koşullama; rule+ML+meta ensemble; deflated Sharpe / PBO / permütasyon / SPA / FDR. Üç-katmanlı raporlama (ham/maliyet, IS/OOS, düzeltilmiş).

5) BEKLENEN SONUÇLAR. Momentum (orta ufuk) ve rejim-koşullama anlamlı ama MÜTEVAZI IC (~0.02-0.05); ham indikatörler ve divergence anlamsız; saatlik edge mid-price'ta erir; duygu marjinal/haber-günü koşullu katkı. "YÜKSEK oranda öngörülebilir" iddiası muhtemelen REDDEDİLİR, "zayıf-orta, rejim/ufuk-koşullu, maliyet-kırılgan öngörülebilirlik" desteklenir.

6) TEZİN REDDEDİLECEĞİ KOŞULLAR (FALSIFIABILITY — zorunlu): Tez ŞU DURUMLARDA REDDEDİLİR: (a) OOS IC, permütasyon-null'dan FDR-düzeltilmiş anlamlı farklı DEĞİLSE; (b) deflated Sharpe ≤ 0 veya PBO > %50; (c) sinyal buy-hold + random-sign'ı OOS'ta yenmiyorsa; (d) maliyet/mid-price sonrası edge sıfırlanıyorsa; (e) canlı predictions hit-rate'i ~%50'ye (yön için şans) yakınsıyorsa. Bu kriterler ÖNCEDEN sabitlenir; sonradan gevşetilmez (HARKing yasak).

7) TARTIŞMA. EMH ile uyum (zayıf öngörü ≠ işlem-edilebilir alfa); decay/kalabalıklaşma; BIST mikroyapı; vol-ölçekleme artefaktı; sağlayıcı-yanlılığı (AQR 1880-serisi bağımsız teyit).

8) KISITLAR. Kısa OOS, tek evren, transaction-cost varsayımları, Hurst gürültüsü, duygu-geçmişi yokluğu.

## Yol Haritası (basitten profesyonele)

AŞAMALI YOL HARİTASI (basit → profesyonel; her aşamada ne eklenir / nasıl ölçülür / başarı eşiği):

AŞAMA 0 — TEMEL DÜRÜSTLÜK (mevcut sızıntıyı kapat). EKLE: validation.py (purged+embargoed walk-forward), benchmarks.py (buy-hold, random-walk, random-sign). ÖLÇ: OOS hit-rate ve IC, buy-hold'a karşı. EŞİK: CV altyapısı çalışıyor; OOS IC raporlanabiliyor; IS-OOS farkı görünür (overfit teşhisi). Bu aşama olmadan sonraki her sayı şüpheli.

AŞAMA 1 — İSTATİSTİKSEL GEÇERLİK. EKLE: stats.py (permütasyon testi, deflated Sharpe, PBO, FDR/SPA). ÖLÇ: OOS IC'nin martingale-null'dan farkı (p-değeri), deflated Sharpe, PBO. EŞİK: en az bir özellik ailesi FDR-düzeltilmiş p<0.05 VE PBO<%50. Aksi halde "öngörü yok" — bu da bilimsel bir sonuç.

AŞAMA 2 — DOĞRU SİNYALLER. EKLE: features.py momentum/reversal/gün-içi aileleri, labeling.py triple-barrier. ÖLÇ: aile-bazında OOS rank-IC; ablation (her aile baseline üstünde artı-değer). EŞİK: momentum ailesi pozitif anlamlı OOS IC; ham indikatör aileleri (MA/MACD) ablation'da anlamsız (beklenen). 

AŞAMA 3 — REJİM KOŞULLAMA. EKLE: regime.py (Hurst/ADX/vol). ÖLÇ: rejim-koşullu vs koşulsuz OOS IC. EŞİK: koşullama IC'yi anlamlı artırıyor (H2 desteklenir) VE rejim sınıflandırması look-ahead'siz.

AŞAMA 4 — META-MODEL + KALİBRASYON. EKLE: forecast.py MetaForecaster, kalibre confidence (Platt/isotonic). ÖLÇ: Brier skoru, reliability diagram (predictions verisi). EŞİK: confidence kalibre (yüksek-güven tahminler gerçekten daha isabetli); Brier < naif baseline.

AŞAMA 5 — ÇOK-UFUK + ÇAPRAZ-KESİT. EKLE: günlük/haftalık bar, cross_section.py rank-momentum. ÖLÇ: her ufuk×rejim hücresinde ayrı metrik; cross-sectional rank-IC. EŞİK: uzun-ufuk momentum OOS'ta pozitif; saatlik edge mid-price sonrası ölçülmüş (erise bile RAPORLA — H4 testi).

AŞAMA 6 — CANLI DOĞRULAMA + DUYGU ABLATION. EKLE: SENT_PRIORS öğrenme, canlı predictions analizi. ÖLÇ: canlı vs backtest hit-rate; fiyat-only vs fiyat+duygu IC. EŞİK: canlı hit-rate backtest'in makul yakınında (decay sınırlı); duygu marjinal pozitif katkı (yoksa dürüstçe "duygu öngörü katmıyor" raporla).

AŞAMA 7 — PROFESYONEL. EKLE: coin evreni (aynı OOS/maliyet disiplini), config.yaml, otomatik haftalık re-kalibrasyon, tam üç-katmanlı dashboard. EŞİK: tüm tez kriterleri (paper_outline §6) önceden-kayıtlı şekilde değerlendirildi; sonuç (destek VEYA red) yayınlanabilir.

## Riskler ve Azaltımlar

EN BÜYÜK BİLİMSEL/TEKNİK RİSKLER VE AZALTIMLARI:

1) OVERFIT / DATA-SNOOPING (en büyük). Çok indikatör×eşik×parametre×ufuk denenince "en iyi" şans eseri çıkar. MEVCUT finsent'te çoklu-test düzeltmesi YOK. AZALTIM: deflated Sharpe (denenen-deneme sayısına göre), PBO, White Reality Check/SPA, FDR. Parametre SADECE in-sample seçilir, OOS'ta dondurulur. Parsimony (az parametreli model tercih).

2) SIZINTI (mevcut, somut). backtest._pool tüm barları havuzlar; scaler/ML tüm örnekte fit edilip aynı havuzda backtest edilir → in-sample optimizm. Divergence pivot'u, bar-içi sinyal, ileri-kaydırma ek sızıntı kaynakları. AZALTIM: purged+embargoed walk-forward (validation.py, ÖNCELİK 1); kapanış-teyitli t+1 sinyal; divergence YASAK; özellik closes[:i+1] korunur.

3) EMH / ÖNGÖRÜLEMEZLİK NULL'I. Tez "yüksek öngörülebilirlik" iddia ediyor ama semi-strong EMH + STW 1999 lagging indikatörlerin OOS edge'i olmadığını söylüyor. RİSK: bulunan "edge" istatistiksel gürültü veya işlem-edilemez. AZALTIM: martingale/random-walk null'a karşı zorunlu test; "öngörülebilirlik ≠ işlem-edilebilir alfa" ayrımı; mütevazı IC beklentisi; falsifiability kriterleri önceden sabit.

4) REJİM KAYMASI / DECAY / KALABALIKLAŞMA. McLean-Pontiff ~%58 yayın-sonrası erime; momentum 2011-2019 yatay; 50/200 ve klasik MACD kalabalık. RİSK: geçmiş edge gelecekte yok. AZALTIM: son-dönem OOS'a daha çok ağırlık; canlı predictions ile sürekli izleme; rejim-koşullu model; backtest-canlı hit-rate farkını decay teşhisi olarak kullan; standart-dışı pencereler (ama çoklu-test düzeltmesiyle).

5) VERİ KALİTESİ / MİKROYAPI (özellikle BIST). Geniş spread + düşük likidite → bid-ask bounce SAHTE reversal "öngörüsü" üretir; yfinance saatlik veri boşluk/hata. RİSK: yapay şişmiş IC. AZALTIM: mid-price (high+low)/2; en illikit hisselerde reversal filtrele; saatlik veri boşluk-kontrolü; intraday vs overnight ayrımı; BIST asimetrisi (boğada iyi, ayıda zayıf) raporla.

6) ÇOKLU TEST (yukarıyla bağlı, ayrı vurgu). 16 hisse × çok ufuk × çok özellik × çok rejim = yüzlerce hipotez. RİSK: %5 anlamlılıkla onlarca sahte-pozitif. AZALTIM: Benjamini-Hochberg FDR / Bonferroni; aile-bazında değerlendirme; önceden-kayıtlı hipotez seti (HARKing yasak).

7) VOL-ÖLÇEKLEME ARTEFAKTI. TSMOM Sharpe'ının çoğu pozisyon-boyutlandırmadan gelebilir (Kim-Tse-Wald) — öngörü sanılır. AZALTIM: ölçekli vs ölçeksiz AYRI raporla; öngörülebilirlik ölçerken vol-ölçeklemeyi risk-yönetiminden ayır.

8) MOMENTUM CRASH / KUYRUK RİSKİ. V-dönüşlerinde (2009 tipi) biriken alfa haftalarda silinir; ortalama Sharpe bunu gizler. AZALTIM: kuyruk/drawdown metrikleri; rejim filtresi (panik+yüksek-vol); ortalama yanında dağılım raporla.

9) CONFIDENCE YANILSAMASI. forecast.predict'teki güven uydurma formül; kalibre değil. RİSK: "güven %80" yanıltıcı. AZALTIM: meta-model + isotonic/Platt kalibrasyon; reliability diagram; Brier.

10) DUYGU KANITSIZLIĞI. SENT_PRIORS elle; geçmiş duygu yok, backtest edilemez. RİSK: duygu "çalışıyor" sanrısı. AZALTIM: yalnız canlı predictions ablation'ı; fiyat-only baseline'a karşı marjinal IC; katkı yoksa dürüstçe reddet.

11) SAĞLAYICI YANLILIĞI. AQR 1880-serisi managed-futures satıcısından, geriye-dönük kurgu. AZALTIM: bağımsız akademik kaynakla teyit; tek-kaynak (Ichimoku blog, CCI %60-70 iddiası) bulguları "anecdotal" işaretle, güvenme.


---
## Uzman Yorumu (Claude)

**1. Sentezin #1 bulgusunu kod-seviyesinde onaylıyorum.** `backtest._pool` gerçekten tüm
barları havuzluyor, scaler tüm örnekte fit ediliyor, ML aynı havuzda eğitilip ölçülüyor
(ben yazdım, doğru teşhis). Bu, bildirdiğimiz IC≈0.024 / hit≈0.51'i bile **yukarı-yanlı**
yapıyor — gerçek OOS muhtemelen daha düşük. `validation.py` (purged+embargoed walk-forward)
gelmeden üretilen hiçbir sayı bilimsel değil. **Stage 0 = tek kapı.**

**2. Tezi dürüstçe yeniden çerçeveliyorum.** Araştırma kendi içinde öngörüyor: "yüksek
oranda öngörülebilir" iddiası muhtemelen **reddedilecek**; desteklenen sonuç "zayıf-orta,
rejim/ufuk-koşullu, maliyet-kırılgan öngörülebilirlik". Bunu başarısızlık değil **asıl
bilimsel kazanım** olarak konumlamalıyız: martingale'i çoklu-test-düzeltilmiş OOS'ta yenen
*kalibre, koşullu* bir edge — yayınlanabilir ve "borsa tahmin edilebilir" pop-iddiasından
çok daha savunulabilir. İddiayı küçültmüyoruz, **ispatlanabilir kılıyoruz.**

**3. LLM dip-notu burada kilitleniyor.** Sentez "duygu kanıtsız, ablation et" diyor (H5);
dip-notum bunun NASIL'ı: LLM'i ham duygu skoru değil **sürpriz/yenilik/olay-tipi/nedensel-
iletim/kesitsel-göreli-sıra** üreticisi yap; magnitude tarihten, yön LLM'den, ispat
forward-only. Marjinal katkı en çok **haber-günü/yüksek-hacim rejiminde** beklenir — sentezin
rejim-koşullama fikriyle birebir örtüşür.

**4. Opus 4.8 için asıl kaldıraç (uç fikir).** LLM'i yalnız özellik üreticisi değil,
**bilimsel doğrulama döngüsünün adversarial denetçisi** yap: her iddia edilen edge'i bir
"kırmızı-takım" ajanı çürütmeye çalışsın (data-snooping, sızıntı, sağlayıcı-yanlılığı). Bu
workflow'da zaten yaptık; kalıcı modüle çevirmek makalenin "Claude Code benchmark" kimliğine
oturur — model hem üretir hem kendi çıktısını bilimsel yargılar.

**5. En yüksek beklenen-değerli sinyal eksiği:** momentumun gerçek kanıt bölgesi **1-12 ay**;
biz sadece saatlik ret1/3/6 kullanıyoruz. Çok-ölçekli (gün/hafta/ay/çeyrek) ölçeklenmiş
getiri + işaret, vol-ölçekli/ölçeksiz ayrı — Stage 2'nin çekirdeği.

**6. Saatlik ufuk hakkında sert gerçek:** senin en çok ilgilendiğin saatlik tahminin büyük
kısmı (Hurst + mikroyapı) **geçici likidite baskısı**, temel yön değil; BIST geniş spread'i
bunu sahte şişiriyor. Mid-price şart; saatlik "edge" mid-price sonrası erirse bu da bir sonuç
(H4) — gizlemeyiz.

**Sıradaki iş kalemi önerisi:** Stage 0'ı kodla (`validation.py` + `benchmarks.py`), mevcut
forecast'ı gerçek OOS'ta yeniden ölç → ilk dürüst sayı. Portföy sentezi gelince bağla.
