# v0.1.0 — Data Contracts

All agents speak in the same dialect. This file defines that dialect.

## The `Signal` dataclass

Every agent returns this. Defined in `lib/contracts.py`.

```python
@dataclass
class Signal:
    agent: str              # "technical" | "market_sentiment" | "stock_sentiment" | "sentiment_fusion"
    symbol: str | None      # e.g. "RELIANCE.NS"; None for market-level signals
    action: str             # "BUY" | "SELL" | "HOLD"
    confidence: float       # 0.0 to 1.0
    reason: str             # short human-readable explanation
    metrics: dict           # agent-specific raw numbers (e.g. {"rsi": 28.4})
```

## The `Verdict` dataclass

The Orchestrator produces one of these per stock after aggregating signals.

```python
@dataclass
class Verdict:
    symbol: str
    action: str             # "BUY" | "SELL" | "HOLD"
    confidence: float       # 0.0 to 1.0
    technical_signal: Signal
    sentiment_signal: Signal     # the fused sentiment
    market_signal: Signal        # the macro signal (shared across all stocks in this run)
    timestamp_ist: str           # ISO format, IST
```

## Per-Agent Contract

### Technical Agent (`agents/technical/agent.py`)

```python
def analyze(symbol: str, df: pd.DataFrame) -> Signal:
    """
    Input:  symbol = "RELIANCE.NS"
            df = OHLCV DataFrame, at least 30 rows, columns: [Open, High, Low, Close, Volume]
    Output: Signal(agent="technical", symbol=symbol, action=..., confidence=..., 
                   reason="RSI = 28.4 (oversold)", metrics={"rsi": 28.4})
    Rule:   RSI < 30 → BUY (confidence scales with how far below 30)
            RSI > 70 → SELL (confidence scales with how far above 70)
            else    → HOLD (confidence 0.5)
    """
```

### Market Sentiment Agent (`agents/market_sentiment/agent.py`)

```python
def analyze() -> Signal:
    """
    Input:  none (uses connectors to fetch Nifty, VIX, Dow, crude, USD/INR)
    Output: Signal(agent="market_sentiment", symbol=None, action="BUY"|"SELL"|"HOLD",
                   confidence=0.0-1.0, reason="Nifty +0.2%, VIX 13.4, calm market",
                   metrics={"nifty_pct": 0.2, "vix": 13.4, "dow_pct": 0.1, ...})
    Logic:  Claude Haiku analyzes the inputs and classifies market mood as
            bullish (BUY-favorable), bearish (SELL-favorable), or neutral (HOLD).
    """
```

### Stock Sentiment Agent (`agents/stock_sentiment/agent.py`)

```python
def analyze(symbol: str, company_name: str) -> Signal:
    """
    Input:  symbol = "RELIANCE.NS", company_name = "Reliance Industries"
    Output: Signal(agent="stock_sentiment", symbol=symbol, action="BUY"|"SELL"|"HOLD",
                   confidence=0.0-1.0, reason="Q2 earnings beat estimates",
                   metrics={"headline_count": 5, "positive": 3, "negative": 1, "neutral": 1})
    Logic:  Fetches last 5 Google News headlines via RSS, sends them to Claude Haiku
            for sentiment classification.
    """
```

### Sentiment Fusion (`agents/sentiment_fusion/agent.py`)

```python
def fuse(market_signal: Signal, stock_signal: Signal) -> Signal:
    """
    Input:  market_signal (from Market Sentiment Agent)
            stock_signal (from Stock Sentiment Agent)
    Output: Signal(agent="sentiment_fusion", symbol=stock_signal.symbol, action=..., 
                   confidence=..., reason="market neutral + stock +ve",
                   metrics={"market_weight": 0.4, "stock_weight": 0.6,
                            "fused_score": 0.65, "market_override": false})
    Logic:  - Weighted score: 40% market + 60% stock
            - Override: if market is strongly bearish (confidence > 0.7), 
              downgrade any BUY to HOLD
    """
```

### Final Aggregation (in `orchestrator.py`)

```python
def aggregate(technical: Signal, sentiment: Signal, market: Signal) -> Verdict:
    """
    Rule for v0.1.0:
    - If technical and sentiment agree on action → use that action,
      confidence = (technical.confidence + sentiment.confidence) / 2
    - If they disagree → action = "HOLD", confidence = 0.3
    - market is passed through for logging
    """
```

## Google Sheet Schema

Sheet name: anything (set via `GOOGLE_SHEET_ID`). First row is headers.

| Column | Type | Example |
|---|---|---|
| `timestamp_ist` | string | `2026-05-16 11:45:00` |
| `symbol` | string | `RELIANCE.NS` |
| `final_action` | string | `BUY` |
| `final_confidence` | float | `0.74` |
| `technical_action` | string | `BUY` |
| `technical_reason` | string | `RSI = 28.4 (oversold)` |
| `rsi` | float | `28.4` |
| `stock_sent_action` | string | `BUY` |
| `stock_sent_reason` | string | `Q2 beat estimates` |
| `market_action` | string | `HOLD` |
| `market_reason` | string | `Nifty flat, VIX calm` |
| `fused_sent_action` | string | `BUY` |
| `fused_sent_confidence` | float | `0.65` |
| `errors` | string | empty, or error message |

## Email Format

```
Subject: 📊 NSE Signals · [N BUY] · [N SELL] · [HH:MM IST]

Market: 🟡 [mood] — [reason]

🟢 RELIANCE — BUY (74%)
   • RSI: 28 (oversold)
   • Stock news: Positive
   • Reason: Both signals aligned

🔴 HDFCBANK — SELL (62%)
   ...

⚪ HOLDS (3): TCS, INFY, ICICIBANK
```
