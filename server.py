"""
Nabız sunucusu — bilgisayarda çalışır.

Tek süreçte üç iş yapar:
  1) Arka planda her REFRESH_MIN dakikada bir gerçek kaynakları toplar
     (Reddit, StockTwits, RSS haber, KAP) → SQLite'a yazar. Kalıcı geçmiş =
     gerçek momentum. Sosyal veride bot/kredibilite filtresi devrede.
  2) /api/* uçlarından skorları ve GERÇEK yorum/haber örneklerini sunar.
  3) Ana sayfada Nabız arayüzünü (web/dashboard.html) gösterir.

Çalıştır:   python server.py
Sonra aç:   http://localhost:8000
Telefondan (aynı wifi): http://<bilgisayarın-IP>:8000
"""
from __future__ import annotations

import threading
import time
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from finsent import db, prices, forecast, fx
from finsent.portfolio import cross_section
from finsent.pipeline import run_once
from finsent.config import TICKERS, HORIZON_BARS, PRICE_PERIOD_BACKTEST, PRICE_PERIOD_LIVE
from finsent.collectors import (
    RSSNewsCollector, RedditCollector, StockTwitsCollector, KAPCollector, SampleCollector,
)

import os

# --- Ayarlar ---
REFRESH_MIN = 10          # kaç dakikada bir veri toplansın
# Gerçek kaynaklar (varsayılan). İnternetsiz demo için: NABIZ_SAMPLE=1
USE_SAMPLE = os.environ.get("NABIZ_SAMPLE") == "1"
PORT = int(os.environ.get("NABIZ_PORT", "8000"))
RETRAIN_SEC = 6 * 3600    # modeli kaç saniyede bir yeniden eğit (taze barlarla)
CS_PERIOD = "max"         # kesitsel model: USD-bazlı uzun geçmiş (enflasyon-nötr; bkz. Stage 6)

app = FastAPI(title="Nabız")
_state = {"last": 0, "running": False, "stats": None, "error": None}
# Saatlik öngörü durumu (zayıf/gürültü — Stage 0): model + backtest + son tahminler.
_fc = {"model": None, "calibration": None, "backtest": None,
       "latest": [], "trained_at": 0, "error": None}
# Kesitsel öngörü durumu (ASIL ölçülen sinyal): günlük rejim-koşullu momentum, market-nötr.
_cs = {"model": None, "record": None, "ranking": [], "trained_at": 0, "error": None}


def _collectors():
    if USE_SAMPLE:
        return [SampleCollector()]
    return [RSSNewsCollector(), RedditCollector(), StockTwitsCollector(), KAPCollector()]


def _init_forecaster():
    """Bir kez (ve 6 saatte bir): fiyat geçmişini çek, modeli kalibre/eğit, backtest et."""
    try:
        conn = db.connect()
        prices.update_prices(conn, list(TICKERS), period=PRICE_PERIOD_BACKTEST)
        fc, cal, bt = forecast.train_forecaster(conn, list(TICKERS), HORIZON_BARS)
        _fc.update({"model": fc, "calibration": cal, "backtest": bt,
                    "trained_at": time.time(), "error": None})
        conn.close()
        print(f"[forecast] model hazir: {fc.name}, hit_rate={fc.hit_rate}")
    except Exception as e:
        _fc["error"] = str(e)
        print("[forecast] init hata:", e)


def _forecast_cycle():
    """Her döngüde: canlı fiyatı tazele, olgunlaşan tahminleri sonuçla, yeni öngörü üret+logla."""
    if _fc["model"] is None:
        return
    try:
        conn = db.connect()
        prices.update_prices(conn, list(TICKERS), period=PRICE_PERIOD_LIVE)
        forecast.resolve_due(conn)
        preds = forecast.forecast_all(conn, _fc["model"], list(TICKERS))
        forecast.log_predictions(conn, preds, HORIZON_BARS)
        _fc["latest"] = preds
        conn.close()
    except Exception as e:
        print("[forecast] cycle hata:", e)


def _init_cs():
    """Bir kez (ve 6 saatte bir): USDTRY + günlük geçmişi çek, USD-bazlı KESİTSEL modeli eğit."""
    try:
        conn = db.connect()
        fx.update_fx(conn, period=CS_PERIOD, interval="1d")
        prices.update_prices(conn, list(TICKERS), period=CS_PERIOD, interval="1d")
        fc, rec = cross_section.train(conn, list(TICKERS))
        _cs.update({"model": fc, "record": rec, "trained_at": time.time(), "error": None})
        conn.close()
        print(f"[crosssection] model hazir: sicil={rec}")
    except Exception as e:
        _cs["error"] = str(e)
        print("[crosssection] init hata:", e)


def _cs_cycle():
    """Her döngüde: güncel kesitsel sıralamayı (en güçlü → en zayıf) hesapla."""
    if _cs["model"] is None:
        return
    try:
        conn = db.connect()
        _cs["ranking"] = cross_section.rank_now(conn, _cs["model"], list(TICKERS))
        conn.close()
    except Exception as e:
        print("[crosssection] cycle hata:", e)


