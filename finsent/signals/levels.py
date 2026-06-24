"""
Doğrulanmış Teknik Seviye Motoru (Stage 21).

NEDEN (kritik kullanıcı talebi — trade'de tolerans YOK): Seviye "göz kararı" olamaz.
MRVL'de "$321 ATH" dedim; GERÇEK ATH $326.21'di (kullanıcı yakaladı, ben yanıldım).
Bir daha olmamalı → her varlık için, GERÇEK fiyat verisinden DETERMİNİSTİK seviye haritası.

ÜRETİLEN (hepsi ÖLÇÜLÜR, uydurma yok):
  - ATH / ATL (TÜM geçmiş, period=max) + tarih + uzaklık
  - 52-hafta yüksek / düşük
  - Swing destek/direnç: pivot tespiti (yerel ekstrem) + kümeleme; dokunuş sayısı = güç
  - SMA 20 / 50 / 200 (dinamik destek/direnç)
  - ATR(14) + ATR% (stop/oynaklık ölçeği)
  - Önceki gün H/L/C, bugün O/H/L, gün-içi ext (pre/post) H/L, VWAP
  - Fiyata EN YAKIN direnç (üstte) + EN YAKIN destek (altta) — tüm kaynaklar birleşik
  - Konum sınıfı: ZİRVE/blue-sky · ortalamaların üstünde/altında · arası

Fiyatlar auto_adjust=False (bölünme-ayarlı, temettü-ayarsız = trader'ın grafikte gördüğü
nominal seviye). ATH için derin geçmiş şart → bağımsız, yfinance'ten taze çeken canlı araç.

Canlı çağrı:  python -m finsent.signals.levels MRVL INTC MU AVAX-USD BTC-USD
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from ..config import TICKER_MARKET, yf_symbol


def _yf():
    try:
        import yfinance as yf  # noqa: WPS433
        return yf
    except Exception as e:  # pragma: no cover
        print(f"[levels] yfinance yok: {e}")
        return None


def _sym(t: str) -> str:
    """Kanonik sembol ('MRVL','AVAX') ya da ham yf sembolü ('AVAX-USD','THYAO.IS') kabul."""
    u = t.upper()
    if u in TICKER_MARKET:
        return yf_symbol(u)
    return t


def _r(x):
    if x is None:
        return None
    ax = abs(x)
    if ax >= 100:
        return round(x, 2)
    if ax >= 1:
        return round(x, 3)
    return round(x, 5)


def _atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    return sum(trs[-period:]) / period if len(trs) >= period else None


def _pivots(highs, lows, k=4):
    """Yerel ekstrem (k bar her iki yanda) = swing tepe/dip. Teknik direnç/destek çekirdeği."""
    ph, pl = [], []
    n = len(highs)
    for i in range(k, n - k):
        if highs[i] >= max(highs[i - k:i + k + 1]):
            ph.append(highs[i])
        if lows[i] <= min(lows[i - k:i + k + 1]):
            pl.append(lows[i])
    return ph, pl


def _cluster(vals, tol):
    """Yakın seviyeleri (tol = oransal mesafe) tek bölgede topla; dokunuş = güç."""
    out: list[dict] = []
    for v in sorted(vals):
        if out and abs(v - out[-1]["mean"]) / out[-1]["mean"] <= tol:
            c = out[-1]
            c["vals"].append(v)
            c["touches"] += 1
            c["mean"] = sum(c["vals"]) / len(c["vals"])
        else:
            out.append({"mean": v, "vals": [v], "touches": 1})
    return out


def _round_levels(price):
    """Psikolojik yuvarlak seviyeler (fiyat büyüklüğüne göre adım)."""
    if price >= 1000:
        step = 50.0
    elif price >= 100:
        step = 10.0
    elif price >= 10:
        step = 1.0
    elif price >= 1:
        step = 0.5
    else:
        step = 0.1
    base = round(price / step) * step
    return [base + step * i for i in (-2, -1, 0, 1, 2) if base + step * i > 0]


def _extended_high(yf, sym, reg_by_date):
    """Pre/post (uzatılmış seans) en yüksek GERÇEK tik — TradingView'in intraday/4s grafikleri
    bunları gösterir; düzenli-seans günlük bar göstermez. TİK-GÜRÜLTÜ FİLTRESİ: bir uzatılmış
    yüksek ancak AYNI GÜNÜN düzenli-seans yükseği onun %96'sından büyükse geçerli (yoksa anlık
    bozuk tik → ele; örn. MRVL 3 Haz $339.72 pre-market, o gün düzenli ~$290 → gürültü).
    yfinance 60dk prepost ~730g pencere (tüm-geçmiş yok ama güncel ATH'lar bu pencerede)."""
    try:
        h = yf.Ticker(sym).history(period="730d", interval="60m", prepost=True, auto_adjust=False)
    except Exception:
        return None
    if h is None or h.empty:
        return None
    best = None
    for ts, row in h.iterrows():
        hi = float(row["High"])
        if hi != hi:  # NaN
            continue
        rh = reg_by_date.get(ts.strftime("%Y-%m-%d"))
        if rh and rh >= hi * 0.96 and (best is None or hi > best[0]):
            best = (hi, ts.strftime("%Y-%m-%d"))
    return best


def compute_levels(ticker: str, yf=None) -> dict:
    """Bir varlık için TAM, ölçülmüş seviye haritası döner (uydurma yok)."""
    yf = yf or _yf()
    if yf is None:
        return {"ticker": ticker.upper(), "error": "yfinance yok"}
    sym = _sym(ticker)
    tk = yf.Ticker(sym)
    try:
        d = tk.history(period="max", interval="1d", auto_adjust=False)
    except Exception as e:  # pragma: no cover
        return {"ticker": ticker.upper(), "sym": sym, "error": f"günlük veri: {e}"}
    if d is None or d.empty or len(d) < 30:
        return {"ticker": ticker.upper(), "sym": sym, "error": "yetersiz günlük veri"}
    try:
        it = tk.history(period="1d", interval="1m", auto_adjust=False, prepost=True)
    except Exception:
        it = None

    dh = [float(x) for x in d["High"].tolist()]
    dl = [float(x) for x in d["Low"].tolist()]
    dc = [float(x) for x in d["Close"].tolist()]
    do = [float(x) for x in d["Open"].tolist()]
    dts = [ts.strftime("%Y-%m-%d") for ts in d.index]

    now = datetime.now(timezone.utc)
    delay = ext_hi = ext_lo = vwap = None
    if it is not None and not it.empty:
        ic = [float(x) for x in it["Close"].dropna().tolist()]
        price = ic[-1] if ic else dc[-1]
        try:
            delay = (now - it.index[-1].to_pydatetime().astimezone(timezone.utc)).total_seconds() / 60
        except Exception:
            delay = None
        ext_hi, ext_lo = float(it["High"].max()), float(it["Low"].min())
        tp = [(float(h) + float(l) + float(c)) / 3
              for h, l, c in zip(it["High"], it["Low"], it["Close"])]
        vol = [float(v) for v in it["Volume"]]
        sv = sum(vol)
        vwap = sum(t * v for t, v in zip(tp, vol)) / sv if sv > 0 else None
    else:
        price = dc[-1]

    res = _levels_core(ticker.upper(), sym, TICKER_MARKET.get(ticker.upper(), "US"),
                       price, dh, dl, dc, do, dts, now, delay, ext_hi, ext_lo, vwap)
    eh = _extended_high(yf, sym, dict(zip(dts, dh)))   # TV-uyumu: pre/post yüksek (gürültü-filtreli)
    if eh and eh[0] > max(dh) * 1.0008:
        res["ext_high"] = {"price": _r(eh[0]), "date": eh[1]}
    return res


def _levels_core(ticker, sym, market, price, dh, dl, dc, do, dts, now,
                 delay=None, ext_hi=None, ext_lo=None, vwap=None) -> dict:
    """Saf seviye çekirdeği (ağ YOK) — compute_levels veriyi çeker, burayı çağırır.
    Offline/sentetik test edilebilir → değişmezler garanti (ATH==max(high), direnç üstte/destek altta)."""
    # ATH / ATL (TÜM geçmiş) — burası asıl güvence
    iath = max(range(len(dh)), key=lambda i: dh[i])
    iatl = min(range(len(dl)), key=lambda i: dl[i])
    ath, ath_d = dh[iath], dts[iath]
    atl, atl_d = dl[iatl], dts[iatl]
    h52, l52 = max(dh[-252:]), min(dl[-252:])

    # önceki gün / bugün (son bar bugünse ayrıştır)
    nd = now.strftime("%Y-%m-%d")
    if dts[-1] == nd and len(dc) >= 2:
        today_bar = {"open": do[-1], "high": dh[-1], "low": dl[-1]}
        prior = {"high": dh[-2], "low": dl[-2], "close": dc[-2]}
    else:
        today_bar = None
        prior = {"high": dh[-1], "low": dl[-1], "close": dc[-1]}

    def sma(n):
        return sum(dc[-n:]) / n if len(dc) >= n else None
    s20, s50, s200 = sma(20), sma(50), sma(200)
    atr = _atr(dh, dl, dc, 14)
    atr_pct = (atr / price * 100) if atr else None

    # swing pivotlar (son ~180 gün) + kümeleme
    win = min(len(dh), 180)
    ph, pl = _pivots(dh[-win:], dl[-win:], k=4)
    # Kümeleme bandı DAR olmalı (yoksa ATH gibi kritik seviye komşu swing'e karışır).
    # ATR'den hafif etkilenir ama %0.6'da sabitlenir → ayrı seviyeler ayrı kalır.
    tol = min(0.006, max(0.004, (atr / price * 0.08) if atr else 0.005))

    levels: list[dict] = []

    def add(p, typ, strength=1):
        if p and p > 0:
            levels.append({"price": p, "type": typ, "strength": strength})

    add(ath, "ATH")
    add(atl, "ATL")
    add(h52, "52h-T")
    add(l52, "52h-D")
    add(s20, "SMA20")
    add(s50, "SMA50")
    add(s200, "SMA200")
    add(prior["high"], "dün-T")
    add(prior["low"], "dün-D")
    if today_bar:
        add(today_bar["high"], "bugün-T")
        add(today_bar["low"], "bugün-D")
    for c in _cluster(ph, tol):
        add(c["mean"], "ö.tepe", c["touches"])
    for c in _cluster(pl, tol):
        add(c["mean"], "ö.dip", c["touches"])
    for rl in _round_levels(price):
        add(rl, "yuvarlak")

    def near(side):
        if side == "res":
            cand = sorted((l for l in levels if l["price"] > price * 1.0008),
                          key=lambda l: l["price"])
        else:
            cand = sorted((l for l in levels if l["price"] < price * 0.9992),
                          key=lambda l: -l["price"])
        merged: list[dict] = []
        for l in cand:
            if merged and abs(l["price"] - merged[-1]["price"]) / merged[-1]["price"] <= tol:
                merged[-1]["types"].append(l["type"])
                merged[-1]["strength"] += l["strength"]
            else:
                merged.append({"price": l["price"], "types": [l["type"]],
                               "strength": l["strength"]})
        res = []
        for m in merged:
            dp = round((m["price"] - price) / price * 100, 2)
            if abs(dp) > 25:          # 25%+ uzak = gün-içi/swing için gürültü (ATH/52h zaten başlıkta)
                continue
            res.append({"price": _r(m["price"]), "dist_pct": dp,
                        "types": m["types"], "strength": m["strength"]})
            if len(res) >= 4:
                break
        if not res and merged:        # hiç yoksa en yakını yine de göster
            m = merged[0]
            res.append({"price": _r(m["price"]),
                        "dist_pct": round((m["price"] - price) / price * 100, 2),
                        "types": m["types"], "strength": m["strength"]})
        return res

    resistances, supports = near("res"), near("sup")

    if price >= ath * 0.999:
        pos = "ZİRVE/BLUE-SKY (ATH'da/üstünde — üstte yatay direnç YOK)"
    elif price >= ath * 0.98:
        pos = (f"ATH'a ÇOK YAKIN ({(price - ath) / ath * 100:+.1f}%) — "
               "kırarsa blue-sky, reddederse geri çekilme")
    elif all(x and price > x for x in (s20, s50, s200)):
        pos = "tüm ortalamaların ÜSTÜNDE (güçlü uptrend)"
    elif all(x and price < x for x in (s20, s50, s200)):
        pos = "tüm ortalamaların ALTINDA (downtrend)"
    else:
        pos = "ortalamalar/seviyeler arası (kararsız bölge)"

    return {
        "ticker": ticker, "sym": sym,
        "market": market,
        "price": _r(price), "delay_min": round(delay, 1) if delay is not None else None,
        "asof": now.isoformat(),
        "ath": {"price": _r(ath), "date": ath_d,
                "below_pct": round((price - ath) / ath * 100, 2)},
        "atl": {"price": _r(atl), "date": atl_d},
        "high_52w": _r(h52), "low_52w": _r(l52),
        "sma": {"20": _r(s20), "50": _r(s50), "200": _r(s200)},
        "atr14": _r(atr), "atr_pct": round(atr_pct, 2) if atr_pct else None,
        "prior_day": {k: _r(v) for k, v in prior.items()},
        "today": {k: _r(v) for k, v in today_bar.items()} if today_bar else None,
        "ext_today": {"high": _r(ext_hi), "low": _r(ext_lo)} if ext_hi else None,
        "vwap": _r(vwap),
        "resistances": resistances, "supports": supports,
        "position": pos,
    }


def format_levels(d: dict) -> str:
    if "error" in d:
        return f"━━ {d.get('ticker')} ━━ HATA: {d['error']}"
    out = []
    delay = f" (gecikme {d['delay_min']}dk)" if d.get("delay_min") is not None else ""
    out.append(f"━━ {d['ticker']} ({d['sym']})  ${d['price']}{delay} ━━")
    out.append(f"  Konum: {d['position']}")
    a = d["ath"]
    out.append(f"  ATH ${a['price']} ({a['date']})  fiyat ATH'a göre {a['below_pct']:+.2f}%"
               f"  |  52h ${d['high_52w']} – ${d['low_52w']}")
    if d.get("ext_high"):
        e = d["ext_high"]
        out.append(f"  ⚠ uzatılmış-seans yüksek (pre/post; TV intraday'de görünür): "
                   f"${e['price']} ({e['date']}) — düzenli ATH üstünde, tik-gürültü filtreli")
    s = d["sma"]
    out.append(f"  SMA20 ${s['20']} · SMA50 ${s['50']} · SMA200 ${s['200']}"
               f"  |  ATR ${d['atr14']} ({d['atr_pct']}%)")
    pr = d["prior_day"]
    line = f"  dün H${pr['high']} L${pr['low']} C${pr['close']}"
    if d.get("today"):
        t = d["today"]
        line += f"  |  bugün O${t['open']} H${t['high']} L${t['low']}"
    if d.get("vwap"):
        line += f"  |  VWAP ${d['vwap']}"
    out.append(line)
    out.append("  ▲ DİRENÇLER (üstte, yakından uzağa):")
    for r in d["resistances"]:
        out.append(f"      ${r['price']}  ({r['dist_pct']:+.2f}%)  "
                   f"[{', '.join(r['types'])}]  {'★' * min(r['strength'], 5)}")
    out.append("  ▼ DESTEKLER (altta, yakından uzağa):")
    for sp in d["supports"]:
        out.append(f"      ${sp['price']}  ({sp['dist_pct']:+.2f}%)  "
                   f"[{', '.join(sp['types'])}]  {'★' * min(sp['strength'], 5)}")
    return "\n".join(out)


def main(argv):
    yf = _yf()
    if yf is None:
        return
    for t in argv:
        print(format_levels(compute_levels(t, yf)))
        print()


if __name__ == "__main__":
    main(sys.argv[1:] or ["MRVL"])
