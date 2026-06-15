"""
Öngörü modeli — gün içi (birkaç saat) yön + güven üretir.

İki backend, ortak arayüz (sentiment.py'deki desenin aynısı):
  1) RuleForecaster — ŞEFFAF. Fiyat özelliklerinin ağırlığı backtest'ten gelen
     IC'lerle (veriden) belirlenir; duygu özellikleri prior ağırlıkla eklenir.
     Sıfır ek ağır bağımlılık. Varsayılan taban.
  2) MLForecaster — scikit-learn lojistik regresyon. Kuruluysa devreye girer,
     değilse sessizce kurala düşer. Fiyat geçmişinden yönü öğrenir.
  3) BlendForecaster — ikisinin ortalaması ("ikisi birden").

Çıktı (predict): {signal -1..+1, direction up/down/neutral, confidence 0..1,
expected_move_pct, model}.

Güven (confidence) ve beklenen hareket UYDURMA değil: modelin geçmişteki
yön-isabet oranı ve ortalama |getiri|si ile ölçeklenir.
"""
from __future__ import annotations

import math
import json
import hashlib
from datetime import datetime, timezone, timedelta

from . import db, prices, features, backtest
from .config import (
    PRICE_INTERVAL, HORIZON_BARS, NEUTRAL_BAND, SENT_PRIORS,
)


# ---------------------------------------------------------------------------
# Modeller
# ---------------------------------------------------------------------------
class _Base:
    name = "base"
    hit_rate: float | None = None       # backtest yön isabeti (0..1)
    typical_move: float = 0.01          # ortalama |getiri| — beklenen hareket ölçeği

    def signal_only(self, feat: dict) -> float:
        raise NotImplementedError

    def predict(self, feat: dict) -> dict:
        s = max(-1.0, min(1.0, self.signal_only(feat)))
        if s >= NEUTRAL_BAND:
            direction = "up"
        elif s <= -NEUTRAL_BAND:
            direction = "down"
        else:
            direction = "neutral"
        # Güven: sinyal şiddeti + modelin geçmiş kenarı (hit_rate-0.5).
        edge = (self.hit_rate - 0.5) if self.hit_rate is not None else 0.0
        conf = 0.5 + abs(s) * 0.4 + max(edge, 0.0) * 2.0
        conf = max(0.5, min(0.92, conf))
        return {
            "signal": round(s, 4),
            "direction": direction,
            "confidence": round(conf, 3),
            "expected_move_pct": round(s * self.typical_move * 100, 3),
            "model": self.name,
        }


class RuleForecaster(_Base):
    """Şeffaf kural: standardize fiyat özellikleri × IC ağırlığı + duygu prior'ları."""
    name = "rule"

    def __init__(self, scaler: dict, price_w: dict):
        self.scaler = scaler
        self.price_w = price_w

    def signal_only(self, feat: dict) -> float:
        price = 0.0
        for f in features.PRICE_FEATURES:
            m, s = self.scaler.get(f, (0.0, 1.0))
            z = (feat.get(f, 0.0) - m) / (s or 1.0)
            price += self.price_w.get(f, 0.0) * z
        sent = sum(SENT_PRIORS.get(f, 0.0) * feat.get(f, 0.0) for f in features.SENT_FEATURES)
        return math.tanh(price + sent)


class MLForecaster(_Base):
    """scikit-learn lojistik regresyon. Standardize özelliklerden P(yukarı)."""
    name = "ml"

    def __init__(self, model, scaler: dict):
        self.model = model
        self.scaler = scaler

    def _z(self, feat: dict) -> list[float]:
        return [(feat.get(f, 0.0) - self.scaler.get(f, (0.0, 1.0))[0])
                / (self.scaler.get(f, (0.0, 1.0))[1] or 1.0) for f in features.FEATURES]

    def signal_only(self, feat: dict) -> float:
        proba_up = float(self.model.predict_proba([self._z(feat)])[0][1])
        return 2.0 * proba_up - 1.0


class BlendForecaster(_Base):
    """Kural + ML ortalaması. ML yoksa sadece kural."""
    name = "blend"

    def __init__(self, rule: RuleForecaster, ml: MLForecaster | None):
        self.rule = rule
        self.ml = ml

    def signal_only(self, feat: dict) -> float:
        s = self.rule.signal_only(feat)
        if self.ml is not None:
            s = 0.5 * s + 0.5 * self.ml.signal_only(feat)
        return s


# ---------------------------------------------------------------------------
# Eğitim / kalibrasyon
# ---------------------------------------------------------------------------
def _train_ml_from(X: list[dict], y: list[float], scaler: dict) -> MLForecaster | None:
    """Verilen (X,y)'den ML eğitir. SAF: walk-forward CV her fold'un train dilimiyle
    çağırır → sızıntısız. sklearn yoksa/yetersiz/tek-sınıf veride None (kurala düşer)."""
    try:
        from sklearn.linear_model import LogisticRegression
    except Exception:
        return None
    if len(X) < 50:
        return None
    Z = [[(row.get(f, 0.0) - scaler[f][0]) / scaler[f][1] for f in features.FEATURES] for row in X]
    ydir = [1 if r > 0 else 0 for r in y]
    if len(set(ydir)) < 2:
        return None
    try:
        model = LogisticRegression(max_iter=500)
        model.fit(Z, ydir)
    except Exception as e:  # pragma: no cover
        print(f"[forecast] ML eğitilemedi ({e}); kurala düşülüyor.")
        return None
    return MLForecaster(model, scaler)


