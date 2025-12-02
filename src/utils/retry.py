# src/utils/retry.py
import time
import random
from typing import Callable, Any, Tuple
from loguru import logger


class RetryLimitError(Exception):
    """Raised when retry attempts are exhausted."""
    pass


def retry(
    operation: Callable[[], Any],
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.2,
    retry_on: Tuple[type, ...] = (Exception,),
    agent: str = "retry"
) -> Any:

    log = logger.bind(agent=agent)
    last_error = None

    for i in range(1, attempts + 1):
        try:
            log.debug(f"Attempt {i}/{attempts}")
            return operation()

        except retry_on as e:
            last_error = e

            if i == attempts:
                log.error(f"Retry failed after {attempts} attempts: {e}")
                raise RetryLimitError(str(e)) from e

            sleep = delay * (backoff ** (i - 1))
            sleep += random.uniform(-jitter, jitter) * sleep
            sleep = max(0.0, sleep)

            log.warning(f"Attempt {i} failed: {e} | retrying in {sleep:.2f}s")
            time.sleep(sleep)

    raise RetryLimitError(str(last_error))

