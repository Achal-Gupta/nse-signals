# v0.3.0 — Data Contracts

## New: `Universe`

```python
@dataclass
class Universe:
    timestamp_ist: str
    stocks: list[dict]      # [{symbol, name, source, ...metadata...}]
    pool1_size: int         # how many came from Nifty 100 baseline
    pool2_size: int         # how many came from news-hybrid
    overlaps: int           # how many appeared in both pools
    errors: list[str]
```

The `source` field on each stock is one of:
- `"nifty100"` — from Pool 1 (Nifty 100 baseline by liquidity)
- `"news_hybrid"` — from Pool 2 (news mentions + market movers)
- `"nifty100+news_hybrid"` — in both pools
- `"fallback"` — used when both pools failed

## Updated: `Verdict`

Added field:

```python
universe_source: str   # e.g. "nifty100" — for downstream analysis
```

## Multi-Horizon Outcomes

```python
OUTCOME_HORIZONS = ["eod", "1d", "3d", "5d"]
HORIZON_DAYS = {"eod": 0, "1d": 1, "3d": 3, "5d": 5}
```

For each BUY/SELL signal, P&L is computed at all 4 horizons as data becomes
available. Math:

```
BUY:  pct = (close_at_horizon - price_at_signal) / price_at_signal × 100
SELL: pct = (price_at_signal - close_at_horizon) / price_at_signal × 100
```

`outcome_best_horizon` records the horizon with the largest absolute return.

## Google Sheet Schema (33 columns)

### Signals Tab

| # | Column | Source |
|---|---|---|
| 1 | timestamp_ist | orchestrator |
| 2 | symbol | universe |
| 3 | universe_source | universe (`nifty100` / `news_hybrid` / etc.) |
| 4 | final_action | aggregator |
| 5 | final_confidence | aggregator |
| 6 | price_at_signal | data fetcher |
| 7 | aggregator_score | aggregator |
| 8 | rsi_action | rsi agent |
| 9 | rsi_value | rsi metrics |
| 10 | macd_action | macd agent |
| 11 | macd_hist | macd metrics |
| 12 | bb_action | bb agent |
| 13 | bb_percent_b | bb metrics |
| 14 | vwap_action | vwap agent |
| 15 | vwap_distance_pct | vwap metrics |
| 16 | stock_sent_action | stock sentiment |
| 17 | stock_sent_reason | stock sentiment |
| 18 | market_action | market sentiment |
| 19 | market_reason | market sentiment |
| 20 | fused_sent_action | sentiment fusion |
| 21 | fused_sent_confidence | sentiment fusion |
| 22 | vix_level | regime |
| 23 | vix_pct_change | regime |
| 24 | nifty_pct | regime |
| 25 | nifty_5d_pct | regime |
| 26 | outcome_eod_pct | paper trader (EOD same day) |
| 27 | outcome_1d_pct | paper trader (next trading day) |
| 28 | outcome_3d_pct | paper trader (3 trading days later) |
| 29 | outcome_5d_pct | paper trader (5 trading days later) |
| 30 | outcome_best_horizon | paper trader |
| 31 | outcome_status | (legacy, may be deprecated) |
| 32 | errors | global per-run errors |
| 33 | _padding | reserved for v0.4+ |

### Universe Tab (new)

| Column | Contents |
|---|---|
| timestamp_ist | when universe was built |
| symbol | NSE symbol |
| name | company name |
| source | which pool selected it |
| extra_metadata_json | additional metrics (traded value, news mentions, etc.) |

One row per stock per day. ~40 rows/day, ~880 rows/month.

## Backtester Contract

```python
def backtest_symbol(symbol: str, days: int = 90, include_sentiment: bool = False) -> BacktestResult
```

Returns aggregated metrics and per-agent hit rates.

### Backtest Limitations (Important to Document)

- **Uses daily candles**, not 15-min as live system does
- **No historical news** — sentiment agent uses neutral placeholder
- **Per-agent hit rate** uses each agent's signal direction × next-day return
- **No transaction costs / slippage** modeled
- **No multi-horizon** in backtests — uses next-day return only
- **Survivorship bias** — backtests on today's listings ignore delisted stocks

Use backtest output as a *directional sanity check*, not a P&L prediction.