def fit_from_data(X: list[dict], y: list[float], prefer_ml: bool = True) -> tuple[_Base, dict]:
    """
    Verilen (özellik, getiri) setinden bir forecaster kurar (scaler + IC-ağırlıklı
    kural + opsiyonel ML). SAFTIR — yalnız verilen veriyle fit eder; bu yüzden hem
    canlı fit hem de walk-forward CV'nin her train-fold'u bunu kullanır. hit_rate
    BURADA set EDİLMEZ (ölçüm dışarıda, OOS'ta yapılır).
    """
    cal = backtest.calibrate_from(X, y)
    scaler = cal["scaler"]
    ic = cal["price_ic"]
    tot = sum(abs(v) for v in ic.values()) or 1.0
    price_w = {f: ic[f] / tot for f in ic}     # IC-orantılı, normalize ağırlıklar
    rule = RuleForecaster(scaler, price_w)
    ml = _train_ml_from(X, y, scaler) if prefer_ml else None
    fc: _Base = BlendForecaster(rule, ml) if ml else rule
    fc.typical_move = cal.get("typical_move", 0.01)
    return fc, cal


def train_forecaster(conn, tickers, horizon: int = HORIZON_BARS,
                     prefer_ml: bool = True) -> tuple[_Base, dict, dict]:
    """
    Canlı tahmin için modeli TÜM veriyle fit eder (geleceği tahmin için doğrudur).
    Dönen `bt` SIZINTILI in-sample backtest'tir (fit=ölçüm aynı veri) — yalnızca
    hızlı sağlık göstergesi; bilimsel OOS ölçüm için validation.cross_validate kullan.
    Dönüş: (forecaster, calibration, in_sample_backtest).
    """
    X, y, _ = backtest._pool(conn, list(tickers), horizon)
    fc, cal = fit_from_data(X, y, prefer_ml)
    cal["horizon"] = horizon

    bt = backtest.backtest_forecaster(conn, list(tickers), horizon, fc)
    fc.hit_rate = bt["overall"].get("hit_rate")
    print(f"[forecast] model={fc.name} ml={'var' if isinstance(fc, BlendForecaster) and fc.ml else 'yok'} "
          f"n={cal['n']} in_sample_hit={fc.hit_rate} IC={bt['overall'].get('ic')}")
    return fc, cal, bt


# ---------------------------------------------------------------------------
# Canlı tahmin
# ---------------------------------------------------------------------------
def _latest_score_row(conn, ticker: str):
    for w in ("1h", "24h"):
        row = conn.execute(
            "SELECT * FROM scores WHERE ticker=? AND window=? ORDER BY computed_at DESC LIMIT 1",
            (ticker, w),
        ).fetchone()
        if row:
            return row
    return None


def live_features(conn, ticker: str, interval: str = PRICE_INTERVAL):
    """Bir ticker için anlık özellik vektörü + son fiyat. Veri yetmezse None."""
    c = prices.closes(conn, ticker, interval, limit=80)
    if len(c) < features.MIN_BARS:
        return None
    i = len(c) - 1
    pf = features.price_features(c, i)
    if pf is None:
        return None
    sf = features.sentiment_features(_latest_score_row(conn, ticker))
    return {**pf, **sf}, c[i]


def forecast_all(conn, forecaster: _Base, tickers, interval: str = PRICE_INTERVAL) -> list[dict]:
    """Tüm tickerlar için canlı öngörü üretir."""
    out: list[dict] = []
    for t in tickers:
        lf = live_features(conn, t, interval)
        if not lf:
            continue
        feat, price_at = lf
        pred = forecaster.predict(feat)
        pred.update({"ticker": t, "price_at": price_at, "features": feat})
        out.append(pred)
    return out


def log_predictions(conn, preds: list[dict], horizon: int = HORIZON_BARS,
                    interval_hours: float = 1.0) -> int:
    """Üretilen öngörüleri günlüğe yazar (ufuk dolunca sonuçlanacak)."""
    now = datetime.now(timezone.utc)
    target = (now + timedelta(hours=horizon * interval_hours)).isoformat()
    made = now.isoformat()
    n = 0
    for p in preds:
        pid = hashlib.sha1(f"{p['ticker']}|{made}".encode("utf-8")).hexdigest()[:16]
        db.insert_prediction(
            conn, id=pid, ticker=p["ticker"], made_at=made, horizon_bars=horizon,
            target_ts=target, model=p["model"], signal=p["signal"],
            direction=p["direction"], confidence=p["confidence"],
            expected_move=p["expected_move_pct"], price_at=p["price_at"],
            features=json.dumps(p["features"]),
        )
        n += 1
    return n


def resolve_due(conn, interval: str = PRICE_INTERVAL) -> int:
    """Ufku dolan tahminleri gerçek fiyat hareketiyle eşleyip işaretler."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    resolved = 0
    for p in db.open_predictions(conn):
        if p["target_ts"] > now_iso:
            continue  # henüz olgunlaşmadı
        hit = prices.price_at_or_after(conn, p["ticker"], p["target_ts"], interval)
        if not hit:
            continue  # hedef sonrası bar henüz yok (piyasa kapalı vb.)
        _, close = hit
        base = p["price_at"]
        if not base:
            continue
        realized = (close - base) / base
        rdir = "up" if realized > 0 else "down" if realized < 0 else "neutral"
        correct = 1 if p["direction"] == rdir else 0
        db.resolve_prediction(conn, p["id"], round(realized, 5), rdir, correct, now_iso)
        resolved += 1
    return resolved
