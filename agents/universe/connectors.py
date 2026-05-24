"""
Universe connectors — data sources for stock selection.

- Nifty 100 baseline from YAML data file
- Google News RSS scraping for trending stock mentions
- yfinance for market movers (top gainers/losers)
"""
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Optional

import yaml
import feedparser
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

NIFTY_100_FILE = Path(__file__).parent.parent.parent / "data" / "nifty_100_baseline.yaml"

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
NEWS_QUERIES = [
    "Indian stock market",
    "NSE shares today",
    "Nifty stocks news",
    "BSE stocks gainers losers",
]


def load_nifty_100_baseline() -> list[dict]:
    """Load the curated Nifty 100 list from YAML."""
    try:
        with open(NIFTY_100_FILE) as f:
            data = yaml.safe_load(f)
        return data.get("stocks", [])
    except Exception as e:
        logger.error(f"Failed to load Nifty 100 baseline: {e}")
        return []


def filter_by_liquidity(stocks: list[dict], min_volume_value: float = 5e8) -> list[dict]:
    """
    Filter stocks by recent traded value (price × volume).
    Default threshold: ₹50 crore notional traded daily.

    Returns the input stocks annotated with `avg_traded_value` and `avg_close`,
    sorted by avg_traded_value descending.
    """
    enriched = []
    for stock in stocks:
        symbol = stock["symbol"]
        try:
            df = yf.download(symbol, period="5d", interval="1d",
                             progress=False, auto_adjust=True)
            if df is None or df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df["traded_value"] = df["Close"] * df["Volume"]
            avg_value = float(df["traded_value"].mean())
            avg_close = float(df["Close"].mean())
            if avg_value >= min_volume_value and avg_close >= 100:
                enriched.append({
                    **stock,
                    "avg_traded_value": round(avg_value, 0),
                    "avg_close": round(avg_close, 2),
                })
        except Exception as e:
            logger.debug(f"Skipping {symbol}: {e}")
            continue

    enriched.sort(key=lambda s: s["avg_traded_value"], reverse=True)
    return enriched


# ─────────────────────────────────────────
# News-hybrid sources
# ─────────────────────────────────────────

# Patterns to extract NSE-style stock mentions from headlines
# Looks for ALLCAPS tokens that could be tickers, or company names from baseline
_TICKER_RE = re.compile(r"\b([A-Z]{3,12})\b")


def fetch_market_news_headlines(limit_per_query: int = 30) -> list[str]:
    """Fetch headlines from multiple market-related news queries."""
    headlines = []
    for q in NEWS_QUERIES:
        url = GOOGLE_NEWS_RSS.format(q=urllib.parse.quote_plus(q))
        try:
            feed = feedparser.parse(url)
            headlines.extend(e.title for e in feed.entries[:limit_per_query])
        except Exception as e:
            logger.warning(f"News fetch failed for query '{q}': {e}")
            continue
    return headlines


def extract_mentioned_companies(headlines: list[str], baseline_stocks: list[dict]) -> list[dict]:
    """
    Match company names from baseline against headlines.
    Returns baseline stocks whose name appears in at least one headline,
    sorted by mention count (highest first).
    """
    mention_count: dict[str, int] = {}
    name_to_stock: dict[str, dict] = {}

    for stock in baseline_stocks:
        name_lower = stock["name"].lower()
        name_to_stock[name_lower] = stock
        mention_count[name_lower] = 0
        # Also track first word of name (e.g., "Reliance" from "Reliance Industries")
        first_word = name_lower.split()[0]
        if first_word != name_lower and len(first_word) >= 4:
            name_to_stock.setdefault(first_word, stock)
            mention_count.setdefault(first_word, 0)

    for headline in headlines:
        hl_lower = headline.lower()
        for name in mention_count:
            if name in hl_lower:
                mention_count[name] += 1

    # Aggregate per-stock (a stock may match both full name and first word)
    stock_counts: dict[str, int] = {}
    for name, count in mention_count.items():
        if count == 0:
            continue
        stock = name_to_stock[name]
        symbol = stock["symbol"]
        stock_counts[symbol] = max(stock_counts.get(symbol, 0), count)

    # Build result
    out = []
    for symbol, count in sorted(stock_counts.items(), key=lambda x: -x[1]):
        stock = next(s for s in baseline_stocks if s["symbol"] == symbol)
        out.append({**stock, "news_mentions": count, "source": "news_hybrid"})
    return out


def fetch_movers(baseline_stocks: list[dict], top_n: int = 10) -> list[dict]:
    """
    Identify top gainers and top losers among baseline_stocks based on today's
    intraday percent change.

    Returns up to `top_n` stocks, mixed gainers and losers, with `pct_change` set.
    """
    movers = []
    for stock in baseline_stocks[:50]:  # Don't poll the entire list — cap for speed
        symbol = stock["symbol"]
        try:
            df = yf.download(symbol, period="2d", interval="1d",
                             progress=False, auto_adjust=True)
            if df is None or df.empty or len(df) < 2:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            prev = float(df["Close"].iloc[-2])
            curr = float(df["Close"].iloc[-1])
            if prev <= 0:
                continue
            pct = (curr - prev) / prev * 100
            movers.append({
                **stock,
                "pct_change": round(pct, 2),
                "source": "news_hybrid",
            })
        except Exception:
            continue

    # Sort by absolute pct change descending, take top N
    movers.sort(key=lambda s: abs(s["pct_change"]), reverse=True)
    return movers[:top_n]
