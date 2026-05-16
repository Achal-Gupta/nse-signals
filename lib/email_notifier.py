"""
Email notifier via Gmail SMTP.
Sends HTML email with the day's signals.
"""
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from lib.contracts import Verdict, ACTION_BUY, ACTION_SELL, ACTION_HOLD

logger = logging.getLogger(__name__)


def _action_emoji(action: str) -> str:
    return {ACTION_BUY: "🟢", ACTION_SELL: "🔴", ACTION_HOLD: "⚪"}.get(action, "❓")


def _build_html(verdicts: List[Verdict], errors: List[str]) -> tuple[str, str]:
    """Returns (subject, html_body)."""
    if not verdicts and not errors:
        return ("📊 NSE Signals · no data", "<p>No data generated this run.</p>")

    buys = [v for v in verdicts if v.action == ACTION_BUY]
    sells = [v for v in verdicts if v.action == ACTION_SELL]
    holds = [v for v in verdicts if v.action == ACTION_HOLD]

    timestamp = verdicts[0].timestamp_ist if verdicts else ""
    subject = f"📊 NSE Signals · {len(buys)} BUY · {len(sells)} SELL · {timestamp[-8:-3] if timestamp else ''}"

    market_html = ""
    if verdicts:
        m = verdicts[0].market_signal
        market_html = (
            f"<p><b>Market:</b> {_action_emoji(m.action)} {m.action} "
            f"({int(m.confidence * 100)}%) — {m.reason}</p>"
        )

    rows_html = ""
    for v in buys + sells:
        rows_html += (
            f"<div style='margin: 12px 0; padding: 10px; border-left: 4px solid "
            f"{'#22c55e' if v.action == ACTION_BUY else '#ef4444'};'>"
            f"<b>{_action_emoji(v.action)} {v.symbol} — {v.action} "
            f"({int(v.confidence * 100)}%)</b><br>"
            f"• Technical: {v.technical_signal.reason}<br>"
            f"• Sentiment: {v.sentiment_signal.reason}"
            f"</div>"
        )

    holds_html = ""
    if holds:
        symbols = ", ".join(v.symbol.replace(".NS", "") for v in holds)
        holds_html = f"<p>⚪ <b>HOLDS ({len(holds)}):</b> {symbols}</p>"

    errors_html = ""
    if errors:
        errors_list = "".join(f"<li>{e}</li>" for e in errors)
        errors_html = f"<p style='color:#b91c1c;'><b>Errors:</b><ul>{errors_list}</ul></p>"

    body = f"""
    <html><body style='font-family: -apple-system, sans-serif;'>
    {market_html}
    {rows_html}
    {holds_html}
    {errors_html}
    <hr>
    <p style='color:#6b7280; font-size:12px;'>NSE Signals v0.1.0 · {timestamp}</p>
    </body></html>
    """
    return subject, body


def send_email(verdicts: List[Verdict], errors: List[str]) -> None:
    """
    Send signals email. Reads SMTP credentials from environment:
      GMAIL_USER, GMAIL_APP_PASSWORD, ALERT_EMAIL_TO
    """
    user = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    to_addr = os.environ["ALERT_EMAIL_TO"]

    subject, html_body = _build_html(verdicts, errors)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())

    logger.info(f"Email sent: {subject}")
