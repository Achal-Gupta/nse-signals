"""
Technical Agent — RSI-based signal.
See agents/technical/skill.md for the rule definition.
"""
import logging
from typing import Optional

import pandas as pd
import pandas_ta as ta

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)

RSI_PERIOD = 14
OVERSOLD = 30.0
OVERBOUGHT = 70.0


def _rsi_to_confidence(rsi: float) -> tuple[str, float]:
    """Map an RSI value to (action, confidence)."""
    if rsi < OVERSOLD:
        # 30 -> 0.5, 10 -> 1.0, linear in between, capped
        conf = min(1.0, 0.5 + (OVERSOLD - rsi) / 40.0)
        return ACTION_BUY, round(conf, 3)
    if rsi > OVERBOUGHT:
        conf = min(1.0, 0.5 + (rsi - OVERBOUGHT) / 40.0)
        return ACTION_SELL, round(conf, 3)
    return ACTION_HOLD, 0.5


def analyze(symbol: str, df: Optional[pd.DataFrame]) -> Signal:
    """
    Run RSI on the given OHLCV DataFrame and return a Signal.

    On any error (missing data, computation failure), returns a HOLD signal
    with a low confidence and an error reason.
    """
    if df is None or df.empty or len(df) < RSI_PERIOD + 1:
        return Signal(
            agent="technical",
            symbol=symbol,
            action=ACTION_HOLD,
            confidence=0.0,
            reason="Insufficient data",
            metrics={},
        )

    try:
        close = df["Close"]
        rsi_series = ta.rsi(close, length=RSI_PERIOD)
        if rsi_series is None or rsi_series.dropna().empty:
            return Signal(
                agent="technical",
                symbol=symbol,
                action=ACTION_HOLD,
                confidence=0.0,
                reason="RSI computation returned empty",
                metrics={},
            )
        rsi = float(rsi_series.dropna().iloc[-1])
        action, confidence = _rsi_to_confidence(rsi)

        if action == ACTION_BUY:
            reason = f"RSI = {rsi:.1f} (oversold)"
        elif action == ACTION_SELL:
            reason = f"RSI = {rsi:.1f} (overbought)"
        else:
            reason = f"RSI = {rsi:.1f} (neutral)"

        return Signal(
            agent="technical",
            symbol=symbol,
            action=action,
            confidence=confidence,
            reason=reason,
            metrics={"rsi": round(rsi, 2)},
        )
    except Exception as e:
        logger.error(f"Technical analysis failed for {symbol}: {e}", exc_info=True)
        return Signal(
            agent="technical",
            symbol=symbol,
            action=ACTION_HOLD,
            confidence=0.0,
            reason=f"Error: {str(e)[:80]}",
            metrics={},
        )