def _loop():
    """Arka plan döngüsü (daemon thread): önce duygu, sonra öngörü (saatlik + kesitsel)."""
    while True:
        try:
            _state["running"] = True
            _state["error"] = None
            _state["stats"] = run_once(_collectors(), prefer_transformer=False)
            _state["last"] = time.time()
            # Öngörü katmanı (gerçek fiyat ister; sample/offline modda atlanır).
            if not USE_SAMPLE:
                if _fc["model"] is None or (time.time() - _fc["trained_at"] > RETRAIN_SEC):
                    _init_forecaster()
                _forecast_cycle()
                if _cs["model"] is None or (time.time() - _cs["trained_at"] > RETRAIN_SEC):
                    _init_cs()
                _cs_cycle()
        except Exception as e:
            _state["error"] = str(e)
            print("[loop] hata:", e)
        finally:
            _state["running"] = False
        time.sleep(REFRESH_MIN * 60)


@app.on_event("startup")
def _start():
    threading.Thread(target=_loop, daemon=True).start()
    # Not: ok yerine "->" (bazı Windows konsolları '→' karakterini kodlayamayıp çöker).
    print(f"\n  Nabiz calisiyor ->  http://localhost:{PORT}\n")


# ---------------- Arayüz ----------------
@app.get("/", response_class=HTMLResponse)
def index():
    return (Path(__file__).parent / "web" / "dashboard.html").read_text(encoding="utf-8")


# ---------------- API ----------------
@app.get("/api/status")
def status():
    return {
        "last": _state["last"], "running": _state["running"],
        "stats": _state["stats"], "error": _state["error"],
        "refresh_min": REFRESH_MIN, "sample_mode": USE_SAMPLE,
        "forecast_ready": _fc["model"] is not None,
        "forecast_model": _fc["model"].name if _fc["model"] else None,
        "cs_ready": _cs["model"] is not None,
    }


@app.get("/api/scores")
def scores(window: str = "24h"):
    conn = db.connect()
    rows = db.latest_scores(conn, window=window)
    conn.close()
    out = []
    for r in rows:
        out.append({
            "ticker": r["ticker"], "sentiment": r["sentiment"], "momentum": r["momentum"],
            "volume": r["volume"], "posShare": r["pos_share"], "negShare": r["neg_share"],
            "market": "BIST" if r["ticker"] in _BIST else "US",
        })
    return out


@app.get("/api/ticker/{symbol}")
def ticker(symbol: str, limit: int = 30):
    """Bir hisse için skor + GERÇEK haber ve yorum örnekleri (kaynak türüne göre)."""
    symbol = symbol.upper()
    conn = db.connect()
    score = conn.execute(
        "SELECT * FROM scores WHERE ticker=? AND window='24h' ORDER BY computed_at DESC LIMIT 1",
        (symbol,),
    ).fetchone()
    rows = conn.execute("SELECT * FROM records ORDER BY created_at DESC LIMIT 800").fetchall()
    conn.close()

    news, social = [], []
    for r in rows:
        if symbol not in json.loads(r["tickers"]):
            continue
        author = json.loads(r["author"])
        item = {
            "text": r["text"], "source": r["source"], "sentiment": r["sentiment"],
            "score": r["sentiment_score"], "credibility": round(r["credibility"], 2),
            "url": r["url"], "created_at": r["created_at"],
            "author": author.get("handle", "?"),
        }
        if r["source_type"] == "social":
            social.append(item)
        else:
            news.append(item)
        if len(news) + len(social) >= limit:
            break
    return {
        "ticker": symbol,
        "score": dict(score) if score else None,
        "news": news, "social": social,
    }


@app.get("/api/daily")
def daily():
    """Basit günlük özet — AI/anahtar gerektirmez, skorlardan üretilir."""
    conn = db.connect()
    rows = db.latest_scores(conn, window="24h")
    conn.close()
    items = [dict(r) for r in rows if r["volume"]]
    if not items:
        return {"text": "Henüz yeterli veri toplanmadı. Birkaç dakika içinde dolacak."}
    items.sort(key=lambda x: x["sentiment"], reverse=True)
    top = items[0]; bottom = items[-1]
    mover = max(items, key=lambda x: abs(x["momentum"]))
    avg = sum(x["sentiment"] for x in items) / len(items)
    mood = ("genel hava pozitif" if avg > 0.12 else
            "genel hava negatif" if avg < -0.12 else "piyasa kararsız")
    txt = (f"Bugün {len(items)} hissede {mood}. En pozitif {top['ticker']} "
           f"({top['sentiment']:+.2f}), en negatif {bottom['ticker']} ({bottom['sentiment']:+.2f}). "
           f"En sert hareket {mover['ticker']} hissesinde (momentum {mover['momentum']:+.2f}).")
    return {"text": txt}


_BIST = {"THYAO", "GARAN", "ASELS", "SISE", "KCHOL", "EREGL", "AKBNK", "BIMAS", "TUPRS"}


