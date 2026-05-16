"""
Stock Sentiment connectors — fetches per-company news headlines.
Uses Google News RSS (free, no API key).
"""
import logging
import urllib.parse
from typing import List

import feedparser

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


def fetch_headlines(company_name: str, limit: int = 5) -> List[str]:
    """
    Fetch the latest news headlines for a company. Returns at most `limit`
    headline strings; never raises (returns [] on failure).
    """
    query = urllib.parse.quote_plus(f"{company_name} stock")
    url = GOOGLE_NEWS_RSS.format(q=query)
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return []
        return [entry.title for entry in feed.entries[:limit]]
    except Exception as e:
        logger.error(f"Failed to fetch headlines for {company_name}: {e}")
        return []
