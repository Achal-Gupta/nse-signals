"""
Sentiment Fusion — combines market + stock sentiment.
Rule-based, no LLM call. See agents/sentiment_fusion/skill.md.
"""
import logging

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)

MARKET_WEIGHT = 0.4
STOCK_WEIGHT = 0.6
ACTION_THRESHOLD = 0.25
STRONG_MARKET_THRESHOLD = 0.7


def _signal_to_score(sig: Signal) -> float:
    """Map a Signal to a signed score in [-1, +1]."""
    if sig.action == ACTION_BUY:
        return +sig.confidence
    if sig.action == ACTION_SELL:
        return -sig.confidence
    return 0.0


def fuse(market_signal: Signal, stock_signal: Signal) -> Signal:
    """Combine market-wide and stock-specific sentiment into a fused Signal."""
    market_score = _signal_to_score(market_signal)
    stock_score = _signal_to_score(stock_signal)

    fused_score = MARKET_WEIGHT * market_score + STOCK_WEIGHT * stock_score

    # Determine raw action from fused score
    if fused_score > ACTION_THRESHOLD:
        action = ACTION_BUY
    elif fused_score < -ACTION_THRESHOLD:
        action = ACTION_SELL
    else:
        action = ACTION_HOLD

    # Apply market override rules
    override_applied = False
    if (market_signal.action == ACTION_SELL
            and market_signal.confidence > STRONG_MARKET_THRESHOLD
            and action == ACTION_BUY):
        action = ACTION_HOLD
        override_applied = True
    elif (market_signal.action == ACTION_BUY
          and market_signal.confidence > STRONG_MARKET_THRESHOLD
          and action == ACTION_SELL):
        action = ACTION_HOLD
        override_applied = True

    confidence = round(min(abs(fused_score), 1.0), 3) if action != ACTION_HOLD else 0.4

    reason_parts = [
        f"market {market_signal.action.lower()}",
        f"stock {stock_signal.action.lower()}",
    ]
    if override_applied:
        reason_parts.append("market override applied")
    reason = " + ".join(reason_parts)

    return Signal(
        agent="sentiment_fusion",
        symbol=stock_signal.symbol,
        action=action,
        confidence=confidence,
        reason=reason,
        metrics={
            "market_weight": MARKET_WEIGHT,
            "stock_weight": STOCK_WEIGHT,
            "market_score": round(market_score, 3),
            "stock_score": round(stock_score, 3),
            "fused_score": round(fused_score, 3),
            "market_override": override_applied,
            "stock_action": stock_signal.action,
            "stock_reason": stock_signal.reason,
        },
    )
