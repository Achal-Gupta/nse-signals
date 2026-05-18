# MACD Agent — Skill Definition

## Role

Moving Average Convergence Divergence — a trend-following momentum indicator.
Rule-based, no LLM call.

## Rules

Standard MACD(12, 26, 9):
- **MACD line** = EMA(12) - EMA(26) of Close
- **Signal line** = EMA(9) of MACD line
- **Histogram** = MACD - Signal

Signal logic (v0.2.0):
- **BUY** when histogram crosses above zero (bullish crossover) AND MACD > 0
- **SELL** when histogram crosses below zero (bearish crossover) AND MACD < 0
- Confidence proportional to histogram magnitude (capped at 1.0)
- Otherwise **HOLD** with confidence 0.5

## Why MACD

- Captures **trend direction and momentum** — complementary to RSI's mean-reversion focus
- Works well when there's a real trend (where RSI fails)
- Weak in choppy / range-bound markets — which is where RSI takes over

## Limitations

- Lagging indicator — confirms moves rather than predicts them
- False signals in choppy markets (whipsaws)
- The aggregator's weighted-score approach reduces reliance on any single indicator
