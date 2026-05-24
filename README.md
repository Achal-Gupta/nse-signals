# NSE Trading Signals

> A multi-agent trading signal system for NSE.
> Runs on schedule, analyzes a dynamic 40-stock universe, logs outcomes
> across multiple time horizons, and emails consolidated recommendations.

**Current version:** v0.3.0

## What's New in v0.3.0

- **Dynamic 40-stock universe** (Universe Agent): 20 Nifty 100 large-caps
  + 20 news-trending stocks, refreshed daily
- **Multi-horizon outcome tracking**: same-day, 1d, 3d, 5d returns per signal
- **Backtesting**: `vectorbt`-based historical replay (`python backtest.py`)
- **Cleanup**: removed empty placeholder files for rule-based indicators

## What It Does (v0.3.0)

Every 15 minutes during NSE market hours:

1. Validates secrets
2. **Builds today's 40-stock universe** (cached for the day)
3. Computes market regime (VIX, Nifty trends)
4. Fetches market-wide sentiment via Claude Haiku (once per run)
5. For each of 40 watched stocks:
   - Pulls OHLCV
   - Runs 4 technical agents (RSI, MACD, BB, VWAP)
   - Runs news sentiment via Claude Haiku
   - Fuses market + stock sentiment
   - Aggregates signals using weighted scoring
6. Sends email + logs to Sheets (Signals + Universe tabs)

At end of day (16:00 IST), a separate EOD job closes paper trades:
- Fills `outcome_eod_pct`, `outcome_1d_pct`, `outcome_3d_pct`, `outcome_5d_pct`
  as data becomes available
- Records `outcome_best_horizon` (which horizon had the largest absolute return)

## Backtesting

```bash
# Backtest a few specific stocks for 90 days
python backtest.py --days 90 --symbols RELIANCE.NS TCS.NS INFY.NS

# Backtest today's full universe
python backtest.py --days 90 --universe
```

## What It Does NOT Do (Yet)

- Two-stage funnel for larger universes (v0.4.0)
- Learn from outcomes (v0.5.0 Reviewer Agent)
- Risk management / position sizing (v0.6.0)
- Real trade execution (v0.7.0)

See [docs/design/v0.3.0/decisions.md](docs/design/v0.3.0/decisions.md) for full roadmap.

## Cost

~₹400-600/month at v0.3.0 scale (40 stocks × ~26 runs/day).
Up from ~₹150/month at v0.2.0 (was 5 stocks).

## Schedule

External scheduling via cron-job.org (more reliable than GitHub Actions cron).
- Signals: every 15 min, 9:00-15:45 IST, Mon-Fri
- EOD review: once at 16:00 IST, Mon-Fri

## Status

| Version | Status |
|---------|--------|
| v0.1.0  | ✅ Released |
| v0.2.0  | ✅ Released |
| v0.3.0  | 🚧 In development |
