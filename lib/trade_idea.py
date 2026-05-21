"""
Trade idea grouper (v0.2.1).

Same stock + same action within a configurable time window = same "trade idea."
This addresses signal stickiness: when an aggregator score stays above the
threshold for several 15-min cycles, we don't want to count that as multiple
independent signals.

The trade_idea_id is deterministic — generated from (symbol, action, idea_start_date_hour).
This way subsequent signals within the window produce the same id without
needing to read sheet history.

Idea boundary logic (v0.2.1 simplification):
  - Group by 60-minute clock buckets (00, 01, ..., 23)
  - Within a bucket, same (symbol, action) → same id
  - Example: TCS BUY at 14:30 → id includes "14"
             TCS BUY at 14:45 → same id "14"
             TCS BUY at 15:00 → NEW id "15" (new bucket)
             TCS BUY at 15:30 → same id "15"

This isn't a perfect 60-min sliding window — it uses fixed hour buckets, so
a TCS BUY at 14:55 and 15:00 get different ids despite being 5 min apart.
Tradeoff is simplicity (no state needed) vs precision. For v0.2.1 paper trade
analysis this is sufficient; we can refine to sliding window in v0.3.0+.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def compute_trade_idea_id(symbol: str, action: str, timestamp_ist: str) -> str:
    """
    Generate a deterministic trade_idea_id from (symbol, action, timestamp_hour).

    Args:
        symbol: e.g. "RELIANCE.NS"
        action: "BUY" | "SELL" | "HOLD"
        timestamp_ist: ISO format like "2026-05-19 14:30:46"

    Returns:
        String like "RELIANCE.NS_BUY_2026-05-19_14" or empty if HOLD.

    HOLDs don't get trade_idea_id since they're not actionable.
    """
    if action == "HOLD":
        return ""

    try:
        dt = datetime.strptime(timestamp_ist, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.warning(f"Could not parse timestamp for trade_idea_id: {timestamp_ist}")
        return ""

    hour_bucket = dt.strftime("%Y-%m-%d_%H")
    return f"{symbol}_{action}_{hour_bucket}"
