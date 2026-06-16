"""
finsent.evaluation — bilimsel değerlendirme katmanı.

Modüller (alt-modülleri AÇIKÇA import et; döngüsel importu önlemek için burada
eager re-export YOK):
  backtest    : in-sample kalibrasyon/ölçüm (hızlı sağlık göstergesi).
  validation  : purged + embargoed walk-forward CV (dürüst örnek-dışı).
  benchmarks  : null/temel çizgiler (buy&hold, random-sign, permütasyon).
  stats       : istatistiksel sertleştirme (Sharpe, PSR, Deflated Sharpe, bootstrap, FDR).

Kullanım: ``from finsent.evaluation import validation, benchmarks, stats``
"""
