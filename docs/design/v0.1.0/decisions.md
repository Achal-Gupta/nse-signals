# v0.1.0 — Decisions & Roadmap

## Why These Choices (Major Decisions)

### 1. Linear Pipeline, No LangGraph (Yet)

With only 2 effective agents (Technical + Sentiment), LangGraph adds setup
overhead without parallelism benefit. We'll migrate in v0.2.0 when agent
count grows to 4+. The agent contracts (`Signal` dataclass) are designed
to be drop-in compatible with a LangGraph state object.

### 2. Two-Tier Sentiment (Market + Stock)

Stock-specific news is often overwhelmed by macro mood. Splitting sentiment
into a market-wide agent (runs once per cycle, cheap) and a stock-specific
agent (runs per stock) captures both signals. The Fusion module applies a
40/60 market/stock weighting and a "strongly bearish market → downgrade
all BUYs" override.

### 3. Email (Gmail SMTP) Instead of Telegram

- Free, zero setup beyond a Gmail app password
- Phone push via Gmail app is reliable
- Email inbox serves as a free searchable audit log

### 4. Google Sheets as v0.1.0 Storage

- Viewable on phone, no DB setup
- Adequate for ~3,000 rows/month
- Will migrate to SQLite/Supabase in v0.9.0 when it gets slow

### 5. GitHub Actions for Scheduling

- Free 2,000 min/month (we use ~1,100 at 15-min cadence with 30s runs)
- No server to maintain
- Phone-manageable via GitHub mobile

### 6. Agent Packaging (`skill.md` + `connectors.py` + `agent.py` + `subagents.py`)

Inspired by Anthropic's Finance Agents (released May 2026), which package
agents as skills + connectors + subagents. We adopt the same convention
so each agent is a self-contained module — making future agent additions
mechanical, not architectural rework.

### 7. RSI Only (No MACD/EMA/BB Yet)

v0.1.0 prioritizes end-to-end plumbing over technical sophistication.
Adding more indicators is trivial once the plumbing works (v0.2.0).

### 8. Claude Haiku for All LLM Calls

- Cheapest model, sub-second latency
- Sentiment classification doesn't need Opus-level reasoning
- Opus will be used in v0.5.0 for the Reviewer Agent (complex reasoning over trade history)

## What's Explicitly NOT in v0.1.0

| Feature | Why deferred | Target version |
|---|---|---|
| Dynamic stock universe | Hardcoded 5 stocks proves the loop first | v0.3.0 |
| Backtesting | Need clean signal contracts first | v0.3.0 |
| Multi-indicator agents (MACD, EMA, BB) | Pipeline maturity first | v0.2.0 |
| Reviewer Agent (learning loop) | Need ≥30 days of signal data first | v0.5.0 |
| Risk Manager | No trade execution yet, no need | v0.6.0 |
| Broker integration | Manual approval flow only at v0.7.0 | v0.7.0 |
| Sector Sentiment Agent | One more layer of sentiment before adding | v0.8.0 |
| Production hosting (Oracle Cloud) | GitHub Actions sufficient until v0.5.0 | v0.9.0 |

## Roadmap (Each Step ≈ 2–4 Weeks)

| Version | Theme | Key additions |
|---|---|---|
| **v0.1.0** ← here | MVP plumbing | 2 agents, email, Sheets, GitHub Actions |
| **v0.2.0** | More indicators + LangGraph + Paper trading | MACD, EMA, BB; agents run in parallel via LangGraph; daily P&L tracking on hypothetical trades |
| **v0.3.0** | Universe Agent + Backtesting | Nifty 200 filter; replay last 90 days against current agents |
| **v0.4.0** | Two-stage funnel | Fast Screener reduces universe to ~15 candidates before deep analysis |
| **v0.5.0** | Reviewer Agent | End-of-day Claude Opus 4.7 analysis writes Lessons that next-day agents read |
| **v0.6.0** | Risk Manager | Position sizing, stop-loss, max daily loss |
| **v0.7.0** | Broker integration | Upstox/Dhan API; email approval link → places order |
| **v0.8.0** | Sector Sentiment + Supabase | Add 11-sector sentiment layer; migrate primary storage to Postgres |
| **v0.9.0** | Oracle Cloud VM | Move off GitHub Actions for always-on reliability + dashboard |
| **v1.0.0** | Hardening | Error handling, tests, monitoring, full documentation |

## Setup Steps (Mobile-Only)

### 1. Anthropic API Key
- Open `console.anthropic.com` in mobile browser
- Sign up → API Keys → Create key
- Copy and save

### 2. Gmail App Password
- Open `myaccount.google.com` → Security
- Enable 2-Step Verification (if not already)
- Search "App passwords" → create one named "NSE Signals"
- Save the 16-char password

### 3. Google Sheets Setup
- Create a new Google Sheet, name it "NSE Signals Log"
- Copy the Sheet ID from URL (between `/d/` and `/edit`)
- Go to `console.cloud.google.com`
- New project → Enable Google Sheets API → Create Service Account
- Generate JSON key, download
- Share the Sheet with the service account email (Editor access)
- Base64-encode the JSON file (use any online base64 tool from your phone)

### 4. GitHub Secrets
In your repo: Settings → Secrets and variables → Actions → New repository secret

Add:
- `ANTHROPIC_API_KEY`
- `GMAIL_USER` (your Gmail address)
- `GMAIL_APP_PASSWORD` (16-char app password)
- `ALERT_EMAIL_TO` (where to send alerts; can be your Gmail)
- `GOOGLE_SHEETS_CREDS_JSON` (base64 of the service account JSON)
- `GOOGLE_SHEET_ID` (from your Sheet URL)

### 5. Enable Actions
Repo → Actions tab → enable workflows

### 6. Initialize the Sheet
First run will auto-create the header row. You can also do this manually.

### 7. Watch It Run
Next 15-min boundary during market hours, you'll receive an email.
