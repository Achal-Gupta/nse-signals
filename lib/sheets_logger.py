"""
Google Sheets logger. Appends one row per verdict per run.
Schema documented in docs/design/v0.1.0/contracts.md.
"""
import os
import json
import base64
import logging
from typing import List

import gspread
from google.oauth2.service_account import Credentials

from lib.contracts import Verdict

logger = logging.getLogger(__name__)

SHEET_HEADERS = [
    "timestamp_ist",
    "symbol",
    "final_action",
    "final_confidence",
    "technical_action",
    "technical_reason",
    "rsi",
    "stock_sent_action",
    "stock_sent_reason",
    "market_action",
    "market_reason",
    "fused_sent_action",
    "fused_sent_confidence",
    "errors",
]


def _open_sheet():
    """Authenticate and open the configured Google Sheet's first worksheet."""
    creds_b64 = os.environ["GOOGLE_SHEETS_CREDS_JSON"]
    sheet_id = os.environ["GOOGLE_SHEET_ID"]

    creds_dict = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(sheet_id)
    return sh.sheet1


def _ensure_headers(ws) -> None:
    """Write header row if sheet is empty."""
    try:
        first_row = ws.row_values(1)
        if not first_row:
            ws.append_row(SHEET_HEADERS)
    except Exception as e:
        logger.warning(f"Could not verify headers: {e}")


def _verdict_to_row(v: Verdict, error: str = "") -> list:
    tech = v.technical_signal
    fused = v.sentiment_signal
    market = v.market_signal
    stock_sent_action = fused.metrics.get("stock_action", "")
    stock_sent_reason = fused.metrics.get("stock_reason", "")
    return [
        v.timestamp_ist,
        v.symbol,
        v.action,
        round(v.confidence, 3),
        tech.action,
        tech.reason,
        tech.metrics.get("rsi", ""),
        stock_sent_action,
        stock_sent_reason,
        market.action,
        market.reason,
        fused.action,
        round(fused.confidence, 3),
        error,
    ]


def log_verdicts(verdicts: List[Verdict], errors: List[str]) -> None:
    """Append one row per verdict. Errors are global and appended as a single
    extra row with symbol='_RUN_ERROR'."""
    try:
        ws = _open_sheet()
        _ensure_headers(ws)
        rows = [_verdict_to_row(v) for v in verdicts]
        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
        if errors:
            err_row = [""] * len(SHEET_HEADERS)
            err_row[0] = verdicts[0].timestamp_ist if verdicts else ""
            err_row[1] = "_RUN_ERROR"
            err_row[-1] = " | ".join(errors)
            ws.append_row(err_row)
        logger.info(f"Logged {len(rows)} rows to sheet")
    except Exception as e:
        # We don't want sheet failures to break the run
        logger.error(f"Sheet logging failed: {e}", exc_info=True)
