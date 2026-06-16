"""
Canlı kesitsel öngörü — projenin ASIL ölçülen sinyali.

Saatlik panel rozeti gürültüdür (Stage 0: p=0.35). Buradaki sinyal farklıdır: GÜNLÜK,
rejim-koşullu momentumla hisseleri BİRBİRİNE GÖRE sıralar (market-nötr). "Şu hisse çıkar"
demez; "şu hisse, şu diğerinden GÖRECELİ daha güçlü" der — ölçtüğümüz tek gerçek edge bu.

Backtest sicili sınırda-anlamlıdır (5y: Sharpe ~1.1, bootstrap p≈0.006, DSR(7)≈0.91) ve
arayüzde DÜRÜSTÇE gösterilir — "kesin ispat değil" diye. (bkz. docs/sonuclar.md)
"""
from __future__ import annotations

from .. import prices, features, forecast, fx
from ..config import TICKER_MARKET
from ..evaluation import stats
from . import weights, ls_backtest

CS_HORIZON = 5          # gün (ufuk)
CS_INTERVAL = "1d"


def train(conn, tickers, interval: str = CS_INTERVAL, horizon: int = CS_HORIZON,
          usd: bool = True):
    """
    Günlük geçmişten kesitsel modeli eğitir + market-nötr L/S backtest sicilini ölçer.
    usd=True (varsayılan): BIST USD'ye çevrilir — TL enflasyonu artefaktını çıkarır
    (Stage 6 dersi: TL-bazlı "güçlü" sinyal büyük ölçüde kur artefaktıydı).
    Dönüş: (forecaster, record). Veri yetmezse (None, None).
    """
    X: list[dict] = []
    y: list[float] = []
    for t in tickers:
        for r in ls_backtest._records(conn, t, horizon, interval, usd=usd):
            X.append(r["feat"])
            y.append(r["fwd"])
    if len(X) < 100:
        return None, None
    fc, _ = forecast.fit_from_data(X, y, prefer_ml=True)

    bt = ls_backtest.cross_sectional_walk_forward(
        conn, list(tickers), horizon=horizon, interval=interval, n_splits=5, usd=usd)
    rets = bt["ls_returns"]
    ppy = 252 / horizon
    sr = stats.sharpe(rets, ppy) if rets else None
    record = {
        "sharpe": round(sr, 2) if sr is not None else None,
        "bootstrap_p": round(stats.block_bootstrap_pvalue(rets), 4) if len(rets) >= 10 else None,
        "dsr7": round(stats.deflated_sharpe(rets, 7)["dsr"], 3) if rets and stats.deflated_sharpe(rets, 7)["dsr"] is not None else None,
        "n_rebalances": len(rets),
        "horizon_days": horizon,
    }
    return fc, record


def rank_now(conn, fc, tickers, interval: str = CS_INTERVAL, usd: bool = True) -> list[dict]:
    """
    Şu anki kesitsel sıralama: her hissenin son özelliğiyle model sinyali → kesitsel
    dolar-nötr ağırlık → sıralı liste (en güçlü → en zayıf), yön + rejim etiketiyle.
    usd=True: BIST USD'ye çevrilir (para-nötr, eğitimle tutarlı).
    """
    sigs: dict[str, float] = {}
    vols: dict[str, float] = {}
    feats: dict[str, dict] = {}
    for t in tickers:
        c = fx.usd_series(conn, t, interval)[0] if usd else prices.closes(conn, t, interval)
        if len(c) < features.MIN_BARS:
            continue
        feat = features.price_features(c, len(c) - 1)
        if feat is None:
            continue
        feat = {**feat, **{k: 0.0 for k in features.SENT_FEATURES}}
        sigs[t] = fc.signal_only(feat)
        vols[t] = feat.get("vol") or 0.0
        feats[t] = feat
    if len(sigs) < 2:
        return []

    w = weights.cross_sectional_weights(sigs, vols)
    order = sorted(sigs, key=lambda t: sigs[t], reverse=True)
    out = []
    for i, t in enumerate(order):
        wt = w.get(t, 0.0)
        er = feats[t].get("er", 0.5)
        out.append({
            "ticker": t,
            "rank": i + 1,
            "signal": round(sigs[t], 3),
            "weight": round(wt, 3),
            "side": "long" if wt > 0.02 else "short" if wt < -0.02 else "neutral",
            "regime": "trend" if er > 0.55 else "choppy" if er < 0.45 else "nötr",
            "market": TICKER_MARKET.get(t, "US"),
        })
    return out
