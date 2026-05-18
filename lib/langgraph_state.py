"""
LangGraph state schema for the orchestrator pipeline.

The graph is sequential in v0.2.0 with the structure:

    secrets_check -> regime -> market_sentiment -> per_stock_loop -> notify_and_log

Per-stock processing is currently a single node that loops internally over
the watchlist. v0.3.0 will introduce true parallel fanout via Send API.
"""
from typing import TypedDict, Optional
from lib.contracts import Signal, Verdict, Regime


class TradingState(TypedDict, total=False):
    """Shared state passed through every LangGraph node."""
    timestamp_ist: str
    watchlist: list[dict]            # [{"symbol": ..., "name": ...}, ...]
    regime: Regime
    market_signal: Signal
    verdicts: list[Verdict]
    errors: list[str]
    skipped: Optional[bool]          # True if outside market hours (graph short-circuits)
