# Data Fetcher

Pulls OHLCV (candle) data and index snapshots via `yfinance`. Not an LLM
agent — pure data access. Provided as a packaged module so future versions
can swap to Kite/Upstox APIs without touching consumers.

## Functions

- `get_ohlcv(symbol, period, interval) -> DataFrame | None` — candle data
- `get_index_snapshot(symbol) -> dict | None` — `{close, pct_change}` for an index

## Notes

- All NSE stock symbols need the `.NS` suffix (e.g. `RELIANCE.NS`)
- Nifty 50: `^NSEI`, India VIX: `^INDIAVIX`
- yfinance can be flaky — every call returns `None` on failure, never raises
