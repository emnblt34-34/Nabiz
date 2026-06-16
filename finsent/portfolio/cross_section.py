"""
Canlı kesitsel öngörü — projenin ASIL ölçülen sinyali.

Saatlik panel rozeti gürültüdür (Stage 0: p=0.35). Buradaki sinyal farklıdır: GÜNLÜK,
rejim-koşullu momentumla hisseleri BİRBİRİNE GÖRE sıralar (market-nötr). "Şu hisse çıkar"
demez; "şu hisse, şu diğerinden GÖRECELİ daha güçlü" der — ölçtüğümüz tek gerçek edge bu.

Backtest sicili sınırda-anlamlıdır (5y: Sharpe ~1.1, bootstrap p≈0.006, DSR(7)≈0.91) ve
arayüzde DÜRÜSTÇE gösterilir — "kesin ispat değil" diye. (bkz. docs/sonuclar.md)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from .. import db, prices, features, forecast, fx
from ..config import TICKER_MARKET
from ..evaluation import stats, backtest
from . import weights, ls_backtest

CS_HORIZON = 5          # gün (ufuk)
CS_INTERVAL = "1d"

# Güven (confidence) — KALİBRE EDİLDİ (run_confidence_research.py, 216k OOS nokta):
# momentum-hizalama(0.6)+trend-rejimi(0.4) → düşük<0.40 isabet~0.49, orta~0.53, yüksek≥0.66 ~0.59.
# "güven"i iddia etmiyoruz; ölçülen isabetle gösteriyoruz. Yüksek NADİR (~%0.2).
_CONF_LOOKBACKS = [21, 63, 126, 252]


def _sgn(x: float) -> int:
    return 1 if x > 0 else -1 if x < 0 else 0


def _confidence(feat: dict, signal: float) -> float:
    s = _sgn(signal)
    if s == 0:
        return 0.0
    align = sum(1 for n in _CONF_LOOKBACKS if _sgn(feat.get(f"mom_{n}", 0.0)) == s) / len(_CONF_LOOKBACKS)
    er = feat.get("er", 0.5)
    regime = max(0.0, min(1.0, (er - 0.45) / 0.20))
    return round(0.6 * align + 0.4 * regime, 3)


def _conf_label(conf: float):
    """Dönüş: (etiket, ölçülen_isabet)."""
    if conf >= 0.66:
        return "yüksek", 0.59
    if conf >= 0.40:
        return "orta", 0.53
    return "düşük", 0.49


def _why(feat: dict, signal: float, news_n: int, side: str) -> list[str]:
    """'Alım/satım gücü neden?' — haber DEĞİL, ölçülen teknik sürücüler (momentum+rejim+hacim)."""
    s = _sgn(signal)
    aligned = sum(1 for n in _CONF_LOOKBACKS if _sgn(feat.get(f"mom_{n}", 0.0)) == s)
    er = feat.get("er", 0.5)
    why = [f"{aligned}/4 momentum ufku (≈1–12 ay) sinyalle aynı yönde"
           + (" — hizalı" if aligned >= 3 else " — karışık")]
    if er > 0.55:
        why.append(f"trend rejimi (ER={er:.2f}) → momentum güvenilir")
    elif er < 0.45:
        why.append(f"choppy rejim (ER={er:.2f}) → momentum zayıf/dönüşlü")
    else:
        why.append(f"nötr rejim (ER={er:.2f})")
    vt = feat.get("vol_trend", 0.0)
    if vt > 0.05:
        why.append("hacim trendi artıda (artan ilgi)")
    if feat.get("vol_spike", 0.0) > 1.5:
        why.append("hacim spike (dikkat/olay sinyali)")
    if news_n == 0:
        if side == "long":
            why.append("haber YOK → alım baskısı TEKNİK (çok-ölçekli momentum + trend), haberden değil")
        elif side == "short":
            why.append("haber YOK → zayıflık teknik (momentum aşağı), haberden değil")
    else:
        why.append(f"son 48s {news_n} haber (haber-etki kanalı olası)")
    return why


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
        if usd:
            c, dates = fx.usd_series(conn, t, interval)
        else:
            rows = db.get_prices(conn, t, interval)
            c = [float(r["close"]) for r in rows if r["close"] is not None]
            dates = [r["ts"][:10] for r in rows if r["close"] is not None]
        if len(c) < features.MIN_BARS:
            continue
        vmap = {r["ts"][:10]: (r["volume"] or 0.0) for r in db.get_prices(conn, t, interval)}
        volumes = [vmap.get(d, 0.0) for d in dates]
        last = len(c) - 1
        feat = features.price_features(c, last)
        if feat is None:
            continue
        feat = {**feat, **features.volume_features(c, volumes, last),
                **{k: 0.0 for k in features.SENT_FEATURES}}
        sigs[t] = fc.signal_only(feat)
        vols[t] = feat.get("vol") or 0.0
        feats[t] = feat
    if len(sigs) < 2:
        return []

    # Canlı DUYGU (24h) — momentum sinyalinin yanında göster (haber/yorum katmanı).
    sent_map = {s["ticker"]: (s["sentiment"], s["volume"])
                for s in db.latest_scores(conn, window="24h")}
    # (c) Son 48h HABER sayısı (yf:news + diğer news) — "önemli haber var" göstergesi.
    since = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    news_cnt: dict[str, int] = {}
    for nr in conn.execute(
            "SELECT tickers FROM records WHERE source_type='news' AND created_at>=?", (since,)):
        for tk in json.loads(nr["tickers"]):
            news_cnt[tk] = news_cnt.get(tk, 0) + 1

    w = weights.cross_sectional_weights(sigs, vols)
    order = sorted(sigs, key=lambda t: sigs[t], reverse=True)
    out = []
    for i, t in enumerate(order):
        wt = w.get(t, 0.0)
        er = feats[t].get("er", 0.5)
        sent, sv = sent_map.get(t, (None, 0))
        side = "long" if wt > 0.02 else "short" if wt < -0.02 else "neutral"
        nn = news_cnt.get(t, 0)
        conf = _confidence(feats[t], sigs[t])
        clabel, chit = _conf_label(conf)
        out.append({
            "ticker": t,
            "rank": i + 1,
            "signal": round(sigs[t], 3),
            "weight": round(wt, 3),
            "side": side,
            "regime": "trend" if er > 0.55 else "choppy" if er < 0.45 else "nötr",
            "market": TICKER_MARKET.get(t, "US"),
            "sentiment": round(sent, 3) if sent is not None else None,
            "sent_n": sv or 0,
            "news_n": nn,                    # son 48h haber sayısı
            "confidence": conf,             # kalibre güven-proxy [0..1]
            "conf_label": clabel,           # düşük/orta/yüksek
            "conf_hit": chit,               # bu kovanın ÖLÇÜLEN OOS isabeti
            "why": _why(feats[t], sigs[t], nn, side),  # alım/satım gücü nedeni (teknik)
        })
    return out


# ---------------------------------------------------------------------------
# (b) Forward SENTIMENT ABLATION — duygu fiyat-ötesi öngörü katıyor mu?
# Geçmişe backtest EDİLEMEZ (tarihsel duygu yok); tek dürüst yol bu ileriye-dönük A/B.
# Günde bir kez logla, ufuk dolunca gerçek getiriyle eşle, marjinal katkıyı ölç.
# ---------------------------------------------------------------------------
def log_ablation(conn, ranking: list[dict], horizon_days: int = 5) -> int:
    """Bugün için her hisseye: fiyat-sinyali + canlı duygu + USD fiyat logla (1/gün)."""
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    if conn.execute("SELECT 1 FROM cs_ablation WHERE made_at LIKE ? LIMIT 1",
                    (today + "%",)).fetchone():
        return 0  # bugün zaten loglandı
    made = now.isoformat()
    target = (now + timedelta(days=horizon_days)).isoformat()
    n = 0
    for it in ranking:
        t = it["ticker"]
        closes, _ = fx.usd_series(conn, t, CS_INTERVAL)
        if not closes:
            continue
        conn.execute(
            """INSERT OR IGNORE INTO cs_ablation
               (id, made_at, target_ts, ticker, price_signal, sentiment, sent_n, price_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (f"{today}|{t}", made, target, t, it["signal"],
             it.get("sentiment"), it.get("sent_n") or 0, closes[-1]))
        n += 1
    conn.commit()
    return n


