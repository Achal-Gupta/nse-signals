"""
Orchestrator — the main entry point for v0.1.0.

Flow:
  1. Check we're in market hours (IST)
  2. Load watchlist
  3. Get market sentiment (once)
  4. For each stock: fetch OHLCV, run technical + stock sentiment,
     fuse sentiment, aggregate final verdict
  5. Send email + log to sheet
"""
import os
import sys
import logging
from datetime import datetime, time, timezone, timedelta
from pathlib import Path

import yaml

# Ensure project root is on path when run via GitHub Actions
sys.path.insert(0, str(Path(__file__).parent))

from lib.contracts import (
    Signal, Verdict,
    ACTION_BUY, ACTION_SELL, ACTION_HOLD,
)
from lib.email_notifier import send_email
from lib.sheets_logger import log_verdicts

from agents.data_fetcher import get_ohlcv
from agents.technical import analyze as technical_analyze
from agents.market_sentiment import analyze as market_analyze
from agents.stock_sentiment import analyze as stock_sentiment_analyze
from agents.sentiment_fusion import fuse as fuse_sentiment


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator")

IST = timezone(timedelta(hours=5, minutes=30))
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


def in_market_hours(now_ist: datetime) -> bool:
    """Mon-Fri between 09:15 and 15:30 IST."""
    if now_ist.weekday() >= 5:  # Sat/Sun
        return False
    return MARKET_OPEN <= now_ist.time() <= MARKET_CLOSE


def load_watchlist(path: str = "config/watchlist.yaml") -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("stocks", [])


def aggregate(technical: Signal, sentiment: Signal, market: Signal,
              symbol: str, timestamp_ist: str) -> Verdict:
    """
    v0.1.0 aggregation rule:
      - technical & sentiment agree on a directional action → use it,
        confidence = average
      - else → HOLD, confidence 0.3
    """
    if technical.action == sentiment.action and technical.action != ACTION_HOLD:
        avg_conf = round((technical.confidence + sentiment.confidence) / 2, 3)
        return Verdict(
            symbol=symbol,
            action=technical.action,
            confidence=avg_conf,
            technical_signal=technical,
            sentiment_signal=sentiment,
            market_signal=market,
            timestamp_ist=timestamp_ist,
        )
    return Verdict(
        symbol=symbol,
        action=ACTION_HOLD,
        confidence=0.3,
        technical_signal=technical,
        sentiment_signal=sentiment,
        market_signal=market,
        timestamp_ist=timestamp_ist,
    )


def run(force: bool = False) -> int:
    """Main run. Returns exit code (0 = success)."""
    now_ist = datetime.now(IST)
    timestamp_str = now_ist.strftime("%Y-%m-%d %H:%M:%S")

    if not force and not in_market_hours(now_ist):
        logger.info(f"Outside market hours (IST {now_ist.strftime('%H:%M')}, "
                    f"weekday={now_ist.weekday()}). Exiting.")
        return 0

    watchlist = load_watchlist()
    logger.info(f"Watchlist size: {len(watchlist)}")

    # 1. Market sentiment — once per run
    logger.info("Fetching market sentiment...")
    market_signal = market_analyze()
    logger.info(f"Market: {market_signal.action} ({market_signal.confidence:.2f}) "
                f"— {market_signal.reason}")

    verdicts: list[Verdict] = []
    errors: list[str] = []

    # 2. Per-stock analysis
    for stock in watchlist:
        symbol = stock["symbol"]
        name = stock["name"]
        try:
            logger.info(f"--- {symbol} ---")
            df = get_ohlcv(symbol, period="5d", interval="15m")
            tech_signal = technical_analyze(symbol, df)
            stock_sent = stock_sentiment_analyze(symbol, name)
            fused = fuse_sentiment(market_signal, stock_sent)
            verdict = aggregate(tech_signal, fused, market_signal, symbol, timestamp_str)
            verdicts.append(verdict)
            logger.info(f"{symbol}: {verdict.action} ({verdict.confidence:.2f})")
        except Exception as e:
            err_msg = f"{symbol}: {type(e).__name__}: {e}"
            logger.error(err_msg, exc_info=True)
            errors.append(err_msg)

    # 3. Notify + log
    try:
        send_email(verdicts, errors)
    except Exception as e:
        logger.error(f"Email send failed: {e}", exc_info=True)
        errors.append(f"email: {e}")

    try:
        log_verdicts(verdicts, errors)
    except Exception as e:
        logger.error(f"Sheet logging failed: {e}", exc_info=True)

    logger.info(f"Done. Verdicts: {len(verdicts)}, errors: {len(errors)}")
    return 0


if __name__ == "__main__":
    force = "--force" in sys.argv
    sys.exit(run(force=force))
