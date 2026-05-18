"""
Score-based weighted aggregator.

Replaces the v0.1.0 "both must agree or HOLD" rule with a continuous
weighted-score combination. Each signal contributes ±confidence,
weighted by its agent.

See agents/sentiment_fusion/skill.md for parallel pattern at sentiment level.
"""
import logging
from typing import Dict

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)


# Starting weights for v0.2.0. Reviewer Agent (v0.5.0) will tune these from data.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "rsi":               0.15,
    "macd":              0.25,
    "bollinger":         0.15,
    "vwap":              0.15,
    "sentiment_fusion":  0.30,
}

ACTION_THRESHOLD = 0.20  # |score| must exceed this for a directional verdict


def _signal_to_score(sig: Signal) -> float:
    """Map a Signal to [-1, +1] score. BUY=+conf, SELL=-conf, HOLD=0."""
    if sig.action == ACTION_BUY:
        return +sig.confidence
    if sig.action == ACTION_SELL:
        return -sig.confidence
    return 0.0


def aggregate(
    per_agent_signals: Dict[str, Signal],
    weights: Dict[str, float] = None,
) -> tuple[str, float, float]:
    """
    Combine multiple agent Signals into a single verdict using weighted scores.

    Args:
        per_agent_signals: {agent_name: Signal}. Must include sentiment_fusion.
        weights: optional override; defaults to DEFAULT_WEIGHTS.

    Returns:
        (action, confidence, raw_score)
    """
    weights = weights or DEFAULT_WEIGHTS

    # Compute weighted score across whatever agents are present.
    # Renormalize weights to only sum over present agents to avoid bias when
    # an agent fails (e.g., RSI errors and is omitted).
    present = {a: w for a, w in weights.items() if a in per_agent_signals}
    if not present:
        return ACTION_HOLD, 0.0, 0.0

    weight_sum = sum(present.values())
    if weight_sum <= 0:
        return ACTION_HOLD, 0.0, 0.0

    score = 0.0
    for agent_name, weight in present.items():
        normalized_weight = weight / weight_sum
        score += normalized_weight * _signal_to_score(per_agent_signals[agent_name])

    if score > ACTION_THRESHOLD:
        return ACTION_BUY, round(min(abs(score), 1.0), 3), round(score, 3)
    if score < -ACTION_THRESHOLD:
        return ACTION_SELL, round(min(abs(score), 1.0), 3), round(score, 3)
    return ACTION_HOLD, round(abs(score), 3), round(score, 3)
