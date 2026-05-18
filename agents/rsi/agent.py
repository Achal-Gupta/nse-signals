"""
RSI Agent — Relative Strength Index signal.
See agents/rsi/skill.md for the rule definition.
"""
import logging
from typing import Optional

import pandas as pd

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)

AGENT_NAME = "rsi"
RSI_PERIOD = 14
OVERSOLD = 30.0
OVERBOUGHT = 70.0


def _compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Wilder's RSI using EMA smoothing."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _rsi_to_confidence(rsi: float) -> tuple[str, float]:
    if rsi < OVERSOLD:
        conf = min(1.0, 0.5 + (OVERSOLD - rsi) / 40.0)
        return ACTION_BUY, round(conf, 3)
    if rsi > OVERBOUGHT:
        conf = min(1.0, 0.5 + (rsi - OVERBOUGHT) / 40.0)
        return ACTION_SELL, round(conf, 3)
    return ACTION_HOLD, 0.5


def analyze(symbol: str, df: Optional[pd.DataFrame]) -> Signal:
    if df is None or df.empty or len(df) < RSI_PERIOD + 1:
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason="Insufficient data", metrics={})
    try:
        rsi_series = _compute_rsi(df["Close"], RSI_PERIOD).dropna()
        if rsi_series.empty:
            return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                          confidence=0.0, reason="RSI returned empty", metrics={})
        rsi = float(rsi_series.iloc[-1])
        action, confidence = _rsi_to_confidence(rsi)
        if action == ACTION_BUY:
            reason = f"RSI = {rsi:.1f} (oversold)"
        elif action == ACTION_SELL:
            reason = f"RSI = {rsi:.1f} (overbought)"
        else:
            reason = f"RSI = {rsi:.1f} (neutral)"
        return Signal(agent=AGENT_NAME, symbol=symbol, action=action,
                      confidence=confidence, reason=reason,
                      metrics={"rsi": round(rsi, 2)})
    except Exception as e:
        logger.error(f"RSI failed for {symbol}: {e}", exc_info=True)
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason=f"Error: {str(e)[:80]}", metrics={})
