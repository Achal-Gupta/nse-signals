# Technical Agent

Rule-based technical analysis. Currently uses only RSI(14).

## Files

| File | Purpose |
|---|---|
| `skill.md` | Role + rules (what an LLM version would use as system prompt) |
| `connectors.py` | Empty in v0.1.0 (no external data; receives DataFrame) |
| `agent.py` | Entry point: `analyze(symbol, df) -> Signal` |
| `subagents.py` | Empty in v0.1.0; will host MACD/EMA/BB in v0.2.0 |

## Contract

```python
def analyze(symbol: str, df: pd.DataFrame) -> Signal
```

Returns a `Signal` with `action ∈ {BUY, SELL, HOLD}` and confidence 0–1.
On any error, returns `HOLD` with confidence 0 (never raises).
