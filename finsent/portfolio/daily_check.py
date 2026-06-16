"""
Günlük yön anlık-kaydı (Stage 17) — "yarın tutarlılığı inceleme"nin DÜRÜST altyapısı.

Her gün bir kez, her hisse için O ANKİ yön öngörüsü (kesitsel side) + güven + USD fiyat loglanır.
Ufuk (varsayılan 1 işlem günü) dolunca gerçekleşen USD getiriyle eşlenir, yön tutmuş mu (correct)
işaretlenir. Böylece:
  - günlük yön çağrılarının CANLI isabeti zamanla birikir (geçmişe uydurma yok),
  - Stage 14 güven-kalibrasyonu SAHADA doğrulanır: yüksek güven gerçekten daha mı isabetli?

resolve() ufku dolanı çözer; stats() güven katmanına göre isabet döner.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from .. import db, fx

INTERVAL = "1d"


def _dir_from_side(side: str) -> str:
    return "up" if side == "long" else "down" if side == "short" else "neutral"


def log_snapshot(conn, ranking: list[dict], horizon_days: int = 1) -> int:
    """Bugün için her hisseye: yön + güven + USD fiyat logla (1/gün; idempotent)."""
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    if conn.execute("SELECT 1 FROM daily_check WHERE made_at LIKE ? LIMIT 1",
                    (today + "%",)).fetchone():
        return 0  # bugün zaten loglandı
    made = now.isoformat()
    target = (now + timedelta(days=horizon_days)).isoformat()
    n = 0
    for it in ranking:
        t = it["ticker"]
        closes, _ = fx.usd_series(conn, t, INTERVAL)
        if not closes:
            continue
        conn.execute(
            """INSERT OR IGNORE INTO daily_check
               (id, made_at, target_ts, ticker, market, price_at, direction,
                signal, confidence, conf_label, horizon_days)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (f"{today}|{t}", made, target, t, it.get("market"), closes[-1],
             _dir_from_side(it.get("side", "neutral")), it.get("signal"),
             it.get("confidence"), it.get("conf_label"), horizon_days))
        n += 1
    conn.commit()
    return n


def resolve(conn) -> int:
    """Ufku dolan kayıtları USD gerçek getiriyle eşle; yön tuttu mu işaretle."""
    now_iso = datetime.now(timezone.utc).isoformat()
    resolved = 0
    for r in conn.execute("SELECT * FROM daily_check WHERE realized_return IS NULL").fetchall():
        if r["target_ts"] > now_iso:
            continue
        closes, dates = fx.usd_series(conn, r["ticker"], INTERVAL)
        tgt = r["target_ts"][:10]
        close_at = next((c for d, c in zip(dates, closes) if d >= tgt), None)
        if close_at is None or not r["price_at"]:
            continue
        ret = (close_at - r["price_at"]) / r["price_at"]
        rdir = "up" if ret > 0 else "down" if ret < 0 else "neutral"
        correct = None
        if r["direction"] in ("up", "down"):
            correct = 1 if rdir == r["direction"] else 0
        conn.execute(
            "UPDATE daily_check SET realized_return=?, realized_dir=?, correct=?, resolved_at=? WHERE id=?",
            (round(ret, 5), rdir, correct, now_iso, r["id"]))
        resolved += 1
    conn.commit()
    return resolved


def stats(conn) -> dict:
    """Çözülen yön çağrılarının canlı isabeti — genel + güven katmanına göre (Stage 14 canlı testi)."""
    rows = conn.execute(
        "SELECT direction, conf_label, correct, realized_return FROM daily_check "
        "WHERE correct IS NOT NULL").fetchall()
    open_n = conn.execute(
        "SELECT COUNT(*) c FROM daily_check WHERE realized_return IS NULL").fetchone()["c"]
    n = len(rows)
    out: dict = {"resolved": n, "open": open_n}
    if n == 0:
        out["note"] = ("henüz çözülen yok — bugün loglandıysa yarın (ufuk dolunca) birikmeye başlar. "
                       "Geçmişe uydurulmaz; sahada ölçülür.")
        return out
    hits = sum(r["correct"] for r in rows)
    out["hit_rate"] = round(hits / n, 4)
    out["avg_signed_return"] = round(
        sum((r["realized_return"] or 0) * (1 if r["direction"] == "up" else -1) for r in rows) / n, 5)
    # güven katmanına göre (kalibrasyon canlı test): yüksek > orta > düşük olmalı
    by: dict = {}
    for lbl in ("yüksek", "orta", "düşük"):
        sub = [r for r in rows if r["conf_label"] == lbl]
        if sub:
            by[lbl] = {"n": len(sub), "hit_rate": round(sum(s["correct"] for s in sub) / len(sub), 4)}
    out["by_confidence"] = by
    out["note"] = "yüksek güven isabeti düşükten belirgin yüksekse → Stage 14 kalibrasyonu SAHADA doğrulandı."
    return out
