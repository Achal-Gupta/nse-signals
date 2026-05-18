"""
MACD Agent — Moving Average Convergence Divergence.
See agents/macd/skill.md for rule definition.
"""
import logging
from typing import Optional

import pandas as pd

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)

AGENT_NAME = "macd"
FAST = 12
SLOW = 26
SIGNAL = 9


def _compute_macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = close.ewm(span=FAST, adjust=False).mean()
    ema_slow = close.ewm(span=SLOW, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=SIGNAL, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def _hist_to_confidence(hist: float, price: float) -> float:
    """
    Map histogram value to confidence in [0.5, 1.0].
    Normalize by price so scaling is symbol-independent.
    """
    if price <= 0:
        return 0.5
    normalized = abs(hist) / price * 1000  # scale factor
    return min(1.0, 0.5 + normalized)


def analyze(symbol: str, df: Optional[pd.DataFrame]) -> Signal:
    min_needed = SLOW + SIGNAL + 5
    if df is None or df.empty or len(df) < min_needed:
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason="Insufficient data", metrics={})
    try:
        close = df["Close"]
        macd_line, signal_line, hist = _compute_macd(close)
        macd_line = macd_line.dropna()
        signal_line = signal_line.dropna()
        hist = hist.dropna()
        if len(hist) < 2:
            return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                          confidence=0.0, reason="MACD returned empty", metrics={})

        last_hist = float(hist.iloc[-1])
        prev_hist = float(hist.iloc[-2])
        last_macd = float(macd_line.iloc[-1])
        last_price = float(close.iloc[-1])

        bullish_cross = prev_hist <= 0 and last_hist > 0 and last_macd > 0
        bearish_cross = prev_hist >= 0 and last_hist < 0 and last_macd < 0

        if bullish_cross:
            action = ACTION_BUY
            confidence = _hist_to_confidence(last_hist, last_price)
            reason = f"MACD bullish crossover (hist={last_hist:.3f})"
        elif bearish_cross:
            action = ACTION_SELL
            confidence = _hist_to_confidence(last_hist, last_price)
            reason = f"MACD bearish crossover (hist={last_hist:.3f})"
        else:
            action = ACTION_HOLD
            confidence = 0.5
            reason = f"MACD neutral (hist={last_hist:.3f}, line={last_macd:.3f})"

        return Signal(
            agent=AGENT_NAME, symbol=symbol, action=action,
            confidence=round(confidence, 3), reason=reason,
            metrics={
                "macd_line": round(last_macd, 4),
                "macd_signal": round(float(signal_line.iloc[-1]), 4),
                "macd_hist": round(last_hist, 4),
            },
        )
    except Exception as e:
        logger.error(f"MACD failed for {symbol}: {e}", exc_info=True)
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason=f"Error: {str(e)[:80]}", metrics={})
