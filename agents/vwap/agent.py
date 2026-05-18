"""
VWAP Agent — rolling Volume Weighted Average Price.
See agents/vwap/skill.md for rule definition.
"""
import logging
from typing import Optional

import pandas as pd

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)

AGENT_NAME = "vwap"
WINDOW = 20
BUY_THRESHOLD_PCT = -0.5
SELL_THRESHOLD_PCT = 0.5


def _compute_rolling_vwap(df: pd.DataFrame, window: int = WINDOW) -> pd.Series:
    """Rolling VWAP using typical price (H+L+C)/3 and Volume."""
    typical = (df["High"] + df["Low"] + df["Close"]) / 3.0
    tp_vol = typical * df["Volume"]
    return tp_vol.rolling(window=window).sum() / df["Volume"].rolling(window=window).sum()


def analyze(symbol: str, df: Optional[pd.DataFrame]) -> Signal:
    required_cols = {"High", "Low", "Close", "Volume"}
    if (df is None or df.empty or len(df) < WINDOW + 2
            or not required_cols.issubset(df.columns)):
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason="Insufficient data", metrics={})
    try:
        vwap_series = _compute_rolling_vwap(df, WINDOW).dropna()
        if vwap_series.empty:
            return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                          confidence=0.0, reason="VWAP returned empty", metrics={})

        last_price = float(df["Close"].iloc[-1])
        last_vwap = float(vwap_series.iloc[-1])
        # Check volume isn't degenerate
        recent_vol = df["Volume"].iloc[-WINDOW:].sum()
        if last_vwap <= 0 or recent_vol <= 0:
            return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                          confidence=0.0, reason="Invalid VWAP/volume", metrics={})

        distance_pct = (last_price - last_vwap) / last_vwap * 100

        if distance_pct < BUY_THRESHOLD_PCT:
            action = ACTION_BUY
            # Each additional 0.5% below adds 0.1 confidence; cap at 1.0
            confidence = min(1.0, 0.5 + abs(distance_pct - BUY_THRESHOLD_PCT) / 5.0)
            reason = f"Price {distance_pct:+.2f}% vs VWAP (below)"
        elif distance_pct > SELL_THRESHOLD_PCT:
            action = ACTION_SELL
            confidence = min(1.0, 0.5 + abs(distance_pct - SELL_THRESHOLD_PCT) / 5.0)
            reason = f"Price {distance_pct:+.2f}% vs VWAP (above)"
        else:
            action = ACTION_HOLD
            confidence = 0.5
            reason = f"Price {distance_pct:+.2f}% vs VWAP (near)"

        return Signal(
            agent=AGENT_NAME, symbol=symbol, action=action,
            confidence=round(confidence, 3), reason=reason,
            metrics={
                "vwap": round(last_vwap, 2),
                "price": round(last_price, 2),
                "vwap_distance_pct": round(distance_pct, 3),
            },
        )
    except Exception as e:
        logger.error(f"VWAP failed for {symbol}: {e}", exc_info=True)
        return Signal(agent=AGENT_NAME, symbol=symbol, action=ACTION_HOLD,
                      confidence=0.0, reason=f"Error: {str(e)[:80]}", metrics={})
