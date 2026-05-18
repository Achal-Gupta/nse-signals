# v0.2.0 — Architecture

## Goal

Expand the signal generation from 1 technical indicator + sentiment to 4 diverse
indicators (covering momentum, trend, volatility, volume) + sentiment, combined
with a proper weighted aggregator. Migrate orchestration to LangGraph. Begin
collecting per-indicator outcome data via a paper trader.

## System Context

```mermaid
graph LR
    User[You<br/>mobile]
    System[NSE Signals v0.2.0<br/>GitHub Actions]

    YF[yfinance<br/>OHLCV + Indices]
    GN[Google News RSS]
    AN[Anthropic<br/>Claude Haiku]
    GS[Google Sheets<br/>signals + outcomes]
    SMTP[Gmail SMTP]

    System --> YF
    System --> GN
    System --> AN
    System --> GS
    System --> SMTP
    SMTP --> User
```

## Pipeline Topology (LangGraph)

```mermaid
graph TD
    START([START]) --> CHECK
    CHECK[check_market_hours]
    CHECK -->|outside hours| END_SKIP([END])
    CHECK -->|in hours| WL[load_watchlist]
    WL --> REG[compute_regime<br/>VIX + Nifty trends]
    REG --> MS[market_sentiment<br/>Claude Haiku once]
    MS --> APS[analyze_per_stock<br/>loop over 5 stocks]
    APS --> NL[notify_and_log]
    NL --> END([END])

    subgraph "Per-Stock Analysis (inside analyze_per_stock node)"
        DF[Data Fetcher] --> RSI[RSI Agent]
        DF --> MACD[MACD Agent]
        DF --> BB[Bollinger Agent]
        DF --> VWAP[VWAP Agent]
        DF --> SSN[Stock News<br/>Claude Haiku]
        SSN --> SF[Sentiment Fusion]
        RSI --> AGG[Score-Based Aggregator]
        MACD --> AGG
        BB --> AGG
        VWAP --> AGG
        SF --> AGG
        AGG --> V[Verdict]
    end
```

## EOD Workflow (separate cron)

```mermaid
graph LR
    Cron[16:00 IST cron] --> EOD[eod_review.py]
    EOD --> PT[paper_trader.close_pending_trades]
    PT -->|read previous day's<br/>BUY/SELL rows| Sheet[Google Sheet]
    PT -->|fetch close price| YF[yfinance]
    PT -->|write outcome_pct,<br/>outcome_status| Sheet
```

## Component List

| Component | Role | Path |
|---|---|---|
| **Orchestrator** | LangGraph runner | `orchestrator.py` |
| **EOD Reviewer** | Close paper trades | `eod_review.py` |
| **Secret Validator** | Fail-fast on missing/blank secrets | `lib/secret_validator.py` |
| **Aggregator** | Weighted score across all signals | `lib/aggregator.py` |
| **Paper Trader** | EOD outcome calculator | `lib/paper_trader.py` |
| **LangGraph State** | Shared state schema | `lib/langgraph_state.py` |
| **Data Fetcher** | yfinance wrapper | `agents/data_fetcher/` |
| **RSI Agent** | Mean reversion | `agents/rsi/` |
| **MACD Agent** | Trend / momentum | `agents/macd/` |
| **Bollinger Agent** | Volatility mean reversion | `agents/bollinger/` |
| **VWAP Agent** | Volume confirmation | `agents/vwap/` |
| **Market Sentiment** | Macro mood (Claude Haiku) | `agents/market_sentiment/` |
| **Stock Sentiment** | Per-company news (Claude Haiku) | `agents/stock_sentiment/` |
| **Sentiment Fusion** | Combine market + stock | `agents/sentiment_fusion/` |
| **Email Notifier** | HTML email | `lib/email_notifier.py` |
| **Sheets Logger** | Append rows + write outcomes | `lib/sheets_logger.py` |
| **Contracts** | Signal, Verdict, Regime dataclasses | `lib/contracts.py` |

## Indicator Diversity Justification

We deliberately chose indicators that capture different dimensions of price action:

| Dimension | Indicator | Why |
|---|---|---|
| Momentum (rate of change) | RSI | Mean reversion at extremes |
| Trend direction & strength | MACD | Cleaner trend signal than EMA cross |
| Volatility / mean reversion (vol-aware) | Bollinger Bands | Adapts to changing volatility |
| **Volume confirmation** | VWAP | The only volume-based indicator; institutional benchmark |

We dropped EMA crossover (planned in earlier drafts) because it's heavily
correlated with MACD. Adding VWAP gives a categorically different signal.

## Schedule

- **Main signals workflow**: every 15 min, 9:15–15:30 IST, Mon–Fri
- **EOD review workflow**: 16:00 IST, Mon–Fri (after market close)
- Both workflows support `workflow_dispatch` for manual triggering

## Error Handling

Same defensive pattern as v0.1.0:
- One stock failure → skip it, continue
- Any agent failure → return HOLD with confidence 0
- Sheet logging failures don't break the run (try/except wraps it)
- Secret validation runs first; if it fails, no agents run

## Future Extensibility (v0.3.0+)

The LangGraph topology is designed so that:
- `analyze_per_stock` becomes a parallel `Send`-based fanout (v0.3.0)
- `compute_regime` can route to different aggregator weights (v0.4.0)
- A `reviewer` node can be added after `notify_and_log` (v0.5.0)
- `risk_manager` node added between `analyze_per_stock` and `notify_and_log` (v0.6.0)
