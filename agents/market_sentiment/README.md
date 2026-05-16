# Market Sentiment Agent

Classifies the overall macro mood for Indian equities. Called **once per
orchestrator run** (not per stock), making it cheap and shared.

## Inputs Collected via Connectors

- Nifty 50 (^NSEI)
- India VIX (^INDIAVIX)
- Dow Jones (^DJI) — proxy for global cues
- Crude WTI (CL=F)
- USD/INR (INR=X)

## LLM

Claude Haiku — fast, cheap, more than enough for classification.

## Contract

```python
def analyze() -> Signal  # symbol=None
```

## Failure Modes

- All data unavailable → returns HOLD, confidence 0
- LLM fails or response unparseable → returns HOLD, confidence 0.3
- Never raises
