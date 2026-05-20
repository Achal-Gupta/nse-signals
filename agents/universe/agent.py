"""
Universe Agent.

Builds the daily watchlist of 40 stocks:
  - 20 from filtered Nifty 100 baseline (by liquidity)
  - 20 from news-hybrid (mentions in headlines + market movers)

See agents/universe/skill.md for the full design.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path

import yaml

from lib.contracts import Universe
from agents.universe.connectors import (
    load_nifty_100_baseline,
    filter_by_liquidity,
    fetch_market_news_headlines,
    extract_mentioned_companies,
    fetch_movers,
)

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "universe_config.yaml"

# Hardcoded fallback list — guarantees never-empty universe
FALLBACK_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "source": "fallback"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "source": "fallback"},
    {"symbol": "INFY.NS", "name": "Infosys", "source": "fallback"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "source": "fallback"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "source": "fallback"},
]


def _load_config() -> dict:
    """Load universe_config.yaml with sensible defaults if missing."""
    defaults = {
        "pool1_count": 20,
        "pool2_count": 20,
        "min_volume_value": 5e8,
    }
    try:
        with open(CONFIG_FILE) as f:
            data = yaml.safe_load(f) or {}
        return {**defaults, **data}
    except Exception as e:
        logger.warning(f"Using default universe config (could not load file): {e}")
        return defaults


def build_universe() -> Universe:
    """
    Build today's stock universe.

    Returns a Universe with stocks list and metadata. Never raises; on total
    failure returns the fallback universe.
    """
    timestamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    config = _load_config()
    errors: list[str] = []

    # ─── Pool 1: Nifty 100 baseline filtered by liquidity ───
    baseline = load_nifty_100_baseline()
    if not baseline:
        errors.append("nifty_100_baseline.yaml empty or unreadable")
        logger.error("Universe Agent: baseline load failed")

    pool1: list[dict] = []
    if baseline:
        try:
            enriched = filter_by_liquidity(baseline, min_volume_value=config["min_volume_value"])
            pool1 = [
                {**s, "source": "nifty100"}
                for s in enriched[:config["pool1_count"]]
            ]
            logger.info(f"Universe Pool 1 (Nifty 100 baseline): {len(pool1)} stocks")
        except Exception as e:
            errors.append(f"pool1 filtering: {e}")
            logger.error(f"Pool 1 failed: {e}", exc_info=True)

    # ─── Pool 2: News-hybrid ───
    pool2: list[dict] = []
    if baseline:
        try:
            # Stream A: news mentions
            headlines = fetch_market_news_headlines(limit_per_query=30)
            logger.info(f"Fetched {len(headlines)} market news headlines")
            mentioned = extract_mentioned_companies(headlines, baseline)
            logger.info(f"News-mentioned stocks: {len(mentioned)}")

            # Stream B: market movers
            movers = fetch_movers(baseline, top_n=15)
            logger.info(f"Market movers: {len(movers)}")

            # Merge dedup
            seen = set()
            combined = []
            for s in mentioned + movers:
                if s["symbol"] not in seen:
                    combined.append(s)
                    seen.add(s["symbol"])
            pool2 = combined[:config["pool2_count"]]
            logger.info(f"Universe Pool 2 (news-hybrid): {len(pool2)} stocks")
        except Exception as e:
            errors.append(f"pool2 selection: {e}")
            logger.error(f"Pool 2 failed: {e}", exc_info=True)

    # ─── Merge with dedup ───
    final: list[dict] = []
    seen = set()
    overlaps = 0

    for s in pool1:
        if s["symbol"] not in seen:
            final.append(s)
            seen.add(s["symbol"])

    for s in pool2:
        if s["symbol"] in seen:
            overlaps += 1
            # Tag existing entry with combined source
            for f in final:
                if f["symbol"] == s["symbol"]:
                    f["source"] = "nifty100+news_hybrid"
                    break
            continue
        final.append(s)
        seen.add(s["symbol"])

    # ─── Fallback if empty ───
    if not final:
        logger.warning("Universe is empty after all pools; using fallback")
        final = FALLBACK_STOCKS[:]
        errors.append("Used fallback universe — all pools failed")

    universe = Universe(
        timestamp_ist=timestamp,
        stocks=final,
        pool1_size=len(pool1),
        pool2_size=len(pool2),
        overlaps=overlaps,
        errors=errors,
    )

    logger.info(f"Universe built: {len(final)} stocks "
                f"(pool1={len(pool1)}, pool2={len(pool2)}, overlaps={overlaps})")
    return universe
