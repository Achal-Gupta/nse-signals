# Bollinger Bands Agent — Skill Definition

## Role

Volatility-aware mean-reversion indicator. Tells us when price is statistically
extended from its recent average.

## Rules

Standard BB(20, 2):
- **Middle band** = SMA(20) of Close
- **Upper band** = SMA(20) + 2 × StdDev(20)
- **Lower band** = SMA(20) - 2 × StdDev(20)
- **%B** = (price - lower) / (upper - lower), where 0 = lower band, 1 = upper band

Signal logic:
- **BUY** when %B < 0.05 (price at or below lower band) → mean reversion expected
- **SELL** when %B > 0.95 (price at or above upper band)
- Confidence scales with how far outside the band price has gone
- Otherwise **HOLD** with confidence 0.5

## Why Bollinger Bands

- Complements RSI: BB uses *price location relative to volatility*, RSI uses *rate of change*
- Adapts to changing volatility (bands widen/narrow with VIX)
- Strong mean-reversion signal in range-bound regimes

## Limitations

- "Riding the band" — in strong trends, price can hug upper band for days while indicator screams overbought
- Standard 2-sigma works for normal regimes; in high-vol (VIX > 25) can produce too many signals
- Aggregator mitigates by requiring agreement from other indicators
