"""
Kesitsel long-short walk-forward backtest — market-nötr "tahmin gücü ölçer".

Stage 2 günlük momentumda anlamlı ama KESİTSEL (rank) bir sinyal bulduk (IC=0.069,
p=0.001) — yön drift'i geçmiyordu. Bu modül o sinyali doğru şekilde hasat eder:
her rebalans tarihinde tüm hisseleri SİNYALE GÖRE sıralayıp dolar-nötr long-short
defter kurar; portföy getirisi = saf sıralama isabeti (piyasa yönü izole).

Sızıntısızlık: validation.walk_forward_folds (purge+embargo) YENİDEN kullanılır;
model her fold'da SADECE geçmiş tarihlerle (pooled, kesitsel) eğitilir. Rebalanslar
ufuk-adımıyla ÖRTÜŞMESİZ → getiri gözlemleri ~bağımsız (Sharpe/bootstrap için temiz).
Bu, pooled (ticker×bar) IC'deki bağımsızlık-şişmesini de doğal olarak çözer.
"""
from __future__ import annotations

from .. import db, features, forecast, fx
from ..evaluation import validation
from ..config import PRICE_INTERVAL, HORIZON_BARS, TICKER_MARKET
from . import weights


def _records(conn, ticker: str, horizon: int, interval: str, usd: bool = False) -> list[dict]:
    """Bir ticker için (date, feat, fwd, vol) kayıtları — no-look-ahead.
    usd=True: BIST USD'ye çevrilir (TL enflasyonu çıkar, ortak para birimi)."""
    if usd:
        closes, dates = fx.usd_series(conn, ticker, interval)
    else:
        rows = db.get_prices(conn, ticker, interval)
        closes, dates = [], []
        for r in rows:
            if r["close"] is not None:
                closes.append(float(r["close"]))
                dates.append(r["ts"][:10])
    # Hacim (para-bağımsız) tarihe göre hizalanır — hacim-olay özellikleri için.
    vmap = {r["ts"][:10]: (r["volume"] or 0.0) for r in db.get_prices(conn, ticker, interval)}
    volumes = [vmap.get(d, 0.0) for d in dates]
    recs = []
    for i in range(features.MIN_BARS - 1, len(closes)):
        pf = features.price_features(closes, i)
        if pf is None:
            continue
        fr = features.forward_return(closes, i, horizon)
        if fr is None:
            continue
        feat = {**pf, **features.volume_features(closes, volumes, i),
                **{k: 0.0 for k in features.SENT_FEATURES}}
        recs.append({"date": dates[i], "feat": feat, "fwd": fr, "vol": pf.get("vol") or 0.0})
    return recs


def cross_sectional_walk_forward(conn, tickers, horizon: int = HORIZON_BARS,
                                 interval: str = PRICE_INTERVAL, n_splits: int = 5,
                                 embargo: int = 1, prefer_ml: bool = True,
                                 usd: bool = False) -> dict:
    """
    Kesitsel L/S walk-forward. Dönüş: {ls_returns, bench_returns (1/N-rank), n_rebalances, ...}.
    Her rebalansta: model(geçmiş) → sinyaller → kesitsel ağırlık → portföy forward getirisi.
    usd=True: BIST USD'ye çevrilir (enflasyon-nötr + ortak para birimi).
    """
    all_recs: list[tuple] = []
    for t in tickers:
        for r in _records(conn, t, horizon, interval, usd=usd):
            all_recs.append((t, r))
    if not all_recs:
        return {"ls_returns": [], "bench_returns": [], "n_rebalances": 0, "horizon": horizon}

    dates = sorted({r["date"] for _, r in all_recs})
    di = {d: k for k, d in enumerate(dates)}
    by_date: dict[str, list] = {}
    for t, r in all_recs:
        by_date.setdefault(r["date"], []).append((t, r))

    # Kripto evrende olabilir (7/24). Rebalans yalnız HİSSE işlem günlerinde olsun
    # (hafta sonu sadece-kripto kesitini ve ufuk örtüşmesini önle).
    eq_count: dict[str, int] = {}
    for t, r in all_recs:
        if TICKER_MARKET.get(t, "US") != "CRYPTO":
            eq_count[r["date"]] = eq_count.get(r["date"], 0) + 1
    has_equity = bool(eq_count)

    folds = validation.walk_forward_folds(len(dates), n_splits=n_splits,
                                          horizon=horizon, embargo=embargo, min_train=60)
    ls_returns: list[float] = []
    bench_returns: list[float] = []
    reb_dates: list[str] = []

    for train_idx, test_idx in folds:
        train_end = train_idx[-1] + 1  # tarih-indeks sınırı (bu tarihten öncesi train)
        train = [(r["feat"], r["fwd"]) for _, r in all_recs if di[r["date"]] < train_end]
        if len(train) < 50:
            continue
        fc, _ = forecast.fit_from_data([a for a, _ in train], [b for _, b in train], prefer_ml)
        # Test penceresinde ÖRTÜŞMESİZ rebalans (her horizon tarihte bir)
        elig = [dates[k] for k in test_idx if (not has_equity or eq_count.get(dates[k], 0) >= 4)]
        for d in elig[::horizon]:
            day = by_date.get(d, [])
            if len(day) < 4:  # kesit için minimum genişlik
                continue
            sigs = {t: fc.signal_only(r["feat"]) for t, r in day}
            vols = {t: r["vol"] for t, r in day}
            fwds = {t: r["fwd"] for t, r in day}
            w = weights.cross_sectional_weights(sigs, vols)
            bw = weights.rank_long_short(sigs)
            ls_returns.append(sum(w[t] * fwds[t] for t in fwds))
            bench_returns.append(sum(bw[t] * fwds[t] for t in fwds))
            reb_dates.append(d)

    return {
        "ls_returns": ls_returns,
        "bench_returns": bench_returns,
        "n_rebalances": len(ls_returns),
        "dates": reb_dates,
        "horizon": horizon,
        "interval": interval,
    }