# ---------------- Öngörü (forecast) API ----------------
@app.get("/api/forecast")
def forecast_list():
    """Tüm hisseler için gün içi öngörü + modelin geçmiş (backtest) ve canlı sicili."""
    bt = _fc["backtest"] or {}
    overall = bt.get("overall", {}) or {}
    items = []
    for p in _fc["latest"]:
        items.append({
            "ticker": p["ticker"], "direction": p["direction"], "signal": p["signal"],
            "confidence": p["confidence"], "expectedMovePct": p["expected_move_pct"],
            "priceAt": p["price_at"], "model": p["model"],
            "market": "BIST" if p["ticker"] in _BIST else "US",
        })
    items.sort(key=lambda x: abs(x["signal"]), reverse=True)  # güçlü sinyaller önce
    conn = db.connect()
    live = db.prediction_stats(conn)
    conn.close()
    return {
        "horizonHours": HORIZON_BARS,
        "model": _fc["model"].name if _fc["model"] else None,
        "ready": _fc["model"] is not None,
        "trainedAt": _fc["trained_at"],
        "backtest": {
            "hitRate": overall.get("hit_rate"), "ic": overall.get("ic"),
            "n": overall.get("n"), "nDirectional": overall.get("n_directional"),
        },
        "live": live,
        "error": _fc["error"],
        "items": items,
        "disclaimer": "Backtest fiyat-teknik bileşeninin gercek isabetini olcer; "
                      "duygu katkisi canli (live) sicilde dogrulanir. Yatirim tavsiyesi degildir.",
    }


@app.get("/api/forecast/{symbol}")
def forecast_one(symbol: str):
    """Bir hisse için öngörü detayı: sinyal, özellikler, backtest ve canlı isabet."""
    symbol = symbol.upper()
    bt = _fc["backtest"] or {}
    per = (bt.get("per_ticker") or {}).get(symbol)
    cur = next((p for p in _fc["latest"] if p["ticker"] == symbol), None)
    conn = db.connect()
    live = db.prediction_stats(conn, symbol)
    recent = conn.execute(
        """SELECT made_at, direction, confidence, signal, expected_move,
                  realized_return, correct FROM predictions
           WHERE ticker=? ORDER BY made_at DESC LIMIT 10""",
        (symbol,),
    ).fetchall()
    conn.close()
    fc_out = None
    if cur:
        fc_out = {
            "direction": cur["direction"], "signal": cur["signal"],
            "confidence": cur["confidence"], "expectedMovePct": cur["expected_move_pct"],
            "priceAt": cur["price_at"], "model": cur["model"],
        }
    return {
        "ticker": symbol,
        "horizonHours": HORIZON_BARS,
        "forecast": fc_out,
        "features": cur["features"] if cur else None,
        "backtest": per,
        "live": live,
        "recent": [dict(r) for r in recent],
    }


@app.get("/api/backtest")
def backtest_view():
    """Modelin tüm geçmiş-fiyat backtest dökümü (genel + ticker bazında + özellik IC'leri)."""
    bt = _fc["backtest"] or {}
    cal = _fc["calibration"] or {}
    return {
        "horizonHours": HORIZON_BARS,
        "ready": _fc["model"] is not None,
        "overall": bt.get("overall"),
        "perTicker": bt.get("per_ticker"),
        "priceIC": cal.get("price_ic"),
        "n": cal.get("n"),
        "note": "Hit-rate 0.50 = yazi-tura. Gun ici yon tahmini teknikten zordur; "
                "asil deger duygu sinyalinin canli sicilinde gizli.",
    }


# ---------------- Kesitsel öngörü (ASIL sinyal) API ----------------
@app.get("/api/crosssection")
def crosssection():
    """ASIL ölçülen sinyal: günlük rejim-koşullu kesitsel momentum (market-nötr) +
    DÜRÜST backtest sicili. Hisseleri birbirine göre sıralar; tek-hisse yönü değil."""
    rec = _cs["record"] or {}
    dsr = rec.get("dsr7")
    p = rec.get("bootstrap_p")
    if not _cs["model"]:
        status_txt = "hazırlanıyor (günlük model eğitiliyor, ilk turda ~1-2 dk)"
    elif dsr is not None and dsr > 0.95 and p is not None and p < 0.05:
        status_txt = "ispatlandı (robust)"
    elif p is not None and p < 0.05:
        status_txt = "sınırda-anlamlı (kesin ispat değil)"
    else:
        status_txt = "zayıf / doğrulanamadı"
    return {
        "ready": _cs["model"] is not None,
        "asof": _cs["trained_at"],
        "horizonDays": rec.get("horizon_days", 5),
        "record": rec,
        "status": status_txt,
        "ranking": _cs["ranking"],
        "currency": "USD",
        "error": _cs["error"],
        "note": "PARA-NÖTR (BIST USD'ye çevrili): hisseleri birbirine göre sıralar — üstü göreli "
                "güçlü, altı zayıf. DÜRÜSTLÜK: TL-bazlı 'güçlü' sinyal büyük ölçüde kur "
                "artefaktıydı (Stage 6); para-nötr gerçek edge ZAYIF (16y Sharpe~0.45, son 5y ~0).",
        "disclaimer": "Yatırım tavsiyesi değildir; edge zayıf ve robust ispat eksiktir.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
