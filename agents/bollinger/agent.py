"""
Bollinger Bands Agent.
See agents/bollinger/skill.md for rule definition.
"""
import logging
from typing import Optional

import pandas as pd

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)

AGENT_NAME = "bollinger"
PERIOD = 20
STD_MULT = 2.0
BUY_THRESHOLD = 0.05
SELL_THRESHOLD = 0.95


def _compute_bb(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (lower, middle, upper)."""
    middle = close.rolling(window=PERIOD).mean()
    std = close.rolling(window=PERIOD).std()
    upper = middle + STD_MULT * std
    lower = middle - STD_MULT * std
    return lower, middle, upper


def analyze(symbol: str, df: Optional[pd.DataFrame]) -> Signal:
    if df is None or df.empty or len(df) < PERIOD + 2:
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason="Insufficient data", metrics={})
    try:
        close = df["Close"]
        lower, middle, upper = _compute_bb(close)

        last_price = float(close.iloc[-1])
        last_lower = float(lower.iloc[-1])
        last_middle = float(middle.iloc[-1])
        last_upper = float(upper.iloc[-1])

        if last_upper == last_lower:
            percent_b = 0.5
        else:
            percent_b = (last_price - last_lower) / (last_upper - last_lower)

        if percent_b < BUY_THRESHOLD:
            action = ACTION_BUY
            # The more negative %B, the higher confidence
            confidence = min(1.0, 0.5 + abs(percent_b - BUY_THRESHOLD) * 2)
            reason = f"BB %B={percent_b:.2f} (below lower band)"
        elif percent_b > SELL_THRESHOLD:
            action = ACTION_SELL
            confidence = min(1.0, 0.5 + abs(percent_b - SELL_THRESHOLD) * 2)
            reason = f"BB %B={percent_b:.2f} (above upper band)"
        else:
            action = ACTION_HOLD
            confidence = 0.5
            reason = f"BB %B={percent_b:.2f} (within bands)"

        return Signal(
            agent=AGENT_NAME, symbol=symbol, action=action,
            confidence=round(confidence, 3), reason=reason,
            metrics={
                "bb_lower": round(last_lower, 2),
                "bb_middle": round(last_middle, 2),
                "bb_upper": round(last_upper, 2),
                "bb_percent_b": round(percent_b, 3),
            },
        )
    except Exception as e:
        logger.error(f"BB failed for {symbol}: {e}", exc_info=True)
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason=f"Error: {str(e)[:80]}", metrics={})
