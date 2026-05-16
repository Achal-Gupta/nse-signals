# Sentiment Fusion

Rule-based combiner — no LLM call. Takes the market-wide and stock-specific
sentiment Signals and produces a single fused Signal.

## Contract

```python
def fuse(market_signal: Signal, stock_signal: Signal) -> Signal
```

## Why Rule-Based

The combination logic is mechanical (weighted sum + override). Adding an
LLM call here would burn budget without adding value. In v0.5.0 the
Reviewer Agent will tune these weights based on track record.

## Tunable Constants

In `agent.py`:
- `MARKET_WEIGHT = 0.4`
- `STOCK_WEIGHT = 0.6`
- `ACTION_THRESHOLD = 0.25`
- `STRONG_MARKET_THRESHOLD = 0.7`
