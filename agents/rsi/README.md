# RSI Agent

Wilder's Relative Strength Index — one of four technical agents in v0.2.0.
Rule-based, no LLM call.

## Contract

```python
def analyze(symbol: str, df: pd.DataFrame) -> Signal
```

Agent name in output: `"rsi"`.

## Logic

- RSI < 30 → BUY (confidence scales: 30→0.5, 10→1.0)
- RSI > 70 → SELL (confidence scales: 70→0.5, 90→1.0)
- else → HOLD, confidence 0.5

## Limitations

- Range-bound regime indicator; weak in strong trends
- Can stay overbought/oversold for extended periods
- v0.2.0 mitigation: aggregator combines RSI with MACD/EMA-style trend signal (MACD), volatility (BB), and volume (VWAP) so RSI alone doesn't dominate
