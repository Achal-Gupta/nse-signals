# v0.3.0 — Decisions & Roadmap

## Major Decisions

### 1. Universe Composition: 20 Nifty 100 + 20 News-Hybrid

Initially considered 10/10/20 with mid-caps explicitly included. Decided
against because:
- Mid-cap news sentiment quality degrades sharply (Google News RSS sparse)
- yfinance data quality dips for mid-caps (more "Insufficient data" returns)
- VWAP needs meaningful volume; mid-caps fail this often
- **News-hybrid already pulls in mid-caps that have catalysts**, so explicit allocation was redundant

The current setup gets cap diversity organically: news-hybrid will capture
mid-caps when they're in the news, but won't pollute the universe with
quiet mid-caps that produce no signal.

### 2. Daily Universe Refresh

Re-built every run, but only logged to Universe tab on the first run of the
day (9:15-9:30 IST window). News changes intra-day so the Universe Agent
recomputes, but logging once captures the morning baseline cleanly.

### 3. Fallback Universe Required

A 5-stock fallback list ensures the system never runs with zero stocks. If
both pools fail (network outage, data source down), the system gracefully
degrades to the v0.1.0 watchlist.

### 4. vectorbt for Backtesting (Not Custom Harness)

User chose vectorbt to minimize code maintenance. Tradeoffs accepted:
- vectorbt has feature surface we don't use
- Adds a heavy dependency (~50MB+ install)
- Less control over the exact replay logic

But: it handles drawdown, Sharpe, equity curve, etc. for free. Net win for
time-to-validation.

### 5. Backtests Use Neutral Sentiment (Not Replayed News)

Historical news sentiment is essentially impossible to reproduce — news APIs
don't reliably provide point-in-time historical headlines, and replaying
LLM sentiment classification on old headlines doesn't match what the live
system would have seen.

Decision: backtests use a neutral sentiment placeholder. This means:
- Backtest results measure **technical-only** performance
- The sentiment agent's contribution must be validated through live paper trading
- Per-agent hit rates from backtests are valid for RSI/MACD/BB/VWAP only

### 6. Multi-Horizon Outcomes (eod, 1d, 3d, 5d)

User pushed back on single-horizon (1d) in v0.2.0. Reasonable critique:
different signal types may play out at different time scales.

By logging all 4 horizons, the v0.5.0 Reviewer Agent can answer:
> "What's the optimal holding period for an RSI-driven BUY?"

This is dramatically more valuable than a single time horizon.

### 7. LangSmith Observability Deferred to v0.5.0

Originally planned for v0.3.0. Deferred after realizing:
- Current debugging needs are well-served by Sheets
- LangSmith's value peaks when Reviewer Agent makes non-deterministic decisions (v0.5.0)
- Adding tools preemptively is usually wrong; add them when there's pain

### 8. Cleanup of Empty Placeholder Files

In v0.2.0 we used Anthropic's agent packaging convention (`skill.md` +
`connectors.py` + `agent.py` + `subagents.py`). For rule-based indicators,
`connectors.py` and `subagents.py` were empty placeholder files with no
content beyond a docstring.

These add maintenance overhead without value. Removed in v0.3.0 for:
- `agents/rsi/`
- `agents/macd/`
- `agents/bollinger/`
- `agents/vwap/`

The `skill.md` and `README.md` files stay (they document the agent's role).
`connectors.py` and `subagents.py` will be created when an agent actually
needs them — not preemptively.

## What's NOT in v0.3.0

| Feature | Why deferred | Target |
|---|---|---|
| Two-stage funnel | One change at a time | v0.4.0 |
| Regime-aware aggregator weights | Wait for backtest insights | v0.4.0 |
| Reviewer Agent | Need 30+ days of multi-horizon outcomes | v0.5.0 |
| LangSmith observability | Add when Reviewer Agent ships | v0.5.0 |
| Risk Manager (target/stop-loss prices) | After Reviewer validates per-agent hit rates | v0.6.0 |
| Real broker integration | Approval-flow execution | v0.7.0 |

## Roadmap Going Forward

| Version | Theme |
|---|---|
| v0.1.0 | MVP plumbing — ✅ Released |
| v0.2.0 | Indicators + LangGraph + Paper trading — ✅ Released |
| **v0.3.0** | **Universe + Backtesting + Multi-horizon outcomes — 🚧 This release** |
| v0.4.0 | Two-stage funnel + Regime-aware weights |
| v0.5.0 | Reviewer Agent + LangSmith observability |
| v0.6.0 | Risk Manager (target prices, stop-losses, position sizing) |
| v0.7.0 | Broker integration (semi-auto with approval) |
| v0.8.0 | Sector Sentiment + Supabase migration |
| v0.9.0 | Oracle Cloud VM + Streamlit dashboard |
| v1.0.0 | Hardening, tests, docs, monitoring |

## Reality Checks for v0.3.0

### Cost Impact

- API cost ~3x v0.2.0: 40 stocks × Haiku per cycle (~₹15/day vs ₹5/day)
- Runtime ~3x: ~70-90s per cycle vs ~25s
- Still well within GitHub Actions free tier (~2,000 min/month)
- Anthropic budget bump needed: target ~₹400-600/month

### Don't Trust Backtests Too Much

Backtests on 90 days of NSE history will produce numbers — possibly very
optimistic. Reasons not to over-trust:
- Survivorship bias (only today's NSE-listed stocks tested)
- Daily candles smooth over intraday noise our live system sees
- No transaction costs, no slippage, no news sentiment
- Past 90 days may have been a friendly regime

Use backtest results to **rank indicators relative to each other**, not to
project absolute P&L.

### Universe Stability

40 stocks per day with daily news-driven refresh means the same stock may
or may not be in today's universe vs yesterday's. This:
- Makes per-stock outcome analysis harder (signal yesterday, no signal today)
- Is the right tradeoff for capturing real-time catalysts
- Becomes manageable in v0.5.0 when Reviewer Agent aggregates across stocks
