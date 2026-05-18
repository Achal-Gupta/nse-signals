# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-05-XX

### Added
- **New indicator agents**: MACD, Bollinger Bands, VWAP
  (4 technical agents total now: RSI + MACD + BB + VWAP)
- **Score-based aggregator** (`lib/aggregator.py`) — weighted sum across all
  indicator + sentiment signals. Replaces the v0.1.0 "both must agree or HOLD"
  rule that was too conservative. Each indicator has a starting weight; Reviewer
  Agent will tune these in v0.5.0.
- **LangGraph orchestration** — orchestrator is now a `StateGraph` with named
  nodes and conditional edges. Sets foundation for v0.3.0+ parallel fanout.
- **Paper trader** (`lib/paper_trader.py`) — EOD job that fills in actual outcomes
  (next-trading-day close vs signal price) on BUY/SELL signals.
- **Regime context tags** — every signal now logged with VIX level, VIX change,
  Nifty today %, Nifty 5-day %.
- **Per-indicator outcome logging** — Sheet schema expanded to 27 columns,
  capturing each indicator's action and key metric. Enables Reviewer Agent
  (v0.5.0) to compute per-indicator hit rates.
- **Secret validator** (`lib/secret_validator.py`) — fails fast at startup if
  any required env var is missing or blank. Catches the empty-secret bug class
  hit during v0.1.0 deployment.
- **EOD workflow** (`.github/workflows/eod-review.yml`) — separate scheduled job
  for end-of-day paper trade closure.
- **Design docs** for v0.2.0 in `docs/design/v0.2.0/`.

### Changed
- **Renamed** `agents/technical/` → `agents/rsi/` (technical was misleading
  once we have 4 technical agents).
- **Sheet schema expanded** from 14 to 27 columns. Existing v0.1.0 sheets are
  NOT auto-migrated; create a new sheet or manually update headers.
- **Email format** now includes per-indicator action summary
  (`RSI:H · MACD:B · BB:H · VWAP:S · SENT:B`) and regime line.
- `lib/contracts.py` — `Verdict` dataclass now carries `per_agent_signals`,
  `regime`, `aggregator_score`, `price_at_signal`.

### Fixed
- Aggregator no longer suppresses sentiment signals when RSI is in neutral
  zone (the bug discovered in v0.1.0 testing).

### Migration Notes
- Add `langgraph` to your environment (already in `requirements.txt`).
- Sheet headers changed. To migrate: clear the first row of your Sheet, then
  next run will auto-populate v0.2.0 headers. Historical data without new
  columns will still be in the rows below (left-aligned).
- Add `GOOGLE_SHEETS_CREDS_JSON` and `GOOGLE_SHEET_ID` continue to be required.

## [0.1.0] - 2026-05-16

Initial MVP release. See git tag `v0.1.0`.
