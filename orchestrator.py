"""
Orchestrator (v0.2.0) — LangGraph-based pipeline.

Graph topology:
    START
      ↓
    verify_secrets
      ↓
    check_market_hours  ──(closed)──> END
      ↓ (open or --force)
    load_watchlist
      ↓
    compute_regime          (VIX, Nifty trends)
      ↓
    fetch_market_sentiment  (Claude Haiku, once)
      ↓
    analyze_per_stock_loop  (per-stock: data + 4 indicators + sentiment + fusion + aggregate)
      ↓
    notify_and_log
      ↓
    END
"""
import os
import sys
import logging
from datetime import datetime, time, timezone, timedelta
from pathlib import Path
from typing import Optional

import yaml
from langgraph.graph import StateGraph, START, END

sys.path.insert(0, str(Path(__file__).parent))

from lib.contracts import (
    Signal, Verdict, Regime,
    ACTION_BUY, ACTION_SELL, ACTION_HOLD,
)
from lib.langgraph_state import TradingState
from lib.email_notifier import send_email
from lib.sheets_logger import log_verdicts
from lib.secret_validator import verify_secrets, SecretError
from lib.aggregator import aggregate as aggregate_signals

from agents.data_fetcher import get_ohlcv
from agents.data_fetcher.fetcher import get_index_snapshot
from agents.rsi import analyze as rsi_analyze
from agents.macd import analyze as macd_analyze
from agents.bollinger import analyze as bb_analyze
from agents.vwap import analyze as vwap_analyze
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
NIFTY_50 = "^NSEI"
INDIA_VIX = "^INDIAVIX"

FORCE_RUN = "--force" in sys.argv


def in_market_hours(now_ist: datetime) -> bool:
    if now_ist.weekday() >= 5:
        return False
    return MARKET_OPEN <= now_ist.time() <= MARKET_CLOSE


def load_watchlist_yaml(path: str = "config/watchlist.yaml") -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("stocks", [])


# ────────────────────────────────────────────────────────────
# LangGraph nodes
# ────────────────────────────────────────────────────────────

def node_check_market_hours(state: TradingState) -> TradingState:
    now_ist = datetime.now(IST)
    timestamp = now_ist.strftime("%Y-%m-%d %H:%M:%S")
    if FORCE_RUN:
        logger.info("--force used; bypassing market-hours check")
        return {"timestamp_ist": timestamp, "skipped": False, "errors": []}
    if not in_market_hours(now_ist):
        logger.info(f"Outside market hours (IST {now_ist.strftime('%H:%M')}, "
                    f"weekday={now_ist.weekday()}). Skipping.")
        return {"timestamp_ist": timestamp, "skipped": True, "errors": []}
    return {"timestamp_ist": timestamp, "skipped": False, "errors": []}


def node_load_watchlist(state: TradingState) -> TradingState:
    watchlist = load_watchlist_yaml()
    logger.info(f"Watchlist size: {len(watchlist)}")
    return {"watchlist": watchlist}


