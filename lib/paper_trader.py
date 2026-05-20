"""
Paper trader (v0.3.0) — multi-horizon outcome closure.

Daily EOD job:
  - Scans Signals sheet for unclosed BUY/SELL rows
  - For each, computes which horizon outcomes are now knowable based on date
  - Fills in outcome_eod_pct, outcome_1d_pct, outcome_3d_pct, outcome_5d_pct as available
  - Updates outcome_best_horizon when at least one horizon is filled
"""
import os
import json
import base64
import logging
from datetime import datetime, timedelta, timezone

import gspread
from google.oauth2.service_account import Credentials

from lib.multi_horizon_outcomes import (
    HORIZON_DAYS,
    fetch_daily_history,
    get_close_at_horizon,
    compute_outcome_pct,
    best_horizon_from_outcomes,
)

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


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


def close_pending_trades() -> dict:
    """
    Walk the Signals sheet and fill in any newly-knowable outcome columns.

    Returns counts of {updates, skipped, missing_data}.
    """
    try:
        ws = _open_sheet()
    except Exception as e:
        logger.error(f"Could not open sheet: {e}")
        return {"updates": 0, "skipped": 0, "missing_data": 0}

    try:
        rows = ws.get_all_values()
    except Exception as e:
        logger.error(f"Could not read sheet rows: {e}")
        return {"updates": 0, "skipped": 0, "missing_data": 0}

    if not rows or len(rows) < 2:
        logger.info("Sheet empty or only headers")
        return {"updates": 0, "skipped": 0, "missing_data": 0}

    headers = rows[0]

    # Required column indices
    try:
        ts_idx = headers.index("timestamp_ist")
        symbol_idx = headers.index("symbol")
        action_idx = headers.index("final_action")
        price_idx = headers.index("price_at_signal")
        eod_idx = headers.index("outcome_eod_pct")
        d1_idx = headers.index("outcome_1d_pct")
        d3_idx = headers.index("outcome_3d_pct")
        d5_idx = headers.index("outcome_5d_pct")
        best_idx = headers.index("outcome_best_horizon")
    except ValueError as e:
        logger.error(f"Required column missing from sheet headers: {e}")
        return {"updates": 0, "skipped": 0, "missing_data": 0}

    today_ist = datetime.now(IST).date()
    horizon_cols = {"eod": eod_idx, "1d": d1_idx, "3d": d3_idx, "5d": d5_idx}

    # Group rows by (symbol, signal_date) to batch yfinance calls
    history_cache: dict[tuple[str, str], "pd.DataFrame"] = {}

    updates = 0
    skipped = 0
    missing = 0

    for row_idx, row in enumerate(rows[1:], start=2):
        max_idx = max(ts_idx, symbol_idx, action_idx, price_idx,
                      eod_idx, d1_idx, d3_idx, d5_idx, best_idx)
        if len(row) <= max_idx:
            continue

        ts = row[ts_idx]
        action = row[action_idx]
        if not ts or action not in ("BUY", "SELL"):
            continue

        signal_date = ts.split(" ")[0] if " " in ts else ts

        # Already all filled?
        if all(row[idx].strip() for idx in [eod_idx, d1_idx, d3_idx, d5_idx]):
            continue

        # Don't bother with very old signals (>10 trading days = ~2 weeks calendar)
        try:
            sd = datetime.strptime(signal_date, "%Y-%m-%d").date()
        except ValueError:
            skipped += 1
            continue
        days_since = (today_ist - sd).days
        if days_since < 0 or days_since > 14:
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

        # Fetch history once per (symbol, date)
        cache_key = (symbol, signal_date)
        if cache_key not in history_cache:
            history_cache[cache_key] = fetch_daily_history(symbol, signal_date)
        history = history_cache[cache_key]

        if history is None or history.empty:
            missing += 1
            continue

        # Compute and fill any newly-available horizons
        any_updated = False
        outcome_values: dict[str, float] = {}

        for horizon, col_idx in horizon_cols.items():
            if row[col_idx].strip():
                # Already filled; still capture the value for best_horizon computation
                try:
                    outcome_values[horizon] = float(row[col_idx])
                except ValueError:
                    pass
                continue

            close_price = get_close_at_horizon(history, signal_date, horizon)
            if close_price is None:
                continue

            pct = compute_outcome_pct(action, signal_price, close_price)
            outcome_values[horizon] = pct

            try:
                ws.update_cell(row_idx, col_idx + 1, round(pct, 3))
                any_updated = True
            except Exception as e:
                logger.error(f"Failed update on row {row_idx}, col {horizon}: {e}")

        # Update best_horizon if we have any outcomes
        if outcome_values and any_updated:
            best = best_horizon_from_outcomes(outcome_values)
            try:
                ws.update_cell(row_idx, best_idx + 1, best)
            except Exception as e:
                logger.error(f"Failed best_horizon update on row {row_idx}: {e}")

        if any_updated:
            updates += 1

    logger.info(f"Paper trader: updated {updates} rows, skipped {skipped}, missing data {missing}")
    return {"updates": updates, "skipped": skipped, "missing_data": missing}
