# RSI Agent — Skill Definition

## Role

Wilder's Relative Strength Index — captures momentum and mean reversion at
extremes. One of four technical agents in v0.2.0. Rule-based, no LLM call.

## Rules (v0.2.0, unchanged from v0.1.0)

Compute RSI on a 14-period window using the Close column with Wilder's EMA
smoothing (alpha = 1/period).

- **RSI < 30:** Oversold → `BUY` signal. Confidence scales linearly:
  RSI = 30 → 0.5, RSI = 20 → 0.75, RSI ≤ 10 → 1.0
- **RSI > 70:** Overbought → `SELL`. Same scaling reflected.
- **30 ≤ RSI ≤ 70:** `HOLD`, confidence 0.5

## Output

Returns a `Signal` with `agent="rsi"` and `metrics={"rsi": float}`.

## Limitations Acknowledged

- RSI is a mean-reversion indicator; weak in strong trends (overbought stocks
  can stay overbought for days). MACD agent compensates with trend signal.
- RSI's 30/70 thresholds are convention, not gospel; v0.5.0's Reviewer Agent
  may tune them per-stock based on actual outcomes.
