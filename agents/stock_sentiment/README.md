# Stock Sentiment Agent

Per-company news sentiment via Google News RSS + Claude Haiku.

## Contract

```python
def analyze(symbol: str, company_name: str) -> Signal
```

## Sources

- **Google News RSS** — free, no API key. Query: `"<company_name> stock"`,
  Indian region (`gl=IN`).

## Limitations to Acknowledge

- Google News doesn't always return highly relevant or recent headlines for
  smaller companies
- No deduplication if multiple outlets cover the same story (5 stories about
  one earnings call would all look positive, inflating signal)
- v0.2.0 may add dedup + source weighting
