"""
finsent.portfolio — portföy/risk katmanı ("Tahmin Gücü Ölçer").

Modüller:
  weights      : kesitsel rank → dolar-nötr + ters-vol ağırlık; 1/N-rank benchmark.
  ls_backtest  : kesitsel walk-forward → market-nötr long-short getiri serisi.

İleride: covariance (Ledoit-Wolf/MP-denoise), risk (vol-hedef), blacklitterman (skill-gated).
Kullanım: ``from finsent.portfolio import weights, ls_backtest``
"""
