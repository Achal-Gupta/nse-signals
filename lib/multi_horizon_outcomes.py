"""
Multi-horizon outcome computation.

For each BUY/SELL signal, compute realized P&L at multiple horizons:
  - eod: same trading day's close
  - 1d: next trading day's close
  - 3d: 3 trading days later close
  - 5d: 5 trading days later close

The EOD reviewer runs daily and fills in whichever horizon's outcome is now
knowable for past signals.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

# Map horizon name to number of trading days ahead (0 = same day)
HORIZON_DAYS = {
    "eod": 0,
    "1d": 1,
    "3d": 3,
    "5d": 5,
}


def fetch_daily_history(symbol: str, signal_date: str, max_lookahead_days: int = 10) -> Optional[pd.DataFrame]:
    """
    Fetch daily OHLCV from signal_date onwards.
    Returns a DataFrame indexed by date with Close column, or None on failure.
    """
    try:
        sd = datetime.strptime(signal_date, "%Y-%m-%d").date()
        start = (sd - timedelta(days=2)).isoformat()
        # Lookahead must allow enough calendar days for max trading days
        end = (sd + timedelta(days=max_lookahead_days + 7)).isoformat()
        df = yf.download(symbol, start=start, end=end, progress=False,
                         auto_adjust=True, interval="1d")
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        # Normalize index to dates
        df.index = pd.to_datetime(df.index).date
        return df[df.index >= sd]
    except Exception as e:
        logger.error(f"fetch_daily_history failed for {symbol} from {signal_date}: {e}")
        return None


def get_close_at_horizon(history: pd.DataFrame, signal_date: str, horizon: str) -> Optional[float]:
    """
    Return the closing price `horizon` trading days after signal_date,
    using history DataFrame already filtered to dates >= signal_date.

    For 'eod', returns the close on the signal_date itself.
    Returns None if not enough data yet.
    """
    if history is None or history.empty:
        return None

    days_ahead = HORIZON_DAYS.get(horizon)
    if days_ahead is None:
        return None

    try:
        if days_ahead >= len(history):
            return None
        target_date = history.index[days_ahead]
        return float(history.loc[target_date, "Close"])
    except (KeyError, IndexError) as e:
        logger.debug(f"No close at horizon {horizon} for {signal_date}: {e}")
        return None


def compute_outcome_pct(action: str, signal_price: float, close_price: float) -> float:
    """Hypothetical return for a paper trade. BUY profits when price rises; SELL profits when it falls."""
    if signal_price <= 0:
        return 0.0
    if action == "BUY":
        return (close_price - signal_price) / signal_price * 100
    if action == "SELL":
        return (signal_price - close_price) / signal_price * 100
    return 0.0


def best_horizon_from_outcomes(outcomes: dict[str, Optional[float]]) -> str:
    """
    Pick the horizon with the largest absolute return among the present values.
    Returns 'eod' if no outcomes present (sensible default).
    """
    present = {h: v for h, v in outcomes.items() if v is not None}
    if not present:
        return ""
    return max(present, key=lambda h: abs(present[h]))
