# NSE Trading Signals

> A multi-agent trading signal system for NSE.
> Runs on a schedule, analyzes stocks across multiple indicators + sentiment,
> logs outcomes, and emails consolidated recommendations.

**Current version:** v0.2.0

## What's New in v0.2.0

- **4 technical indicators**: RSI, MACD, Bollinger Bands, VWAP (covering momentum, trend, volatility, volume)
- **LangGraph orchestration** for clean topology and future parallelism
- **Score-based aggregator** — proper weighted combination of all signals
- **Paper trading** — every BUY/SELL gets an automatic outcome computed at EOD
- **Regime context** logged with every signal (VIX, Nifty trends)
- **Secret validation** at startup to catch misconfigured secrets fast

## What It Does (v0.2.0)

Every 15 minutes during NSE market hours, the system:

1. Validates secrets are present
2. Computes market regime (VIX, Nifty trends)
3. Fetches market-wide sentiment via Claude Haiku (once per run)
4. For each of 5 watched stocks:
   - Pulls OHLCV
   - Runs 4 technical indicator agents (RSI, MACD, BB, VWAP)
   - Runs news sentiment via Claude Haiku
   - Fuses market + stock sentiment
   - Combines all 5 signals with weighted aggregator
5. Sends consolidated email
6. Logs everything (including per-indicator detail) to Google Sheets

At end of day (16:00 IST), a separate job closes paper trades by fetching
actual outcomes and writing P&L back to the Sheet.

## What It Does NOT Do (Yet)

- Execute trades (v0.7.0)
- Backtest on historical data (v0.3.0)
- Dynamic stock universe (v0.3.0)
- Learn weights from past outcomes (v0.5.0)
- Risk management / position sizing (v0.6.0)

See [docs/design/v0.2.0/decisions.md](docs/design/v0.2.0/decisions.md) for full roadmap.

## Architecture

See [docs/design/v0.2.0/architecture.md](docs/design/v0.2.0/architecture.md).

## Setup

GitHub secrets required (same as v0.1.0):
- `ANTHROPIC_API_KEY`
- `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`
- `GOOGLE_SHEETS_CREDS_JSON`, `GOOGLE_SHEET_ID`

## Cost

~₹100-200/month (LangGraph and new indicators add no LLM cost).

## Status

| Version | Status |
|---------|--------|
| v0.1.0  | ✅ Released |
| v0.2.0  | 🚧 In development |
