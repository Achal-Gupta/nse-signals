"""
Secret validator. Fails fast at startup if any required env var is missing or empty.
Lesson learned from v0.1.0: silent empty-secret bugs are painful to debug.
"""
import os
import logging

logger = logging.getLogger(__name__)

REQUIRED_SECRETS = [
    "ANTHROPIC_API_KEY",
    "GMAIL_USER",
    "GMAIL_APP_PASSWORD",
    "ALERT_EMAIL_TO",
    "GOOGLE_SHEETS_CREDS_JSON",
    "GOOGLE_SHEET_ID",
]


class SecretError(RuntimeError):
    pass


def verify_secrets() -> None:
    """Raises SecretError if any required env var is missing or empty/whitespace."""
    missing = []
    blank = []

    for name in REQUIRED_SECRETS:
        value = os.environ.get(name)
        if value is None:
            missing.append(name)
        elif not value.strip():
            blank.append(name)

    issues = []
    if missing:
        issues.append(f"Missing: {', '.join(missing)}")
    if blank:
        issues.append(f"Blank/whitespace: {', '.join(blank)}")

    if issues:
        msg = "Secret validation failed. " + " | ".join(issues)
        logger.error(msg)
        raise SecretError(msg)

    logger.info(f"All {len(REQUIRED_SECRETS)} required secrets present")
