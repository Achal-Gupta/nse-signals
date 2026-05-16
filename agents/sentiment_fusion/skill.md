# Sentiment Fusion — Skill Definition

## Role

Combine the macro market sentiment with per-stock sentiment into one
fused sentiment signal that the orchestrator uses for final aggregation.

## Logic (Rule-based in v0.1.0, no LLM)

### Score Mapping

Each input Signal is converted to a numeric score:
- BUY  →  +confidence
- HOLD →   0
- SELL →  -confidence

Score range: [-1.0, +1.0]

### Weighted Fusion

```
fused_score = 0.4 * market_score + 0.6 * stock_score
```

The 60/40 stock-over-market weighting reflects that the per-stock signal is
more direct, while market mood provides important context.

### Market Override Rule

If `market_signal.action == "SELL"` AND `market_signal.confidence > 0.7`:
- Any fused BUY is downgraded to HOLD (capital preservation in bearish
  macro environments)

If `market_signal.action == "BUY"` AND `market_signal.confidence > 0.7`:
- Any fused SELL is downgraded to HOLD (don't fight strong bullish tape)

### Final Action

- `fused_score > 0.25` → BUY (confidence = abs(fused_score))
- `fused_score < -0.25` → SELL (confidence = abs(fused_score))
- otherwise → HOLD

The 0.25 threshold avoids weak signals becoming actionable.
