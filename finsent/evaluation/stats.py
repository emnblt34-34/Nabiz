"""
İstatistiksel sertleştirme (Stage 1) — "edge gerçek mi?" kararının matematiği.

Bir strateji getiri serisinin ham Sharpe'ı yanıltıcıdır: (1) otokorelasyon naif p'yi
şişirir, (2) çok sayıda deneme yapıldıysa "en iyi" şans eseri yüksek çıkar. Bu modül:
  - sharpe()                : yıllıklandırılmış Sharpe.
  - psr()                   : Probabilistic Sharpe Ratio (çarpıklık/basıklık düzeltmeli).
  - deflated_sharpe()       : DSR — denenen deneme sayısına göre SR* eşiğiyle deflasyon
                              (Bailey & López de Prado). Çoklu-test cevabı.
  - block_bootstrap_pvalue(): otokorelasyon-dayanıklı, ortalama-getiri>0 testi.
  - benjamini_hochberg()    : çok-hipotez için FDR düzeltmesi.

NOT: L/S getiri serisi (rebalans başına 1 gözlem, örtüşmesiz) üzerinde çalışmak, pooled
(ticker×bar) IC'deki bağımsızlık-şişmesini doğal olarak büyük ölçüde çözer.
"""
from __future__ import annotations

import math
import random
import statistics

_N = statistics.NormalDist()
_GAMMA = 0.5772156649015329  # Euler-Mascheroni


def sharpe(returns: list[float], periods_per_year: float) -> float | None:
    """Yıllıklandırılmış Sharpe (rf=0). Az gözlemde None."""
    if len(returns) < 3:
        return None
    mu = statistics.fmean(returns)
    sd = statistics.pstdev(returns)
    return (mu / sd) * math.sqrt(periods_per_year) if sd else None


def _moments(returns: list[float]):
    n = len(returns)
    mu = statistics.fmean(returns)
    sd = statistics.pstdev(returns)
    if sd == 0:
        return mu, sd, 0.0, 3.0
    skew = sum(((r - mu) / sd) ** 3 for r in returns) / n
    kurt = sum(((r - mu) / sd) ** 4 for r in returns) / n
    return mu, sd, skew, kurt


def psr(returns: list[float], sr_benchmark: float = 0.0) -> float | None:
    """
    Probabilistic Sharpe Ratio: gözlemlenen (per-period) SR'ın benchmark SR*'ı
    aşma olasılığı, çarpıklık/basıklık düzeltmeli. 0..1; >0.95 ≈ anlamlı.
    """
    n = len(returns)
    if n < 3:
        return None
    mu, sd, skew, kurt = _moments(returns)
    if sd == 0:
        return None
    sr = mu / sd  # per-period
    denom = math.sqrt(max(1 - skew * sr + (kurt - 1) / 4.0 * sr * sr, 1e-9))
    z = (sr - sr_benchmark) * math.sqrt(n - 1) / denom
    return _N.cdf(z)


def deflated_sharpe(returns: list[float], n_trials: int) -> dict:
    """
    Deflated Sharpe Ratio: n_trials deneme yapıldıysa, şans eseri beklenen MAKSİMUM
    null Sharpe (SR*) eşiğine karşı PSR. Null SR varyansı ~ 1/(n-1) yaklaşımı.
    Dönüş: {dsr, sr_star_per_period, n_trials}. dsr>0.95 ≈ çoklu-test sonrası anlamlı.
    """
    n = len(returns)
    if n < 3 or n_trials < 1:
        return {"dsr": None, "sr_star_per_period": None, "n_trials": n_trials}
    var_sr = 1.0 / (n - 1)  # null per-period SR tahmin varyansı yaklaşımı
    N = max(n_trials, 2)
    z1 = _N.inv_cdf(1 - 1.0 / N)
    z2 = _N.inv_cdf(1 - 1.0 / (N * math.e))
    sr_star = math.sqrt(var_sr) * ((1 - _GAMMA) * z1 + _GAMMA * z2)
    return {"dsr": psr(returns, sr_benchmark=sr_star),
            "sr_star_per_period": round(sr_star, 4), "n_trials": n_trials}


def block_bootstrap_pvalue(returns: list[float], block: int = 5,
                           n_boot: int = 2000, seed: int = 17) -> float | None:
    """
    H0: ortalama getiri = 0. Dairesel blok-bootstrap (otokorelasyonu korur).
    Tek-yönlü p = P(bootstrap_mean >= gözlenen_mean | null). Naif iid p'den daha
    dürüst (büyük), çünkü ardışık getiri bağımlılığını hesaba katar.
    """
    n = len(returns)
    if n < 10:
        return None
    obs = statistics.fmean(returns)
    centered = [r - obs for r in returns]  # null altında merkeze al
    rng = random.Random(seed)
    nb = math.ceil(n / block)
    ge = 0
    for _ in range(n_boot):
        sample: list[float] = []
        for _ in range(nb):
            s = rng.randrange(n)
            for k in range(block):
                sample.append(centered[(s + k) % n])
        if statistics.fmean(sample[:n]) >= obs:
            ge += 1
    return (ge + 1) / (n_boot + 1)


def benjamini_hochberg(pvals: list[float], alpha: float = 0.05) -> list[bool]:
    """FDR (Benjamini-Hochberg): çok-hipotez listesinde hangileri alpha-FDR'de geçer."""
    m = len(pvals)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvals[i])
    thr_rank = 0
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= rank / m * alpha:
            thr_rank = rank
    passed = [False] * m
    for rank, i in enumerate(order, start=1):
        passed[i] = rank <= thr_rank
    return passed
