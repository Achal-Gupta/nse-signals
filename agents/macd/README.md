# MACD Agent

MACD(12, 26, 9) crossover signal. Captures trend direction and momentum,
complementary to RSI's mean-reversion focus.

## Contract

```python
def analyze(symbol: str, df: pd.DataFrame) -> Signal
```

Agent name in output: `"macd"`. Metrics: `macd_line`, `macd_signal`, `macd_hist`.

## When MACD Works

- Strong trending markets (where RSI fails by staying overbought/oversold)
- Multi-week directional moves

## When MACD Fails

- Choppy / range-bound markets → whipsaw signals
- Mitigated by the aggregator combining MACD with mean-reversion (RSI, BB) and volume (VWAP)
