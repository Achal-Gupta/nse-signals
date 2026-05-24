# v0.3.0 — Architecture

## Goal

Expand from a hardcoded 5-stock watchlist to a dynamic 40-stock universe
selected daily, while adding multi-horizon outcome tracking and a backtesting
harness for historical validation.

## What's New

| Capability | Source |
|---|---|
| Universe Agent | Dynamic stock selection: 20 Nifty 100 + 20 news-hybrid |
| Multi-horizon outcomes | eod, 1d, 3d, 5d returns per signal |
| Backtesting | `vectorbt`-based historical replay |
| Universe Sheet tab | Daily snapshot of selected stocks |

## Pipeline Topology (LangGraph)

```mermaid
graph TD
    START([START]) --> CHECK
    CHECK[check_market_hours]
    CHECK -->|outside hours| END_SKIP([END])
    CHECK -->|in hours| UNI[build_universe<br/>40 stocks]
    UNI --> REG[compute_regime<br/>VIX + Nifty trends]
    REG --> MS[market_sentiment<br/>Claude Haiku once]
    MS --> APS[analyze_per_stock<br/>loop over 40 stocks]
    APS --> NL[notify_and_log<br/>email + Sheets + Universe tab]
    NL --> END([END])
```

## Universe Agent Detail

```mermaid
graph TD
    NIFTY[Nifty 100 baseline YAML]
    NEWS[Google News RSS]
    YF[yfinance market data]

    NIFTY --> FILT[Filter by liquidity<br/>avg traded value > ₹50cr]
    FILT --> POOL1[Pool 1: top 20<br/>by traded value]

    NEWS --> MENT[Extract mentioned<br/>company names]
    YF --> MOVE[Top movers<br/>by pct change]
    NIFTY --> MENT
    NIFTY --> MOVE

    MENT --> MERGE[Merge + dedup]
    MOVE --> MERGE
    MERGE --> POOL2[Pool 2: top 20<br/>news-hybrid]

    POOL1 --> FINAL[Final Universe:<br/>40 stocks deduplicated]
    POOL2 --> FINAL
```

## Multi-Horizon Outcome Flow

```mermaid
graph LR
    SIGNAL[Signal fires at<br/>T = signal time] --> SAME[Same-day close<br/>knowable at end of T]
    SAME --> D1[1d close<br/>knowable at end of T+1]
    D1 --> D3[3d close<br/>knowable at end of T+3]
    D3 --> D5[5d close<br/>knowable at end of T+5]

    EOD[EOD job runs daily] -.->|fills available horizons| SAME
    EOD -.->|for past signals| D1
    EOD -.->|whose data is now ready| D3
    EOD -.-> D5
```

For each signal:
- After today's EOD: fill `outcome_eod_pct`
- After next-day EOD: fill `outcome_1d_pct`
- After 3 trading days: fill `outcome_3d_pct`
- After 5 trading days: fill `outcome_5d_pct`
- When any horizon is filled: compute `outcome_best_horizon`

## Component Additions

| Component | Path |
|---|---|
| Universe Agent | `agents/universe/` |
| Backtester | `lib/backtester.py` |
| Multi-horizon outcomes | `lib/multi_horizon_outcomes.py` |
| Backtest CLI | `backtest.py` |
| Baseline data | `data/nifty_100_baseline.yaml` |
| Config | `config/universe_config.yaml` |

## Schedule (Unchanged)

- Main signals: every 15 min during market hours via cron-job.org
- EOD review: once at 16:00 IST via cron-job.org
- Universe build: triggered as part of every main run; logged to Universe tab only at first run of the day (~9:15-9:30 IST)
