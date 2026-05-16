# NSE Trading Signals

> A multi-agent trading signal system for NSE (National Stock Exchange of India).
> Runs on a schedule, analyzes stocks using technical indicators and news sentiment,
> and sends consolidated recommendations via email.

**Current version:** v0.1.0 (MVP)

## What It Does (v0.1.0)

Every 15 minutes during NSE market hours (9:15 AM – 3:30 PM IST, Mon–Fri):

1. Fetches OHLCV data for 5 large-cap stocks
2. Runs a Technical Agent (RSI) on each
3. Runs a Market Sentiment Agent (Nifty, VIX, global cues) — once per cycle
4. Runs a Stock Sentiment Agent (Google News + Claude Haiku) per stock
5. Fuses market + stock sentiment with weighted rules
6. Aggregates technical + fused sentiment into a final BUY/SELL/HOLD verdict
7. Emails the consolidated signals
8. Logs everything to Google Sheets

## What It Does NOT Do (Yet)

- Execute trades (planned for v0.7.0)
- Dynamic stock universe (planned for v0.3.0)
- Learn from past trades (planned for v0.5.0)
- Backtest strategies (planned for v0.3.0)

See [docs/design/v0.1.0/decisions.md](docs/design/v0.1.0/decisions.md) for the full roadmap.

## Architecture

See [docs/design/v0.1.0/architecture.md](docs/design/v0.1.0/architecture.md) for the system design.

## Setup

See [docs/design/v0.1.0/decisions.md](docs/design/v0.1.0/decisions.md) for a step-by-step setup guide.

You need to add these secrets to your GitHub repo (Settings → Secrets and variables → Actions):

- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `GMAIL_USER` — your Gmail address
- `GMAIL_APP_PASSWORD` — Google App Password (not your regular password)
- `ALERT_EMAIL_TO` — where alerts get sent
- `GOOGLE_SHEETS_CREDS_JSON` — service account JSON, base64-encoded
- `GOOGLE_SHEET_ID` — the ID from your Sheet's URL

## Tech Stack

- **Language:** Python 3.11
- **Scheduler:** GitHub Actions (cron)
- **Data:** yfinance (free)
- **News:** Google News RSS (free)
- **LLM:** Anthropic Claude Haiku
- **Notification:** Gmail SMTP
- **Storage:** Google Sheets API

## Cost

~₹100–200/month at v0.1.0 scale.

## Status

| Version | Status |
|---------|--------|
| v0.1.0  | 🚧 In development |
