"""
LangGraph state schema for the orchestrator pipeline (v0.3.0).

Graph topology:

    secrets_check -> market_hours -> universe -> regime -> market_sentiment
      -> per_stock_loop -> notify_and_log

The Universe Agent fetches today's watchlist if not already cached.
"""
from typing import TypedDict, Optional
from lib.contracts import Signal, Verdict, Regime, Universe


class TradingState(TypedDict, total=False):
    """Shared state passed through every LangGraph node."""
    timestamp_ist: str
    universe: Universe
    watchlist: list[dict]
    regime: Regime
    market_signal: Signal
    verdicts: list[Verdict]
    errors: list[str]
    skipped: Optional[bool]
