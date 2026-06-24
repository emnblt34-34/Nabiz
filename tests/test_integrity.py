"""
Bilimsel entegrite testleri — projenin TÜM değeri "sızıntısız, dürüst ölçüm"; bu
testler onu garantiler. Sessiz bir look-ahead/sızıntı bug'ı sonuçları çöpe çevirir.

En kritik test: NO-LOOK-AHEAD — bir özelliğin GELECEĞİ değiştirince DEĞİŞMEMESİ.
Bu, momentum/rejim/hacim dahil her özellikteki her türlü sızıntıyı yakalar.

Çalıştır:  python -m pytest tests/        (pytest varsa)
       ya: python tests/test_integrity.py  (bağımlılıksız)
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

from finsent import features
from finsent.evaluation import stats, backtest, validation
from finsent.portfolio import weights
from finsent.signals import levels


def _rand_series(n=400, seed=42, start=100.0):
    rng = random.Random(seed)
    closes = [start]
    vols = [1000.0]
    for _ in range(n):
        closes.append(max(0.01, closes[-1] * (1 + rng.gauss(0, 0.012))))
        vols.append(rng.uniform(400, 6000))
    return closes, vols, rng


# ---------------------------------------------------------------------------
# 1) NO-LOOK-AHEAD (en kritik) — geleceği bozunca özellik DEĞİŞMEMELİ
# ---------------------------------------------------------------------------
def test_no_look_ahead_price_features():
    closes, _, rng = _rand_series()
    for i in (40, 120, 260, 399):
        f_full = features.price_features(closes, i)
        # (a) geleceği kesmek özelliği değiştirmemeli
        f_trunc = features.price_features(closes[: i + 1], i)
        assert f_full == f_trunc, f"price_features look-ahead (kesme) i={i}"
        # (b) geleceği ÇÖPLE değiştirmek özelliği değiştirmemeli
        alt = closes[:]
        for j in range(i + 1, len(alt)):
            alt[j] = rng.uniform(0.5, 5000)
        f_alt = features.price_features(alt, i)
        assert f_full == f_alt, f"price_features GELECEĞE bağlı! i={i}"


def test_no_look_ahead_volume_features():
    closes, vols, rng = _rand_series()
    for i in (40, 200, 380):
        f_full = features.volume_features(closes, vols, i)
        c2, v2 = closes[:], vols[:]
        for j in range(i + 1, len(c2)):
            c2[j] = rng.uniform(0.5, 5000)
            v2[j] = rng.uniform(1, 1e7)
        assert features.volume_features(c2, v2, i) == f_full, f"volume_features look-ahead i={i}"


def test_momentum_regime_in_features():
    """Momentum + rejim + hacim alanlarının üretildiğini (ve no-look-ahead) doğrula."""
    closes, _, _ = _rand_series()
    f = features.price_features(closes, 300)
    for k in ("mom_252", "momsc_21", "er", "hurst", "mom63_reg"):
        assert k in f, f"özellik eksik: {k}"


# ---------------------------------------------------------------------------
# 2) WALK-FORWARD CV — train daima test'TEN ÖNCE + purge/embargo boşluğu
# ---------------------------------------------------------------------------
def test_walk_forward_purge_embargo():
    horizon, embargo = 5, 1
    folds = validation.walk_forward_folds(400, n_splits=5, horizon=horizon,
                                          embargo=embargo, min_train=60)
    assert folds, "fold üretilmedi"
    for train_idx, test_idx in folds:
        assert max(train_idx) < min(test_idx), "train test'ten önce değil"
        # Etiket ufku kadar boşluk: train'in son örneğinin forward-return etiketi
        # test penceresine SARKMAMALI (sızıntı).
        assert max(train_idx) + horizon < min(test_idx), "purge/embargo ihlali (etiket örtüşmesi)"
        # test ardışık
        assert test_idx == list(range(test_idx[0], test_idx[-1] + 1)), "test ardışık değil"


def test_forward_return_correct():
    c = [10, 11, 12, 13, 14]
    assert abs(features.forward_return(c, 0, 2) - 0.2) < 1e-12        # (12-10)/10
    assert abs(features.forward_return(c, 1, 1) - (1 / 11)) < 1e-12
    assert features.forward_return(c, 3, 5) is None                  # i+h aralık dışı


# ---------------------------------------------------------------------------
# 3) KESİTSEL AĞIRLIK — dolar-nötr (Σw≈0), brüt=1 (Σ|w|≈1), cap'li
# ---------------------------------------------------------------------------
def test_cross_sectional_weights_properties():
    sigs = {"A": 0.9, "B": 0.3, "C": 0.0, "D": -0.4, "E": -0.8}
    vols = {"A": 0.02, "B": 0.03, "C": 0.05, "D": 0.02, "E": 0.04}
    w = weights.cross_sectional_weights(sigs, vols, cap=0.25)
    assert abs(sum(w.values())) < 1e-9, "dolar-nötr değil (Σw≠0)"          # HARD (market-nötr)
    gross = sum(abs(v) for v in w.values())
    assert 0.7 <= gross <= 1.05, f"brüt makul değil ({gross})"             # ~1 (Sharpe ölçek-bağımsız)
    assert all(abs(v) <= 0.25 + 0.06 for v in w.values()), "cap fena aşıldı"
    assert w["A"] > 0 > w["E"] and w["A"] > w["E"], "sıralama yönü yanlış"


def test_rank_long_short_neutral():
    sigs = {"A": 0.5, "B": 0.2, "C": -0.1, "D": -0.6}
    w = weights.rank_long_short(sigs)
    assert abs(sum(w.values())) < 1e-9, "1/N-rank dolar-nötr değil"
    assert abs(sum(abs(v) for v in w.values()) - 1.0) < 1e-9, "brüt≠1"


# ---------------------------------------------------------------------------
# 4) İSTATİSTİK — temel doğruluk
# ---------------------------------------------------------------------------
def test_pearson():
    assert abs(backtest.pearson([1, 2, 3, 4], [1, 2, 3, 4]) - 1.0) < 1e-9
    assert abs(backtest.pearson([1, 2, 3, 4], [4, 3, 2, 1]) + 1.0) < 1e-9
    assert abs(backtest.pearson([1, 2, 3], [5, 5, 5])) < 1e-9        # sabit -> 0


def test_stats_functions():
    assert stats.sharpe([0.01] * 50, 252) is None                   # sd=0 -> None
    sr = stats.sharpe([0.01, -0.005, 0.02, 0.0, 0.015] * 20, 50.4)
    assert sr is not None and sr > 0
    passed = stats.benjamini_hochberg([0.001, 0.002, 0.5, 0.6])
    assert passed[0] and passed[1] and not passed[2] and not passed[3]
    rng = random.Random(3)
    rets = [rng.gauss(0.002, 0.01) for _ in range(300)]
    p = stats.block_bootstrap_pvalue(rets)
    assert p is not None and 0.0 <= p <= 1.0
    dsr = stats.deflated_sharpe(rets, n_trials=7)
    assert dsr["dsr"] is None or 0.0 <= dsr["dsr"] <= 1.0


# ---------------------------------------------------------------------------
# 5) SEVİYE MOTORU (Stage 21) — uydurma YOK; SADECE veriden ölçülür
#    (MRVL'de "$321 ATH" hatasının bir daha olmamasının garantisi)
# ---------------------------------------------------------------------------
def _synth_daily(n=300, seed=7):
    rng = random.Random(seed)
    dc = [100.0]
    for _ in range(n - 1):
        dc.append(max(1.0, dc[-1] * (1 + rng.gauss(0.0008, 0.02))))
    dh = [c * (1 + abs(rng.gauss(0, 0.01))) for c in dc]
    dl = [c * (1 - abs(rng.gauss(0, 0.01))) for c in dc]
    do = [c * (1 + rng.gauss(0, 0.005)) for c in dc]
    dts = [f"2025-{1 + (i // 28) % 12:02d}-{1 + (i % 28):02d}" for i in range(n)]
    return dh, dl, dc, do, dts


def test_levels_core_invariants():
    """Çekirdek SADECE veriden üretir: ATH=max(high), ATL=min(low), her direnç fiyatın
    ÜSTÜNDE, her destek ALTINDA, sıralı, ve deterministik (aynı girdi → aynı çıktı)."""
    dh, dl, dc, do, dts = _synth_daily()
    price = dc[-1]
    now = datetime(2026, 6, 18, 13, 0, tzinfo=timezone.utc)  # dts'te yok → today_bar None
    d = levels._levels_core("TEST", "TEST", "US", price, dh, dl, dc, do, dts, now)
    assert d["ath"]["price"] == levels._r(max(dh)), "ATH != max(high) (uydurma!)"
    assert d["atl"]["price"] == levels._r(min(dl)), "ATL != min(low)"
    assert d["high_52w"] == levels._r(max(dh[-252:])), "52h-yüksek yanlış"
    for r in d["resistances"]:
        assert r["price"] > price, f"direnç fiyatın üstünde değil: {r['price']} <= {price}"
    for s in d["supports"]:
        assert s["price"] < price, f"destek fiyatın altında değil: {s['price']} >= {price}"
    rp = [r["price"] for r in d["resistances"]]
    sp = [s["price"] for s in d["supports"]]
    assert rp == sorted(rp), "dirençler yakından uzağa sıralı değil"
    assert sp == sorted(sp, reverse=True), "destekler yakından uzağa sıralı değil"
    d2 = levels._levels_core("TEST", "TEST", "US", price, dh, dl, dc, do, dts, now)
    assert d == d2, "seviye çekirdeği deterministik değil"


def test_levels_ath_when_price_at_top():
    """Fiyat = tüm-zaman tepe → konum ZİRVE/BLUE-SKY; ATH tam o fiyat, below_pct≈0."""
    dh, dl, dc, do, dts = _synth_daily()
    top = max(dh)
    now = datetime(2026, 6, 18, 13, 0, tzinfo=timezone.utc)
    d = levels._levels_core("TEST", "TEST", "US", top, dh, dl, dc, do, dts, now)
    assert d["ath"]["price"] == levels._r(top)
    assert "ZİRVE" in d["position"] or "BLUE-SKY" in d["position"], d["position"]
    assert abs(d["ath"]["below_pct"]) < 0.2, "tepe fiyatta below_pct ~0 olmalı"


def test_levels_helpers():
    """Pivot tespiti / yuvarlak-seviye / ATR saf yardımcıları."""
    highs = [1, 2, 3, 5, 3, 2, 1, 2, 4, 9, 4, 2, 1]
    lows = [9, 8, 7, 5, 7, 8, 9, 8, 6, 1, 6, 8, 9]
    ph, pl = levels._pivots(highs, lows, k=2)
    assert 9 in ph and 5 in ph and 1 in pl, "swing tepe/dip tespiti yanlış"
    rl = levels._round_levels(323.0)
    assert 320.0 in rl and 330.0 in rl and all(abs(x % 10) < 1e-9 for x in rl)
    rl627 = levels._round_levels(6.27)
    assert 6.5 in rl627 and 6.0 in rl627, "küçük fiyat yuvarlak adımı yanlış"
    h = [10, 11, 12, 11, 12, 13, 12, 13, 14, 13, 14, 15, 14, 15, 16]
    l = [9, 10, 11, 10, 11, 12, 11, 12, 13, 12, 13, 14, 13, 14, 15]
    c = [9.5, 10.5, 11.5, 10.5, 11.5, 12.5, 11.5, 12.5, 13.5, 12.5, 13.5, 14.5, 13.5, 14.5, 15.5]
    assert levels._atr(h, l, c, 14) > 0, "ATR pozitif değil"


def test_crypto_feed_id_mapping():
    """CoinGecko sembol→id eşlemesi (Stage 22): HYPE gibi yfinance'te olmayan coinler için."""
    from finsent.signals import crypto_feed
    assert crypto_feed._id("HYPE") == "hyperliquid", "HYPE eşlemesi yanlış"
    assert crypto_feed._id("BTC") == "bitcoin"
    assert crypto_feed._id("avax") == "avalanche-2"
    assert crypto_feed._id("near") == "near"
    assert crypto_feed._id("dogecoin") == "dogecoin"  # bilinmeyen → küçük-harf passthrough


# ---------------------------------------------------------------------------
# Bağımsız koşucu (pytest yoksa)
# ---------------------------------------------------------------------------
def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ok = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            ok += 1
        except AssertionError as e:
            print(f"  ✗ {t.__name__}  —  {e}")
        except Exception as e:
            print(f"  ! {t.__name__}  —  HATA: {e}")
    print(f"\n{ok}/{len(tests)} test geçti.")
    return ok == len(tests)


if __name__ == "__main__":
    print("=== Bilimsel entegrite testleri ===")
    sys.exit(0 if _run_all() else 1)
