# MACD Agent — Skill Definition

## Role

Moving Average Convergence Divergence — a trend-following momentum indicator.
Rule-based, no LLM call.

## Rules (v0.2.1)

Standard MACD(12, 26, 9):
- **MACD line** = EMA(12) - EMA(26) of Close
- **Signal line** = EMA(9) of MACD line
- **Histogram** = MACD - Signal

Signal logic (sign-based, not crossover):
- **BUY** when histogram > 0 AND MACD line > 0 (bullish positioning)
- **SELL** when histogram < 0 AND MACD line < 0 (bearish positioning)
- **HOLD** otherwise (mixed signs — momentum disagrees with trend)
- Confidence proportional to histogram magnitude, scaled by price

### Why Sign-Based, Not Crossover (v0.2.0 → v0.2.1)

The v0.2.0 implementation required a **strict crossover** — the histogram had
to transition from ≤ 0 in the previous sample to > 0 in the current sample.

In production this never fired (0/180 signals across 2 days). With 15-minute
sampling, the histogram often jumped fully across zero between samples. We'd
see +6.0 → -2.3 with no intermediate near-zero reading, missing the crossover
moment entirely.

The sign-based approach uses current state:
- *Is the histogram positive right now?* (momentum building bullish)
- *Is the MACD line positive right now?* (trend is up)
- *Do they agree?*

This produces more signals (current state is more frequent than transitions)
but is also closer to how traders typically read MACD anyway.

## Why MACD

- Captures trend direction and momentum — complementary to RSI's mean-reversion focus
- Works well in trending markets where RSI fails

## Limitations

- Lagging indicator — confirms moves rather than predicts them
- Will produce false signals in choppy markets
- The aggregator's weighted-score approach limits any single indicator's impact
