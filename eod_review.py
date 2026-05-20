"""
End-of-day review job (v0.3.0).

Runs daily after market close. Scans the Signals sheet and fills in any
newly-knowable outcome columns across 4 horizons (eod, 1d, 3d, 5d).
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

    logger.info("Starting EOD review (multi-horizon outcome closure)...")
    result = close_pending_trades()
    logger.info(f"EOD review summary: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