def resolve_ablation(conn, interval: str = CS_INTERVAL) -> int:
    """Ufku dolan ablation kayıtlarını USD gerçek getiriyle eşle."""
    now_iso = datetime.now(timezone.utc).isoformat()
    resolved = 0
    for r in conn.execute("SELECT * FROM cs_ablation WHERE realized_return IS NULL").fetchall():
        if r["target_ts"] > now_iso:
            continue
        closes, dates = fx.usd_series(conn, r["ticker"], interval)
        tgt = r["target_ts"][:10]
        close_at = next((c for d, c in zip(dates, closes) if d >= tgt), None)
        if close_at is None or not r["price_at"]:
            continue
        ret = (close_at - r["price_at"]) / r["price_at"]
        conn.execute("UPDATE cs_ablation SET realized_return=?, resolved_at=? WHERE id=?",
                     (round(ret, 5), now_iso, r["id"]))
        resolved += 1
    conn.commit()
    return resolved


def ablation_stats(conn) -> dict:
    """Duygunun MARJİNAL katkısı: fiyat-sinyali kontrol edilince duygu hâlâ öngörü taşıyor mu?"""
    rows = conn.execute(
        """SELECT price_signal, sentiment, realized_return FROM cs_ablation
           WHERE realized_return IS NOT NULL AND sentiment IS NOT NULL""").fetchall()
    n = len(rows)
    open_n = conn.execute("SELECT COUNT(*) c FROM cs_ablation WHERE realized_return IS NULL").fetchone()["c"]
    if n < 30:
        return {"n_resolved": n, "open": open_n,
                "note": "yeterli veri yok — forward birikiyor (geçmişe backtest edilemez)."}
    ps = [r["price_signal"] for r in rows]
    se = [r["sentiment"] for r in rows]
    ry = [r["realized_return"] for r in rows]
    # fiyat-sinyalini regres et, kalıntıya karşı duygu korelasyonu = MARJİNAL katkı
    mp, my = sum(ps) / n, sum(ry) / n
    varp = sum((p - mp) ** 2 for p in ps) or 1e-9
    b = sum((p - mp) * (y - my) for p, y in zip(ps, ry)) / varp
    a = my - b * mp
    resid = [y - (a + b * p) for p, y in zip(ps, ry)]
    return {
        "n_resolved": n, "open": open_n,
        "ic_price": round(backtest.pearson(ps, ry), 4),
        "ic_sent_raw": round(backtest.pearson(se, ry), 4),
        "sent_marginal_partial_corr": round(backtest.pearson(se, resid), 4),
        "note": "sent_marginal > 0 ve büyürse: duygu FİYAT-ÖTESİ öngörü katıyor demektir.",
    }
