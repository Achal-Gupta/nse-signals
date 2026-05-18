"""
Paper trader.

Two roles:
1. log_pending_trades(): called at signal time (already done as part of normal
   logging in sheets_logger.py — paper trader doesn't add new logging here)
2. close_pending_trades(): EOD job that finds yesterday's BUY/SELL signals and
   fills in actual outcome (next available close vs signal price).

In v0.2.0 paper trades live in the same sheet as signals. The outcome columns
(`outcome_action`, `outcome_pct`, `outcome_status`) are filled in by the EOD job.
"""
import os
import json
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials
import yfinance as yf

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

# Sheet column indexes (1-based). These must match SHEET_HEADERS in sheets_logger.
COL_TIMESTAMP = 1
COL_SYMBOL = 2
COL_FINAL_ACTION = 3
COL_PRICE_AT_SIGNAL = 5
COL_OUTCOME_PCT = -3   # last three columns: outcome_pct, outcome_status, errors
COL_OUTCOME_STATUS = -2


def _open_sheet():
    creds_b64 = os.environ["GOOGLE_SHEETS_CREDS_JSON"]
    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    creds_dict = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1


def _fetch_close_price(symbol: str, target_date_str: str) -> Optional[float]:
    """
    Fetch the daily close for a symbol on a target trading date.
    Returns None if data unavailable (weekend, holiday, missing).
    """
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        # Pull a wide range and look up the date — handles weekends/holidays
        start = (target_date - timedelta(days=2)).isoformat()
        end = (target_date + timedelta(days=3)).isoformat()
        df = yf.download(symbol, start=start, end=end, progress=False,
                         auto_adjust=True, interval="1d")
        if df is None or df.empty:
            return None
        import pandas as pd
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        # Index is timezone-naive dates; find the first date >= target_date
        df.index = df.index.date if hasattr(df.index, "date") else df.index
        for d in df.index:
            if d >= target_date:
                return float(df.loc[d, "Close"])
        return None
    except Exception as e:
        logger.error(f"Failed to fetch close for {symbol} on {target_date_str}: {e}")
        return None


def close_pending_trades(lookback_days: int = 1) -> None:
    """
    Find unclosed BUY/SELL signals from `lookback_days` ago and fill in outcomes.

    For each pending signal:
      - Look up the trading day after signal_date
      - Fetch that day's close price
      - outcome_pct = (close - signal_price) / signal_price * 100   (BUY)
                    = (signal_price - close) / signal_price * 100   (SELL)
      - outcome_status = "WIN" if positive else "LOSS" (zero counts as WIN)
    """
    try:
        ws = _open_sheet()
    except Exception as e:
        logger.error(f"Could not open sheet: {e}")
        return

    try:
        rows = ws.get_all_values()
    except Exception as e:
        logger.error(f"Could not read sheet rows: {e}")
        return

    if not rows or len(rows) < 2:
        logger.info("Sheet empty or only headers — nothing to close")
        return

    headers = rows[0]
    try:
        outcome_pct_idx = headers.index("outcome_pct")
        outcome_status_idx = headers.index("outcome_status")
        action_idx = headers.index("final_action")
        symbol_idx = headers.index("symbol")
        price_idx = headers.index("price_at_signal")
        ts_idx = headers.index("timestamp_ist")
    except ValueError as e:
        logger.error(f"Required column missing from sheet headers: {e}")
        return

    today_ist = datetime.now(IST).date()
    target_signal_date = (today_ist - timedelta(days=lookback_days)).isoformat()
    close_date = today_ist.isoformat()

    updates = 0
    skipped = 0

    # Iterate rows skipping header
    for row_idx, row in enumerate(rows[1:], start=2):
        # Guard against short rows
        if len(row) <= max(outcome_pct_idx, outcome_status_idx, action_idx,
                            symbol_idx, price_idx, ts_idx):
            continue

        ts = row[ts_idx]
        action = row[action_idx]
        if not ts or action not in ("BUY", "SELL"):
            continue

        signal_date = ts.split(" ")[0] if " " in ts else ts
        if signal_date != target_signal_date:
            continue

        # Already filled?
        if row[outcome_pct_idx].strip():
            continue

        symbol = row[symbol_idx]
        try:
            signal_price = float(row[price_idx])
        except (ValueError, TypeError):
            skipped += 1
            continue

        if signal_price <= 0:
            skipped += 1
            continue

        close_price = _fetch_close_price(symbol, close_date)
        if close_price is None:
            skipped += 1
            continue

        if action == "BUY":
            pct = (close_price - signal_price) / signal_price * 100
        else:  # SELL
            pct = (signal_price - close_price) / signal_price * 100

        status = "WIN" if pct >= 0 else "LOSS"

        try:
            ws.update_cell(row_idx, outcome_pct_idx + 1, round(pct, 3))
            ws.update_cell(row_idx, outcome_status_idx + 1, status)
            updates += 1
        except Exception as e:
            logger.error(f"Failed to update row {row_idx}: {e}")

    logger.info(f"Paper trader: closed {updates} positions, skipped {skipped}")
