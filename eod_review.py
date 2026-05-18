"""
End-of-day review job. Runs once per trading day after market close.
Closes pending paper trades from the previous trading day.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.secret_validator import verify_secrets, SecretError
from lib.paper_trader import close_pending_trades


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("eod_review")


def main() -> int:
    try:
        verify_secrets()
    except SecretError as e:
        logger.error(str(e))
        return 1

    logger.info("Starting end-of-day paper trade review...")
    close_pending_trades(lookback_days=1)
    logger.info("EOD review complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
