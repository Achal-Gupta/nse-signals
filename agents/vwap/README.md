# VWAP Agent

Volume-Weighted Average Price — the only v0.2.0 indicator that uses volume.

## Contract

```python
def analyze(symbol: str, df: pd.DataFrame) -> Signal
```

Agent name: `"vwap"`. Metrics: `vwap`, `price`, `vwap_distance_pct`.

## Why VWAP Matters

Volume-aware signals are categorically different from price-only indicators
(RSI, MACD, BB). VWAP is what institutions use as an execution benchmark, so
distance from VWAP often acts as real support/resistance.

## Limitations

- Rolling 20-candle VWAP, not session-anchored — v0.3.0 improvement
- Less meaningful on illiquid stocks
- Threshold of ±0.5% is heuristic; Reviewer Agent will tune