def _ticker_records_multi(conn, ticker, horizons, interval):
    """Bir ticker: her bar için feat + her ufka forward getiri (no-look-ahead)."""
    rows = db.get_prices(conn, ticker, interval)
    closes: list[float] = []
    dates: list[str] = []
    for r in rows:
        if r["close"] is not None:
            closes.append(float(r["close"]))
            dates.append(r["ts"][:10])
    recs = []
    for i in range(features.MIN_BARS - 1, len(closes)):
        pf = features.price_features(closes, i)
        if pf is None:
            continue
        fwds = {h: features.forward_return(closes, i, h) for h in horizons}
        feat = {**pf, **{k: 0.0 for k in features.SENT_FEATURES}}
        recs.append({"date": dates[i], "feat": feat, "fwds": fwds, "vol": pf.get("vol") or 0.0})
    return recs


def cross_sectional_walk_forward_ensemble(conn, tickers, eval_horizon: int = 5,
                                          train_horizons=(5, 10, 20), interval: str = "1d",
                                          n_splits: int = 5, embargo: int = 1,
                                          prefer_ml: bool = True) -> dict:
    """
    ÇOK-UFUK ENSEMBLE L/S (Stage 4). Her rebalansta, FARKLI ufuklara (5/10/20 gün) eğitilmiş
    modellerin kesitsel sinyallerini ORTALAR → tek defter; eval_horizon getirisiyle ölçer.
    Ufuk çeşitlendirmesi sinyal gürültüsünü düşürür (Hurst-Ooi-Pedersen). Sızıntısız:
    her model fold'un yalnız geçmiş diliminde, kendi ufkunun forward-return'üyle eğitilir.
    """
    horizons = sorted(set(list(train_horizons) + [eval_horizon]))
    maxh = max(horizons)
    all_recs: list[tuple] = []
    for t in tickers:
        for r in _ticker_records_multi(conn, t, horizons, interval):
            if r["fwds"][eval_horizon] is not None:
                all_recs.append((t, r))
    if not all_recs:
        return {"ls_returns": [], "bench_returns": [], "n_rebalances": 0}

    dates = sorted({r["date"] for _, r in all_recs})
    di = {d: k for k, d in enumerate(dates)}
    by_date: dict[str, list] = {}
    for t, r in all_recs:
        by_date.setdefault(r["date"], []).append((t, r))

    folds = validation.walk_forward_folds(len(dates), n_splits=n_splits,
                                          horizon=maxh, embargo=embargo, min_train=60)
    ls_returns: list[float] = []
    bench_returns: list[float] = []
    reb_dates: list[str] = []

    for train_idx, test_idx in folds:
        train_end = train_idx[-1] + 1
        train_recs = [r for _, r in all_recs if di[r["date"]] < train_end]
        if len(train_recs) < 50:
            continue
        models = {}
        for h in train_horizons:
            Xt = [r["feat"] for r in train_recs if r["fwds"][h] is not None]
            yt = [r["fwds"][h] for r in train_recs if r["fwds"][h] is not None]
            if len(Xt) >= 50:
                fc, _ = forecast.fit_from_data(Xt, yt, prefer_ml)
                models[h] = fc
        if not models:
            continue
        for j in range(0, len(test_idx), eval_horizon):
            d = dates[test_idx[j]]
            day = by_date.get(d, [])
            if len(day) < 4:
                continue
            sigs = {t: sum(m.signal_only(r["feat"]) for m in models.values()) / len(models)
                    for t, r in day}
            vols = {t: r["vol"] for t, r in day}
            fwds = {t: r["fwds"][eval_horizon] for t, r in day}
            w = weights.cross_sectional_weights(sigs, vols)
            bw = weights.rank_long_short(sigs)
            ls_returns.append(sum(w[t] * fwds[t] for t in fwds if fwds[t] is not None))
            bench_returns.append(sum(bw[t] * fwds[t] for t in fwds if fwds[t] is not None))
            reb_dates.append(d)

    return {
        "ls_returns": ls_returns,
        "bench_returns": bench_returns,
        "n_rebalances": len(ls_returns),
        "dates": reb_dates,
        "train_horizons": list(train_horizons),
        "eval_horizon": eval_horizon,
        "interval": interval,
    }
