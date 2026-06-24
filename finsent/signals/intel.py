"""
Piyasa-zekası katmanı (Stage 23): ücretsiz, yasal, gün-trade'e uygun "smart money" + duygu sinyalleri.

NEDEN: Haber-odaklı trade'de fiyatın ÖTESİNDE sinyaller değerli; çoğu paralı, bunlar ÜCRETSİZ:
  - insider_form4(ticker): SEC EDGAR Form 4 — içeriden alım/satım (~2 İŞ GÜNÜ gecikme) = GERÇEK sinyal
  - crypto_fng() / stock_fng(): Korku&Açgözlülük endeksi (contrarian/sentiment zamanlaması)
  - vix(): piyasa korku göstergesi
  - earnings_date(ticker): sonraki bilanço (binary olay uyarısı)

NOT: Kongre/Capitol Trades = 45 GÜN gecikme → day-trade edge'i YOK; insider Form 4 çok daha hızlı,
bu yüzden onu bağladık. Hepsi keyless (SEC UA gerektirir).
"""
from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET

_UA = {"User-Agent": "finsent-research trader@finsent.local"}


def _get_json(url: str, headers: dict | None = None):
    req = urllib.request.Request(url, headers=headers or _UA)
    with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310
        return json.loads(r.read())


# ---------------------------------------------------------------------------
# Duygu / piyasa korkusu
# ---------------------------------------------------------------------------
def crypto_fng() -> dict:
    """Kripto Korku&Açgözlülük (alternative.me, keyless). 0-24 aşırı korku ... 75+ aşırı açgözlülük."""
    try:
        x = _get_json("https://api.alternative.me/fng/?limit=1")["data"][0]
        return {"value": int(x["value"]), "label": x["value_classification"]}
    except Exception as e:  # pragma: no cover
        return {"error": str(e)[:60]}


def stock_fng() -> dict:
    """CNN hisse Korku&Açgözlülük (keyless dataviz endpoint)."""
    try:
        d = _get_json("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                      headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
                               "Accept": "application/json",
                               "Referer": "https://www.cnn.com/markets/fear-and-greed"})
        fg = d["fear_and_greed"]
        return {"value": round(fg["score"]), "label": fg["rating"]}
    except Exception as e:
        return {"error": str(e)[:60]}


def vix() -> dict:
    """VIX (oynaklık/korku). <15 sakin · 15-20 normal · 20-28 tedirgin · 28-40 korku · 40+ panik."""
    try:
        import yfinance as yf
        c = [float(x) for x in yf.Ticker("^VIX").history(period="5d", interval="1d")["Close"].dropna()]
        v = c[-1]
        lbl = ("sakin" if v < 15 else "normal" if v < 20 else "tedirgin"
               if v < 28 else "korku" if v < 40 else "panik")
        return {"vix": round(v, 2), "label": lbl}
    except Exception as e:  # pragma: no cover
        return {"error": str(e)[:60]}


def earnings_date(ticker: str) -> dict:
    """Sonraki bilanço tarihi (yfinance calendar) — binary olay uyarısı."""
    try:
        import yfinance as yf
        cal = yf.Ticker(ticker).calendar
        ed = None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
        elif cal is not None and hasattr(cal, "loc"):
            try:
                ed = cal.loc["Earnings Date"].tolist()
            except Exception:
                ed = None
        if isinstance(ed, (list, tuple)) and ed:
            ed = ed[0]
        return {"ticker": ticker.upper(), "earnings": str(ed) if ed else "bilinmiyor"}
    except Exception as e:
        return {"ticker": ticker.upper(), "error": str(e)[:60]}


# ---------------------------------------------------------------------------
# Insider — SEC EDGAR Form 4 (içeriden alım/satım)
# ---------------------------------------------------------------------------
_CIK_CACHE: dict = {}


def _cik(ticker: str):
    if not _CIK_CACHE:
        d = _get_json("https://www.sec.gov/files/company_tickers.json")
        for v in d.values():
            _CIK_CACHE[v["ticker"].upper()] = str(v["cik_str"]).zfill(10)
    return _CIK_CACHE.get(ticker.upper())


