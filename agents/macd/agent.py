"""
MACD Agent — Moving Average Convergence Divergence.

v0.2.1 change: switched from strict crossover detection to sign-based logic.
Crossover detection missed signals when the histogram transitioned between
15-min sampling intervals (we'd see +6.0 at 10:55 and -2.3 at 12:32 — the
actual crossover happened between samples and was invisible to us).

The new logic uses current state of MACD line and histogram:
  - hist > 0 AND macd > 0  → BUY (bullish positioning)
  - hist < 0 AND macd < 0  → SELL (bearish positioning)
  - mixed signs            → HOLD
This is standard MACD signal logic (current state, not transition).

See agents/macd/skill.md for the rule definition.
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
        if len(hist) < 1 or len(macd_line) < 1:
            return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                          confidence=0.0, reason="MACD returned empty", metrics={})

        last_hist = float(hist.iloc[-1])
        last_macd = float(macd_line.iloc[-1])
        last_signal = float(signal_line.iloc[-1])
        last_price = float(close.iloc[-1])

        # Sign-based signal logic (v0.2.1 fix)
        # Both histogram and MACD line must agree on direction.
        # Histogram > 0 means MACD is above its signal line (momentum building up).
        # MACD > 0 means short EMA is above long EMA (price trend is up).
        if last_hist > 0 and last_macd > 0:
            action = ACTION_BUY
            confidence = _hist_to_confidence(last_hist, last_price)
            reason = f"MACD bullish (hist=+{last_hist:.3f}, line=+{last_macd:.3f})"
        elif last_hist < 0 and last_macd < 0:
            action = ACTION_SELL
            confidence = _hist_to_confidence(last_hist, last_price)
            reason = f"MACD bearish (hist={last_hist:.3f}, line={last_macd:.3f})"
        else:
            # Mixed signals — hist and macd disagree on direction
            action = ACTION_HOLD
            confidence = 0.5
            reason = f"MACD mixed (hist={last_hist:.3f}, line={last_macd:.3f})"

        return Signal(
            agent=AGENT_NAME, symbol=symbol, action=action,
            confidence=round(confidence, 3), reason=reason,
            metrics={
                "macd_line": round(last_macd, 4),
                "macd_signal": round(last_signal, 4),
                "macd_hist": round(last_hist, 4),
            },
        )
    except Exception as e:
        logger.error(f"MACD failed for {symbol}: {e}", exc_info=True)
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason=f"Error: {str(e)[:80]}", metrics={})
