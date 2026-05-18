# VWAP Agent — Skill Definition

## Role

Volume-Weighted Average Price. The only indicator in v0.2.0 that incorporates
**volume**, giving the system a different lens than the pure price-action indicators.

Heavily used by institutional traders as a benchmark for execution quality.

## Rules

**Session VWAP**: cumulative (price × volume) / cumulative volume, reset at session open.

For v0.2.0 we use a rolling VWAP over the most recent N candles since session-anchored
VWAP requires precise market-open detection.

- **Rolling VWAP** = Σ(typical_price × volume) / Σ(volume), over last 20 candles
- `typical_price` = (High + Low + Close) / 3
- `distance_pct` = (Close - VWAP) / VWAP × 100

Signal logic:
- **BUY** when price is significantly below VWAP (distance < -0.5%) — institutions often buy here
- **SELL** when price is significantly above VWAP (distance > +0.5%) — institutions often take profit
- Confidence scales with distance magnitude (capped)
- Otherwise **HOLD** with confidence 0.5

## Why VWAP

- **Volume confirmation**: price alone can be misleading; VWAP incorporates how much was traded at each price
- **Institutional benchmark**: large players try to fill at or better than VWAP — this creates real support/resistance
- **Complementary**: differs in *kind* from RSI/MACD/BB which all use only OHLC data

## Limitations

- Less meaningful on illiquid stocks (volume is unreliable)
- Rolling VWAP is a proxy; intraday session VWAP would be more precise (v0.3.0 improvement)
- Distance thresholds are heuristic — Reviewer Agent (v0.5.0) will tune these
