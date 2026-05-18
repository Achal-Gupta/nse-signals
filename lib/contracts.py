"""
Shared data contracts. Every agent speaks in these shapes.
See docs/design/v0.2.0/contracts.md for the design rationale.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Signal:
    """A single agent's analysis output."""
    agent: str            # e.g. "rsi", "macd", "bollinger", "vwap", "market_sentiment", "stock_sentiment", "sentiment_fusion"
    symbol: Optional[str] # None for market-level signals
    action: str           # "BUY" | "SELL" | "HOLD"
    confidence: float     # 0.0 to 1.0
    reason: str
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Regime:
    """Market regime context attached to every run."""
    vix_level: Optional[float]
    vix_pct_change: Optional[float]
    nifty_5d_pct: Optional[float]
    nifty_pct: Optional[float]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verdict:
    """The aggregator's final per-stock conclusion."""
    symbol: str
    action: str
    confidence: float
    price_at_signal: float
    per_agent_signals: dict          # {agent_name: Signal}
    market_signal: Signal
    fused_sentiment_signal: Signal
    regime: Regime
    timestamp_ist: str
    aggregator_score: float

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "price_at_signal": self.price_at_signal,
            "per_agent_signals": {k: v.to_dict() for k, v in self.per_agent_signals.items()},
            "market_signal": self.market_signal.to_dict(),
            "fused_sentiment_signal": self.fused_sentiment_signal.to_dict(),
            "regime": self.regime.to_dict(),
            "timestamp_ist": self.timestamp_ist,
            "aggregator_score": self.aggregator_score,
        }


ACTION_BUY = "BUY"
ACTION_SELL = "SELL"
ACTION_HOLD = "HOLD"
VALID_ACTIONS = {ACTION_BUY, ACTION_SELL, ACTION_HOLD}
