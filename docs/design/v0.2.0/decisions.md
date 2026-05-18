# v0.2.0 — Decisions & Roadmap

## Major Decisions

### 1. LangGraph Adopted (Full Migration)

Replaced linear Python function calls with a `StateGraph`. Six named nodes,
one conditional edge (market hours short-circuit).

**Why now (not gradual):**
- All future versions (Universe routing, Reviewer feedback, Risk Manager) need it
- Refactoring once now is cheaper than twice later
- Per-stock loop stays serial inside one node for v0.2.0; parallel fanout via Send
  is a v0.3.0 change (when watchlist grows beyond 5)

### 2. Score-Based Aggregator (The v0.1.1 Bug Fix)

v0.1.0 logic: "tech & sentiment must both agree on direction or HOLD" — this
suppressed valid signals when one agent was simply neutral. Fixed by converting
each signal to a signed score in [-1, +1] and summing with weights.

```
score = Σ (weight_i × score_i)
|score| > 0.20 → directional verdict
```

### 3. Four Diverse Indicators (Not Just More Indicators)

Each indicator captures a different dimension:

| Dimension | Indicator |
|---|---|
| Momentum (mean reversion at extremes) | RSI |
| Trend & momentum | MACD |
| Volatility-aware mean reversion | Bollinger |
| **Volume confirmation** | VWAP |

We deliberately dropped EMA crossover. EMA is highly correlated with MACD
(both derived from moving averages of the same close prices) and would have
added redundancy disguised as diversity. VWAP fills the only missing
dimension — volume.

### 4. Initial Weights Are Educated Guesses

```python
DEFAULT_WEIGHTS = {
    "rsi":               0.15,
    "macd":              0.25,    # slightly higher: cleaner directional signal
    "bollinger":         0.15,
    "vwap":              0.15,
    "sentiment_fusion":  0.30,    # highest: news catalysts often drive short-term moves
}
```

These are **starting values, not ground truth.** The Reviewer Agent in v0.5.0
will tune them from real outcome data. Until then, all weights are essentially
hypothesis to be tested.

### 5. Paper Trading via Sheet Outcomes (Not Backtesting)

Backtesting was considered for v0.2.0 but deferred to v0.3.0. Paper trading
on live data:
- Costs nothing extra (we're already running the system live)
- Doesn't have look-ahead bias risk
- Builds the dataset the Reviewer Agent needs anyway

**Honest tradeoff:** slower data accumulation than backtesting (one trading day
at a time vs replaying 90 days in one afternoon). That's the price for not
shipping bug-prone historical replay infrastructure in v0.2.0.

### 6. Sheet Schema Expansion (14 → 27 columns)

Wide row, narrow logic. The Reviewer Agent in v0.5.0 needs per-indicator
detail to compute hit rates. We log it now even though nothing reads it yet.

Existing v0.1.0 sheets will *not* auto-migrate. Two options:
- Create a new sheet for v0.2.0 (recommended — clean schema, clear cutoff)
- Manually update header row in existing sheet

### 7. Regime Context Logged But Not Used (Yet)

Every row carries VIX level, VIX change, today's Nifty %, and Nifty 5-day %.
v0.2.0 doesn't use these for routing — the same weights apply regardless of
regime. v0.4.0 will introduce regime-aware weight selection.

We log now to **build the analysis-ready dataset** for free.

### 8. Renamed `agents/technical/` → `agents/rsi/`

"Technical" was confusing once we had 4 technical agents. Each indicator
gets its own top-level folder. Git tracks the rename.

### 9. Secret Validation at Startup

Lesson learned from v0.1.0 deployment: empty/typo'd secrets cause cryptic
runtime errors deep in the pipeline. `verify_secrets()` runs first; if any
required env var is missing or blank, the entire run aborts with a clear
message and exit code 1.

### 10. Notification Channel Stays Email

Decision deferred — email works, no compelling reason to add WhatsApp/Pushover
in v0.2.0. Reconsider when daily email volume becomes annoying.

## What's NOT in v0.2.0

| Feature | Why deferred | Target |
|---|---|---|
| Dynamic stock universe | Stick with 5 stocks for v0.2.0 stability | v0.3.0 |
| Backtesting on historical data | Paper trading first | v0.3.0 |
| Two-stage funnel (fast screener) | Need more stocks first | v0.4.0 |
| Reviewer Agent (Lessons + weight tuning) | Need ≥30 days of outcome data | v0.5.0 |
| Risk Manager | No execution yet | v0.6.0 |
| Broker integration | Approval-flow execution | v0.7.0 |
| Sector sentiment | Additional sentiment dimension | v0.8.0 |
| Migrate Sheets → Supabase | Sheets adequate until volume grows | v0.9.0 |

## Roadmap Going Forward

| Version | Theme | Key additions |
|---|---|---|
| v0.1.0 | MVP plumbing | ✅ Released |
| **v0.2.0** | **Indicators + LangGraph + Paper trading** | **🚧 This release** |
| v0.3.0 | Universe Agent + Backtesting | Dynamic Nifty 200 watchlist; historical replay |
| v0.4.0 | Two-stage funnel + Regime-aware weights | Fast screener; weights vary by VIX regime |
| v0.5.0 | Reviewer Agent | Daily Claude Opus 4.7 analysis updates weights & lessons |
| v0.6.0 | Risk Manager | Position sizing, stop-loss logic |
| v0.7.0 | Broker integration | Upstox/Dhan API + approval link in email |
| v0.8.0 | Sector Sentiment + Supabase | Sector dimension + DB migration |
| v0.9.0 | Oracle Cloud VM + Dashboard | Production hosting + Streamlit |
| v1.0.0 | Hardening | Tests, monitoring, docs |

## Reality Checks for v0.2.0

Three honest cautions:

1. **More indicators ≠ better signals.** RSI/MACD/BB are all derived from the
   same OHLCV close series. They're correlated. VWAP is the only one giving
   independent information via volume. Don't read "4 indicators agree → BUY"
   as 4 independent votes.

2. **Initial weights might be wrong.** We picked them with reasoning, not data.
   Until Reviewer Agent runs in v0.5.0, treat all aggregated verdicts with
   appropriate skepticism. Real money trading still off the table.

3. **Paper trading is optimistic.** Outcomes use close-to-close P&L. Real trades
   would lose to slippage, brokerage, and stop-loss interactions. Treat
   `outcome_pct` as a *relative ranking signal*, not absolute P&L.
