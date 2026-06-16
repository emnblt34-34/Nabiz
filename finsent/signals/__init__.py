"""
finsent.signals — sinyal/rejim yardımcı katmanı (tahmin katmanını besler).

Modüller:
  regime : rejim göstergeleri (Hurst, Efficiency-Ratio, trend-score) — SİNYAL DEĞİL
           KOŞULLAMA. Momentum yalnız trendli rejimde "açılır"; choppy rejimde reversal.

İleride: labeling (triple-barrier), mid-price/microstructure.
Bağımlılık: yalnız stdlib (çekirdeğe bile bağlı değil) → features.py güvenle import eder
(döngü yok).
"""
