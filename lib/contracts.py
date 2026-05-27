"""
Shared data contracts. Every agent speaks in these shapes.
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
class Universe:
    """Today's stock universe selected by the Universe Agent."""
    timestamp_ist: str
    stocks: list[dict]
    pool1_size: int
    pool2_size: int
    overlaps: int
    errors: list[str] = field(default_factory=list)

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
    trade_idea_id: str = ""
    universe_source: str = ""

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
            "universe_source": self.universe_source,
        }


ACTION_BUY = "BUY"
ACTION_SELL = "SELL"
ACTION_HOLD = "HOLD"
VALID_ACTIONS = {ACTION_BUY, ACTION_SELL, ACTION_HOLD}

OUTCOME_HORIZONS = ["eod", "1d", "3d", "5d"]
HORIZON_DAYS = {"eod": 0, "1d": 1, "3d": 3, "5d": 5}