"""
Shared data contracts. Every agent speaks in these shapes.
See docs/design/v0.2.1/contracts.md for the design rationale.

v0.2.1 changes:
- Added trade_idea_id to Verdict for signal stickiness dedup
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Signal:
    """A single agent's analysis output."""
    agent: str
    symbol: Optional[str]
    action: str
    confidence: float
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
    per_agent_signals: dict
    market_signal: Signal
    fused_sentiment_signal: Signal
    regime: Regime
    timestamp_ist: str
    aggregator_score: float
    trade_idea_id: str = ""   # v0.2.1: groups stickiness-related signals (same stock+action within 60min)

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
            "trade_idea_id": self.trade_idea_id,
        }


ACTION_BUY = "BUY"
ACTION_SELL = "SELL"
ACTION_HOLD = "HOLD"
VALID_ACTIONS = {ACTION_BUY, ACTION_SELL, ACTION_HOLD}