def _parse_form4(url: str):
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=15).read()  # noqa: S310
    root = ET.fromstring(raw)
    owner = root.findtext(".//reportingOwner/reportingOwnerId/rptOwnerName") or "?"
    title = root.findtext(".//reportingOwner/reportingOwnerRelationship/officerTitle") or ""
    buys = sells = bsh = ssh = 0.0
    for tr in root.findall(".//nonDerivativeTransaction"):
        code = tr.findtext(".//transactionCoding/transactionCode") or ""
        sh = tr.findtext(".//transactionAmounts/transactionShares/value")
        pr = tr.findtext(".//transactionAmounts/transactionPricePerShare/value")
        ad = tr.findtext(".//transactionAmounts/transactionAcquiredDisposedCode/value") or ""
        if sh is None:
            continue
        sh = float(sh)
        pr = float(pr) if pr else 0.0
        if code == "P" or (code != "S" and ad == "A"):
            buys += sh * pr
            bsh += sh
        elif code == "S" or ad == "D":
            sells += sh * pr
            ssh += sh
    if bsh == 0 and ssh == 0:
        return None
    return {"owner": owner.strip(), "title": title.strip(),
            "buy_usd": round(buys), "sell_usd": round(sells),
            "net": "ALIM" if buys > sells else "SATIM",
            "open_market": "P" if buys > 0 else ("S" if sells > 0 else "")}


def insider_form4(ticker: str, limit: int = 6) -> dict:
    """Bir hissenin son içeriden işlemleri (SEC EDGAR Form 4). P=açık-piyasa alım (asıl sinyal)."""
    cik = _cik(ticker)
    if not cik:
        return {"ticker": ticker.upper(), "error": "CIK bulunamadı"}
    try:
        rec = _get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")["filings"]["recent"]
    except Exception as e:
        return {"ticker": ticker.upper(), "error": f"submissions: {str(e)[:50]}"}
    cikn = str(int(cik))
    trades, scanned = [], 0
    for form, date, acc, doc in zip(rec["form"], rec["filingDate"],
                                    rec["accessionNumber"], rec["primaryDocument"]):
        scanned += 1
        if scanned > 200:
            break
        docname = doc.split("/")[-1]  # 'xslF345X06/form4.xml' -> 'form4.xml' (HAM xml, XSLT-HTML değil)
        if form != "4" or not docname.endswith(".xml"):
            continue
        url = f"https://www.sec.gov/Archives/edgar/data/{cikn}/{acc.replace('-', '')}/{docname}"
        try:
            t = _parse_form4(url)
        except Exception:
            t = None
        if t:
            trades.append({"date": date, **t})
        if len(trades) >= limit:
            break
    # özet: son işlemlerde net alım mı satım mı (P=açık-piyasa alım asıl boğa sinyali)
    net_buy = sum(t["buy_usd"] for t in trades) - sum(t["sell_usd"] for t in trades)
    return {"ticker": ticker.upper(), "trades": trades,
            "net_signal": "ALIM" if net_buy > 0 else "SATIM" if net_buy < 0 else "nötr",
            "net_usd": round(net_buy)}


def summary(tickers) -> None:
    """Tek komutluk piyasa-zekası board'u: duygu + VIX + her hisse için insider + bilanço."""
    cg, sf, vx = crypto_fng(), stock_fng(), vix()
    print("=== PIYASA DUYGUSU ===")
    print("  Kripto F&G: %s (%s)  |  Hisse F&G: %s (%s)  |  VIX: %s (%s)"
          % (cg.get("value"), cg.get("label"), sf.get("value"), sf.get("label"),
             vx.get("vix"), vx.get("label")))
    print("=== INSIDER (SEC Form 4) + BILANCO ===")
    for tk in tickers:
        ins = insider_form4(tk, limit=4)
        ed = earnings_date(tk)
        flag = "🟢" if ins.get("net_signal") == "ALIM" else "🔴" if ins.get("net_signal") == "SATIM" else "⚪"
        print("  %-5s %s insider net %-5s $%-11s | bilanço: %s"
              % (tk, flag, ins.get("net_signal"), ins.get("net_usd"), ed.get("earnings")))


if __name__ == "__main__":
    import sys
    summary(sys.argv[1:] or ["MRVL", "INTC", "MU", "WDC", "FLEX"])
