# v0.2.0 — Data Contracts

All agents speak via these shapes (defined in `lib/contracts.py`).

## `Signal`

```python
@dataclass
class Signal:
    agent: str            # "rsi" | "macd" | "bollinger" | "vwap"
                          # | "market_sentiment" | "stock_sentiment" | "sentiment_fusion"
    symbol: Optional[str] # None for market-level signals
    action: str           # "BUY" | "SELL" | "HOLD"
    confidence: float     # 0.0 to 1.0
    reason: str
    metrics: dict         # agent-specific raw numbers
```

## `Regime`

New in v0.2.0. Captures market context attached to every run.

```python
@dataclass
class Regime:
    vix_level: float | None        # e.g. 19.63
    vix_pct_change: float | None   # e.g. +4.47
    nifty_5d_pct: float | None     # 5-day Nifty 50 percent change
    nifty_pct: float | None        # today's Nifty 50 percent change
```

## `Verdict`

```python
@dataclass
class Verdict:
    symbol: str
    action: str
    confidence: float
    price_at_signal: float                # used by paper trader
    per_agent_signals: dict[str, Signal]  # {"rsi": Signal, "macd": Signal, ...}
    market_signal: Signal
    fused_sentiment_signal: Signal
    regime: Regime
    timestamp_ist: str
    aggregator_score: float               # raw weighted score, useful for debugging
```

## Per-Agent Contracts

### Technical Agents (RSI, MACD, Bollinger, VWAP)

Same shape:

```python
def analyze(symbol: str, df: pd.DataFrame) -> Signal
```

Metric dict varies per agent:
- RSI: `{"rsi": float}`
- MACD: `{"macd_line", "macd_signal", "macd_hist"}`
- BB: `{"bb_lower", "bb_middle", "bb_upper", "bb_percent_b"}`
- VWAP: `{"vwap", "price", "vwap_distance_pct"}`

### Sentiment Agents

Unchanged from v0.1.0.

## Aggregator Contract

```python
def aggregate(
    per_agent_signals: dict[str, Signal],
    weights: dict[str, float] = None,
) -> tuple[str, float, float]:  # (action, confidence, raw_score)
```

### Default Weights

```python
DEFAULT_WEIGHTS = {
    "rsi":               0.15,
    "macd":              0.25,
    "bollinger":         0.15,
    "vwap":              0.15,
    "sentiment_fusion":  0.30,
}
ACTION_THRESHOLD = 0.20
```

Each signal → score in [-1, +1]: BUY = +confidence, SELL = -confidence, HOLD = 0.
Weighted sum compared to ±0.20 threshold for directional verdict.

If an agent is missing (errored), its weight is dropped and remaining weights
are renormalized to sum to 1.

## Google Sheet Schema (27 columns)

| # | Column | Type | Source |
|---|---|---|---|
| 1 | timestamp_ist | string | orchestrator |
| 2 | symbol | string | watchlist |
| 3 | final_action | string | aggregator |
| 4 | final_confidence | float | aggregator |
| 5 | price_at_signal | float | data fetcher |
| 6 | aggregator_score | float | aggregator |
| 7 | rsi_action | string | rsi agent |
| 8 | rsi_value | float | rsi metrics |
| 9 | macd_action | string | macd agent |
| 10 | macd_hist | float | macd metrics |
| 11 | bb_action | string | bb agent |
| 12 | bb_percent_b | float | bb metrics |
| 13 | vwap_action | string | vwap agent |
| 14 | vwap_distance_pct | float | vwap metrics |
| 15 | stock_sent_action | string | stock sentiment |
| 16 | stock_sent_reason | string | stock sentiment |
| 17 | market_action | string | market sentiment |
| 18 | market_reason | string | market sentiment |
| 19 | fused_sent_action | string | sentiment fusion |
| 20 | fused_sent_confidence | float | sentiment fusion |
| 21 | vix_level | float | regime |
| 22 | vix_pct_change | float | regime |
| 23 | nifty_pct | float | regime |
| 24 | nifty_5d_pct | float | regime |
| 25 | outcome_pct | float | paper trader (EOD) |
| 26 | outcome_status | string | paper trader: "WIN"/"LOSS" |
| 27 | errors | string | global per-run errors |

## Paper Trader Outcome Logic

For each BUY/SELL row from `T-1` trading day, EOD job at `T` 16:00:
- Fetch close price on day `T`
- **BUY:** `outcome_pct = (close_T - price_at_signal) / price_at_signal × 100`
- **SELL:** `outcome_pct = (price_at_signal - close_T) / price_at_signal × 100`
- `outcome_status = "WIN" if outcome_pct >= 0 else "LOSS"`

### Honest Limitations
- Ignores intraday stop-loss / target — actual outcomes would differ
- Ignores brokerage and slippage
- Uses one snapshot price; multi-horizon (1d/3d/5d) is a v0.3.0 enhancement
- These are *paper outcomes*, useful for relative agent ranking, not real P&L
