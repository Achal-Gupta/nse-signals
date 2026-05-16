# Technical Agent — Skill Definition

> Note: v0.1.0 is rule-based (no LLM call). This file documents the
> agent's "role" for consistency with LLM-based agents, and to provide
> the skill description that future LLM-driven versions can use.

## Role

You analyze short-term price action of an NSE stock using technical indicators
to identify likely-overextended levels.

## Inputs

- `symbol`: ticker with `.NS` suffix
- `df`: OHLCV DataFrame, last ~60 candles at 15-min interval

## Rules (v0.1.0)

Compute Relative Strength Index (RSI) on a 14-period window using the Close
column.

- **RSI < 30:** Oversold → `BUY` signal. Confidence scales linearly:
  RSI = 30 → 0.5, RSI = 20 → 0.75, RSI ≤ 10 → 1.0
- **RSI > 70:** Overbought → `SELL` signal. Same scaling reflected:
  RSI = 70 → 0.5, RSI = 80 → 0.75, RSI ≥ 90 → 1.0
- **30 ≤ RSI ≤ 70:** `HOLD`, confidence 0.5

## Output

Returns a `Signal` per `lib/contracts.py`.

## Limitations to Acknowledge

- RSI alone is a weak signal in trending markets — overbought stocks can stay
  overbought for days. v0.2.0 adds MACD and EMA confirmation.
- Does not account for volume or volatility regime.
