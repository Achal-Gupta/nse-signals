"""
Data Fetcher — pulls OHLCV via yfinance.
Not an LLM agent. Pure data access.
"""
import logging
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def get_ohlcv(symbol: str, period: str = "5d", interval: str = "15m") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV bars for a symbol.

    Args:
        symbol: NSE symbol with .NS suffix, e.g. "RELIANCE.NS"
        period: how far back, e.g. "5d", "1mo"
        interval: candle size, e.g. "15m", "1h", "1d"

    Returns:
        DataFrame with columns [Open, High, Low, Close, Volume] indexed by datetime.
        None if fetch failed or returned empty.
    """
    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
        if df is None or df.empty:
            logger.warning(f"Empty data for {symbol}")
            return None
        # yfinance returns multi-level columns for single ticker in newer versions;
        # flatten if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        logger.error(f"Failed to fetch {symbol}: {e}")
        return None


def get_index_snapshot(symbol: str) -> Optional[dict]:
    """
    Fetch latest snapshot for an index (Nifty, VIX, etc.).
    Returns: {"close": float, "pct_change": float} or None.
    """
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 2:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        prev_close = float(df["Close"].iloc[-2])
        last_close = float(df["Close"].iloc[-1])
        if prev_close == 0:
            return None
        pct = ((last_close - prev_close) / prev_close) * 100
        return {"close": round(last_close, 2), "pct_change": round(pct, 2)}
    except Exception as e:
        logger.error(f"Failed to fetch index {symbol}: {e}")
        return None
