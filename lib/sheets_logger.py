"""
Google Sheets logger for v0.2.1.

Schema change vs v0.2.0:
- Added `trade_idea_id` column (between aggregator_score and rsi_action)
- Schema goes from 27 to 28 columns

For HOLDs, trade_idea_id is empty. For BUY/SELL, it groups same-hour same-symbol
same-action signals so post-hoc analysis can dedupe stickiness.
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
    "timestamp_ist",            # 1
    "symbol",                   # 2
    "final_action",             # 3
    "final_confidence",         # 4
    "price_at_signal",          # 5
    "aggregator_score",         # 6
    "trade_idea_id",            # 7 (NEW in v0.2.1)
    # Per-indicator detail
    "rsi_action",               # 8
    "rsi_value",                # 9
    "macd_action",              # 10
    "macd_hist",                # 11
    "bb_action",                # 12
    "bb_percent_b",             # 13
    "vwap_action",              # 14
    "vwap_distance_pct",        # 15
    # Sentiment
    "stock_sent_action",        # 16
    "stock_sent_reason",        # 17
    "market_action",            # 18
    "market_reason",            # 19
    "fused_sent_action",        # 20
    "fused_sent_confidence",    # 21
    # Regime
    "vix_level",                # 22
    "vix_pct_change",           # 23
    "nifty_pct",                # 24
    "nifty_5d_pct",             # 25
    # Outcome
    "outcome_pct",              # 26
    "outcome_status",           # 27
    "errors",                   # 28
]


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


def _ensure_headers(ws) -> None:
    try:
        first_row = ws.row_values(1)
        if not first_row:
            ws.append_row(SHEET_HEADERS)
            logger.info("Wrote v0.2.1 headers to empty sheet")
        elif first_row != SHEET_HEADERS:
            logger.warning(
                "Existing sheet headers don't match v0.2.1 schema. "
                "Manually update the header row or use a new sheet to avoid drift."
            )
    except Exception as e:
        logger.warning(f"Could not verify headers: {e}")


def _get_per_agent(verdict: Verdict, name: str):
    return verdict.per_agent_signals.get(name)


def _verdict_to_row(v: Verdict, error: str = "") -> list:
    rsi = _get_per_agent(v, "rsi")
    macd = _get_per_agent(v, "macd")
    bb = _get_per_agent(v, "bollinger")
    vwap = _get_per_agent(v, "vwap")
    fused = v.fused_sentiment_signal
    market = v.market_signal
    stock_sent_action = fused.metrics.get("stock_action", "") if fused else ""
    stock_sent_reason = fused.metrics.get("stock_reason", "") if fused else ""
    regime = v.regime

    return [
        v.timestamp_ist,
        v.symbol,
        v.action,
        round(v.confidence, 3),
        round(v.price_at_signal, 2) if v.price_at_signal else "",
        round(v.aggregator_score, 3),
        v.trade_idea_id,
        # RSI
        rsi.action if rsi else "",
        rsi.metrics.get("rsi", "") if rsi else "",
        # MACD
        macd.action if macd else "",
        macd.metrics.get("macd_hist", "") if macd else "",
        # BB
        bb.action if bb else "",
        bb.metrics.get("bb_percent_b", "") if bb else "",
        # VWAP
        vwap.action if vwap else "",
        vwap.metrics.get("vwap_distance_pct", "") if vwap else "",
        # Sentiment
        stock_sent_action,
        stock_sent_reason,
        market.action if market else "",
        market.reason if market else "",
        fused.action if fused else "",
        round(fused.confidence, 3) if fused else "",
        # Regime
        regime.vix_level if regime else "",
        regime.vix_pct_change if regime else "",
        regime.nifty_pct if regime else "",
        regime.nifty_5d_pct if regime else "",
        # Outcome (blank, filled later by EOD)
        "",
        "",
        # Errors
        error,
    ]


def log_verdicts(verdicts: List[Verdict], errors: List[str]) -> None:
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
        logger.error(f"Sheet logging failed: {e}", exc_info=True)
