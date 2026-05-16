"""
Market Sentiment connectors — pulls market-wide snapshots.
"""
import logging
from typing import Optional

from agents.data_fetcher.fetcher import get_index_snapshot

logger = logging.getLogger(__name__)

# Symbols (yfinance tickers)
NIFTY_50 = "^NSEI"
INDIA_VIX = "^INDIAVIX"
DOW_JONES = "^DJI"
CRUDE_WTI = "CL=F"
USD_INR = "INR=X"


def get_market_snapshot() -> dict:
    """
    Pull a snapshot of market context indicators.
    Always returns a dict; missing values become None (handled downstream).
    """
    return {
        "nifty": get_index_snapshot(NIFTY_50),
        "vix": get_index_snapshot(INDIA_VIX),
        "dow": get_index_snapshot(DOW_JONES),
        "crude": get_index_snapshot(CRUDE_WTI),
        "inr": get_index_snapshot(USD_INR),
    }


def format_snapshot_for_prompt(snap: dict) -> str:
    """Render the snapshot as a clean text block for the LLM."""
    def line(label: str, key: str, suffix: str = "") -> str:
        d = snap.get(key)
        if d is None:
            return f"- {label}: data unavailable"
        return f"- {label}: {d['close']}{suffix} ({d['pct_change']:+.2f}% change)"

    return "\n".join([
        line("Nifty 50", "nifty"),
        line("India VIX", "vix"),
        line("Dow Jones", "dow"),
        line("Crude (WTI)", "crude"),
        line("USD/INR", "inr"),
    ])
