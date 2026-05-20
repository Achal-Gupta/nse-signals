# Universe Agent

Dynamically selects 40 stocks each trading day. Runs once at first cycle after
market open and the result is cached for the rest of the day.

## Contract

```python
def build_universe() -> Universe
```

Returns a `Universe` dataclass (see `lib/contracts.py`).

## Composition (v0.3.0)

| Pool | Count | Source |
|---|---|---|
| Nifty 100 baseline | 20 | Top by avg traded value over 5 days |
| News-hybrid | 20 | Stocks mentioned in market news + top movers |

Total: **40 stocks** (with overlap deduplication).

## Failure Modes

- Pool 1 fails → Pool 2 only (up to 20 stocks)
- Pool 2 fails → Pool 1 only (up to 20 stocks)
- Both fail → 5-stock fallback (RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK)
- Never raises an exception

## Configuration

Tunable via `config/universe_config.yaml`:

```yaml
pool1_count: 20            # Nifty 100 baseline target size
pool2_count: 20            # News-hybrid target size
min_volume_value: 5e8      # ₹50 crore minimum daily traded value
```

## Why News-Hybrid?

Static large-cap watchlists miss stocks that have catalysts on a given day.
News-hybrid captures stocks the market is actively focused on. Combined with
the stable Nifty 100 baseline, this gives both reliability and opportunity.
