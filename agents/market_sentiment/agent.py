"""
Market Sentiment Agent.
Reads macro indicators, sends a snapshot to Claude Haiku for mood classification.
"""
import os
import json
import logging
from typing import Optional

from anthropic import Anthropic

from lib.contracts import Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD, VALID_ACTIONS
from agents.market_sentiment.connectors import get_market_snapshot, format_snapshot_for_prompt

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are a senior macro analyst at an Indian asset manager. \
Read the market data snapshot and classify the IMMEDIATE intraday market mood \
for Indian equities.

Respond with a STRICT JSON object, no preamble, no markdown fences:
{"action": "BUY"|"SELL"|"HOLD", "confidence": 0.0-1.0, "reason": "<max 100 chars>"}

Rules:
- BUY = market mood is bullish (favors buying)
- SELL = market mood is bearish (favors selling)
- HOLD = mixed signals or genuinely neutral
- VIX > 20 = elevated fear; VIX < 12 = complacency
- Nifty move > 1% is significant; > 2% is large
"""


def _parse_response(raw: str) -> Optional[dict]:
    """Extract a JSON object from the model's response."""
    raw = raw.strip()
    # Some safety in case the model still wraps with code fences
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        # Try to find the first {...} block
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
    reason = str(obj.get("reason", ""))[:120]
    return {"action": action, "confidence": conf, "reason": reason}


def analyze() -> Signal:
    """
    Fetch market snapshot and ask Claude Haiku for a mood classification.
    Returns a market-level Signal (symbol=None).
    """
    snap = get_market_snapshot()
    snapshot_text = format_snapshot_for_prompt(snap)

    metrics = {}
    for k, v in snap.items():
        if v is not None:
            metrics[f"{k}_close"] = v["close"]
            metrics[f"{k}_pct"] = v["pct_change"]

    # If all data unavailable, return neutral
    if not metrics:
        return Signal(
            agent="market_sentiment",
            symbol=None,
            action=ACTION_HOLD,
            confidence=0.0,
            reason="Market data unavailable",
            metrics={},
        )

    try:
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"DATA:\n{snapshot_text}"}],
        )
        raw = message.content[0].text if message.content else ""
        parsed = _parse_response(raw)
        if parsed is None:
            logger.warning(f"Could not parse market sentiment response: {raw[:200]}")
            return Signal(
                agent="market_sentiment",
                symbol=None,
                action=ACTION_HOLD,
                confidence=0.3,
                reason="Could not parse LLM response",
                metrics=metrics,
            )
        return Signal(
            agent="market_sentiment",
            symbol=None,
            action=parsed["action"],
            confidence=parsed["confidence"],
            reason=parsed["reason"],
            metrics=metrics,
        )
    except Exception as e:
        logger.error(f"Market sentiment LLM call failed: {e}", exc_info=True)
        return Signal(
            agent="market_sentiment",
            symbol=None,
            action=ACTION_HOLD,
            confidence=0.0,
            reason=f"Error: {str(e)[:80]}",
            metrics=metrics,
        )