def node_compute_regime(state: TradingState) -> TradingState:
    """Fetch regime indicators (VIX + Nifty trends)."""
    import yfinance as yf
    import pandas as pd

    vix_snap = get_index_snapshot(INDIA_VIX)
    nifty_snap = get_index_snapshot(NIFTY_50)

    # Compute Nifty 5-day percent change
    nifty_5d = None
    try:
        df = yf.download(NIFTY_50, period="10d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            closes = df["Close"].dropna()
            if len(closes) >= 6:
                start = float(closes.iloc[-6])
                end = float(closes.iloc[-1])
                if start > 0:
                    nifty_5d = round((end - start) / start * 100, 2)
    except Exception as e:
        logger.warning(f"Could not compute Nifty 5d trend: {e}")

    regime = Regime(
        vix_level=vix_snap["close"] if vix_snap else None,
        vix_pct_change=vix_snap["pct_change"] if vix_snap else None,
        nifty_pct=nifty_snap["pct_change"] if nifty_snap else None,
        nifty_5d_pct=nifty_5d,
    )
    logger.info(f"Regime: VIX={regime.vix_level} ({regime.vix_pct_change}%), "
                f"Nifty today={regime.nifty_pct}%, Nifty 5d={regime.nifty_5d_pct}%")
    return {"regime": regime}


def node_market_sentiment(state: TradingState) -> TradingState:
    logger.info("Fetching market sentiment...")
    market_signal = market_analyze()
    logger.info(f"Market: {market_signal.action} ({market_signal.confidence:.2f}) "
                f"— {market_signal.reason}")
    return {"market_signal": market_signal}


def node_analyze_per_stock(state: TradingState) -> TradingState:
    """Per-stock loop: fetch + 4 indicators + sentiment + fusion + aggregate."""
    verdicts: list[Verdict] = []
    errors: list[str] = list(state.get("errors", []))
    watchlist = state["watchlist"]
    market_signal = state["market_signal"]
    regime = state["regime"]
    timestamp = state["timestamp_ist"]

    for stock in watchlist:
        symbol = stock["symbol"]
        name = stock["name"]
        logger.info(f"--- {symbol} ---")
        try:
            df = get_ohlcv(symbol, period="5d", interval="15m")

            # Indicator agents (rule-based, no LLM)
            rsi_sig = rsi_analyze(symbol, df)
            macd_sig = macd_analyze(symbol, df)
            bb_sig = bb_analyze(symbol, df)
            vwap_sig = vwap_analyze(symbol, df)

            # Sentiment (LLM-based)
            stock_sent = stock_sentiment_analyze(symbol, name)
            fused_sent = fuse_sentiment(market_signal, stock_sent)

            per_agent = {
                "rsi": rsi_sig,
                "macd": macd_sig,
                "bollinger": bb_sig,
                "vwap": vwap_sig,
                "sentiment_fusion": fused_sent,
            }

            action, confidence, raw_score = aggregate_signals(per_agent)

            # Capture current price for paper trader's later use
            price_at_signal = 0.0
            try:
                if df is not None and not df.empty:
                    price_at_signal = float(df["Close"].iloc[-1])
            except Exception:
                pass

            verdicts.append(Verdict(
                symbol=symbol,
                action=action,
                confidence=confidence,
                price_at_signal=price_at_signal,
                per_agent_signals=per_agent,
                market_signal=market_signal,
                fused_sentiment_signal=fused_sent,
                regime=regime,
                timestamp_ist=timestamp,
                aggregator_score=raw_score,
            ))
            logger.info(
                f"{symbol}: {action} ({confidence:.2f}, score={raw_score:+.2f}) | "
                f"RSI:{rsi_sig.action[0]} MACD:{macd_sig.action[0]} "
                f"BB:{bb_sig.action[0]} VWAP:{vwap_sig.action[0]} "
                f"SENT:{fused_sent.action[0]}"
            )
        except Exception as e:
            err_msg = f"{symbol}: {type(e).__name__}: {e}"
            logger.error(err_msg, exc_info=True)
            errors.append(err_msg)

    return {"verdicts": verdicts, "errors": errors}


def node_notify_and_log(state: TradingState) -> TradingState:
    verdicts = state.get("verdicts", [])
    errors = list(state.get("errors", []))

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
    return {"errors": errors}


# ────────────────────────────────────────────────────────────
# Graph wiring
# ────────────────────────────────────────────────────────────

def should_continue(state: TradingState) -> str:
    """Conditional edge: skip the rest if outside market hours."""
    return "skip" if state.get("skipped") else "continue"


def build_graph():
    graph = StateGraph(TradingState)

    graph.add_node("check_market_hours", node_check_market_hours)
    graph.add_node("load_watchlist", node_load_watchlist)
    graph.add_node("compute_regime", node_compute_regime)
    graph.add_node("market_sentiment", node_market_sentiment)
    graph.add_node("analyze_per_stock", node_analyze_per_stock)
    graph.add_node("notify_and_log", node_notify_and_log)

    graph.add_edge(START, "check_market_hours")
    graph.add_conditional_edges(
        "check_market_hours",
        should_continue,
        {"skip": END, "continue": "load_watchlist"},
    )
    graph.add_edge("load_watchlist", "compute_regime")
    graph.add_edge("compute_regime", "market_sentiment")
    graph.add_edge("market_sentiment", "analyze_per_stock")
    graph.add_edge("analyze_per_stock", "notify_and_log")
    graph.add_edge("notify_and_log", END)

    return graph.compile()


def run() -> int:
    try:
        verify_secrets()
    except SecretError as e:
        logger.error(str(e))
        return 1

    app = build_graph()
    final_state = app.invoke({})
    return 0


if __name__ == "__main__":
    sys.exit(run())
