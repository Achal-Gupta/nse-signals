"""
Stock Sentiment Agent.
Fetches news per company, classifies via Claude Haiku.
"""
import os
import json
import logging
from typing import Optional

from anthropic import Anthropic

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD, VALID_ACTIONS
from agents.stock_sentiment.connectors import fetch_headlines

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are an equity analyst covering Indian listed companies. \
Classify the near-term (1-5 trading days) directional bias for the company \
based on its latest headlines.

Respond with STRICT JSON, no preamble or markdown:
{"action": "BUY"|"SELL"|"HOLD", "confidence": 0.0-1.0, "reason": "<max 120 chars>", \
"positive": <int>, "negative": <int>, "neutral": <int>}

Rules:
- A single highly material headline (M&A, earnings beat/miss, regulatory ruling) outweighs many minor ones
- If headlines are off-topic or stale, prefer HOLD with low confidence
- BUY = positive directional bias; SELL = negative
"""


def _parse_response(raw: str) -> Optional[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                obj = json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                return None
        else:
            return None
    if not isinstance(obj, dict):
        return None
    action = str(obj.get("action", "")).upper()
    if action not in VALID_ACTIONS:
        return None
    try:
        conf = float(obj.get("confidence", 0.5))
        conf = max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        conf = 0.5
    return {
        "action": action,
        "confidence": conf,
        "reason": str(obj.get("reason", ""))[:160],
        "positive": int(obj.get("positive", 0) or 0),
        "negative": int(obj.get("negative", 0) or 0),
        "neutral": int(obj.get("neutral", 0) or 0),
    }


def analyze(symbol: str, company_name: str) -> Signal:
    """Fetch headlines for the company and classify sentiment with Claude Haiku."""
    headlines = fetch_headlines(company_name, limit=5)

    if not headlines:
        return Signal(
            agent="stock_sentiment",
            symbol=symbol,
            action=ACTION_HOLD,
            confidence=0.0,
            reason="No headlines available",
            metrics={"headline_count": 0},
        )

    headlines_block = "\n".join(f"- {h}" for h in headlines)
    user_msg = f"Company: {company_name} ({symbol})\n\nHEADLINES:\n{headlines_block}"

    try:
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=250,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = message.content[0].text if message.content else ""
        parsed = _parse_response(raw)
        if parsed is None:
            logger.warning(f"Could not parse stock sentiment for {symbol}: {raw[:200]}")
            return Signal(
                agent="stock_sentiment",
                symbol=symbol,
                action=ACTION_HOLD,
                confidence=0.3,
                reason="Could not parse LLM response",
                metrics={"headline_count": len(headlines)},
            )

        return Signal(
            agent="stock_sentiment",
            symbol=symbol,
            action=parsed["action"],
            confidence=parsed["confidence"],
            reason=parsed["reason"],
            metrics={
                "headline_count": len(headlines),
                "positive": parsed["positive"],
                "negative": parsed["negative"],
                "neutral": parsed["neutral"],
            },
        )
    except Exception as e:
        logger.error(f"Stock sentiment LLM call failed for {symbol}: {e}", exc_info=True)
        return Signal(
            agent="stock_sentiment",
            symbol=symbol,
            action=ACTION_HOLD,
            confidence=0.0,
            reason=f"Error: {str(e)[:80]}",
            metrics={"headline_count": len(headlines)},
        )
