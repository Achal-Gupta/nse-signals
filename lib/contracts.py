"""
Shared data contracts. Every agent speaks in these shapes.
See docs/design/v0.1.0/contracts.md for the design rationale.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Signal:
    """A single agent's analysis output."""
    agent: str                        # "technical" | "market_sentiment" | "stock_sentiment" | "sentiment_fusion"
    symbol: Optional[str]             # e.g. "RELIANCE.NS"; None for market-level signals
    action: str                       # "BUY" | "SELL" | "HOLD"
    confidence: float                 # 0.0 to 1.0
    reason: str                       # human-readable explanation
    metrics: dict = field(default_factory=dict)  # raw numbers

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verdict:
    """The orchestrator's final per-stock conclusion."""
    symbol: str
    action: str                       # "BUY" | "SELL" | "HOLD"
    confidence: float
    technical_signal: Signal
    sentiment_signal: Signal          # fused sentiment
    market_signal: Signal             # macro signal (shared in a run)
    timestamp_ist: str                # ISO format

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "technical_signal": self.technical_signal.to_dict(),
            "sentiment_signal": self.sentiment_signal.to_dict(),
            "market_signal": self.market_signal.to_dict(),
            "timestamp_ist": self.timestamp_ist,
        }


# Constants used across modules
ACTION_BUY = "BUY"
ACTION_SELL = "SELL"
ACTION_HOLD = "HOLD"

VALID_ACTIONS = {ACTION_BUY, ACTION_SELL, ACTION_HOLD}
