# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0] - 2026-05-XX

### Added
- **Universe Agent** (`agents/universe/`) — dynamic 40-stock watchlist:
  20 from Nifty 100 baseline (filtered by liquidity) + 20 news-hybrid
  (news mentions + market movers)
- **Multi-horizon outcome tracking** — per-signal returns at eod, 1d, 3d, 5d
  horizons + `outcome_best_horizon` column
- **vectorbt-based backtester** (`lib/backtester.py`) — replay agents against
  90-day daily history; produces per-agent hit rates and aggregate metrics
- **Backtest CLI** (`backtest.py`) — `python backtest.py --days 90 --symbols X.NS Y.NS`
- **Universe Sheet tab** — daily snapshot of selected stocks for analysis
- **Nifty 100 baseline data** (`data/nifty_100_baseline.yaml`)
- **Universe config** (`config/universe_config.yaml`) — tunable pool sizes and thresholds
- **Universe dataclass** in `lib/contracts.py`
- **`universe_source` field** on Verdict — tracks which pool each stock came from

### Changed
- **Sheet schema expanded** from 27 to 33 columns. Requires manual migration
  (clear row 1 of existing sheet or use a fresh sheet)
- **Verdict** now carries `universe_source`
- **Paper trader** now fills outcomes at 4 horizons instead of single 1-day
- **Orchestrator** integrates Universe Agent as a new LangGraph node
- **EOD review** updated for multi-horizon outcome closure
- **requirements.txt** — added `vectorbt`

### Removed
- Empty placeholder files removed from rule-based agents (cleanup of v0.2.0
  packaging debt):
  - `agents/rsi/connectors.py`, `agents/rsi/subagents.py`
  - `agents/macd/connectors.py`, `agents/macd/subagents.py`
  - `agents/bollinger/connectors.py`, `agents/bollinger/subagents.py`
  - `agents/vwap/connectors.py`, `agents/vwap/subagents.py`

### Migration Notes
- Sheet schema changed; clear row 1 of existing sheet OR use a fresh sheet
  and update `GOOGLE_SHEET_ID` secret
- Watchlist is now dynamic — `config/watchlist.yaml` is deprecated but
  retained as a manual override path (not implemented in v0.3.0)
- LangSmith was originally planned for v0.3.0 but deferred to v0.5.0

## [0.2.0] - 2026-05-19

(See v0.2.0 git tag)

## [0.1.0] - 2026-05-16

(See v0.1.0 git tag)
