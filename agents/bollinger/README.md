# Bollinger Bands Agent

BB(20, 2) mean reversion signal based on %B (price location within band).

## Contract

```python
def analyze(symbol: str, df: pd.DataFrame) -> Signal
```

Agent name: `"bollinger"`. Metrics: `bb_lower`, `bb_middle`, `bb_upper`, `bb_percent_b`.

## When BB Works

- Range-bound markets — mean reversion is reliable
- Sudden spikes that quickly correct

## When BB Fails

- Strong trends — price hugs upper/lower band for days ("riding the band")
- Very high volatility regimes where 2σ thresholds widen too far
