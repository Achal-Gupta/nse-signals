# Design Documentation

Each version has its own folder with three files:

- **`architecture.md`** — System diagram + what each piece does
- **`contracts.md`** — Data shapes flowing between components
- **`decisions.md`** — Key choices, rationale, and forward roadmap

## Versions

- [v0.1.0](v0.1.0/) — MVP with 2 agents (Technical RSI + 2-tier Sentiment)
- [v0.2.0](v0.2.0/) — 4 indicators (RSI/MACD/BB/VWAP), LangGraph, score aggregator, paper trading, regime tags
- [v0.3.0](v0.3.0/) — Universe Agent (40 stocks), multi-horizon outcomes, vectorbt backtester
