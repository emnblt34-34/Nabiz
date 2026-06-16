"""
Dayanıklılık testleri — bir edge STABİL mi yoksa tek-dönem flukı / overfit mi?

DSR ve bootstrap-p tüm örnekte anlamlılığı ölçer ama edge'in birkaç şanslı döneme
yığılıp yığılmadığını söylemez. Bu modül:
  - subperiod_sharpe()    : getiri serisini ardışık dönemlere böler, her birinde Sharpe.
                            Çoğu dönemde pozitifse stabil; tek dönemdeyse kırılgan/overfit.
  - sharpe_bootstrap_ci() : block-bootstrap ile Sharpe güven aralığı (alt sınır >0 mu?).
"""
from __future__ import annotations

import math
import random
import statistics

from . import stats


def subperiod_sharpe(returns: list[float], dates: list[str], n_blocks: int = 4,
                     ppy: float = 50.4) -> dict:
    """Getiri serisini n ardışık döneme böl; her dönemde Sharpe + ortalama getiri."""
    paired = sorted(zip(dates, returns), key=lambda x: x[0])
    rets = [r for _, r in paired]
    ds = [d for d, _ in paired]
    L = len(rets)
    if L < n_blocks * 5:
        return {"blocks": [], "n_positive": 0, "n_blocks": n_blocks}
    size = L // n_blocks
    blocks = []
    for b in range(n_blocks):
        lo = b * size
        hi = (b + 1) * size if b < n_blocks - 1 else L
        seg = rets[lo:hi]
        sr = stats.sharpe(seg, ppy)
        blocks.append({
            "period": f"{ds[lo][:7]}..{ds[hi-1][:7]}",
            "n": len(seg),
            "sharpe": round(sr, 2) if sr is not None else None,
            "mean_ret_pct": round(statistics.fmean(seg) * 100, 3),
        })
    n_pos = sum(1 for bl in blocks if bl["sharpe"] is not None and bl["sharpe"] > 0)
    return {"blocks": blocks, "n_positive": n_pos, "n_blocks": n_blocks}


def sharpe_bootstrap_ci(returns: list[float], ppy: float = 50.4, block: int = 5,
                        n_boot: int = 2000, seed: int = 19) -> dict | None:
    """Block-bootstrap ile yıllık Sharpe güven aralığı (p05/p50/p95) + pozitif oranı.
    Otokorelasyonu korur. Alt sınır (p05) > 0 ise edge gerçekten sağlam sinyali."""
    n = len(returns)
    if n < 20:
        return None
    rng = random.Random(seed)
    nb = math.ceil(n / block)
    srs = []
    for _ in range(n_boot):
        sample: list[float] = []
        for _ in range(nb):
            s = rng.randrange(n)
            for k in range(block):
                sample.append(returns[(s + k) % n])
        sr = stats.sharpe(sample[:n], ppy)
        if sr is not None:
            srs.append(sr)
    if not srs:
        return None
    srs.sort()
    m = len(srs)
    return {
        "sharpe_p05": round(srs[int(0.05 * m)], 2),
        "sharpe_p50": round(srs[int(0.50 * m)], 2),
        "sharpe_p95": round(srs[int(0.95 * m)], 2),
        "frac_positive": round(sum(1 for s in srs if s > 0) / m, 3),
    }
