"""Project file: src/utils/retry.py."""

import time
import random
from loguru import logger


class RetryLimitError(Exception):
    pass


def retry(
    operation,
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.2,
    retry_on=(Exception,),
    agent: str = "retry",
):
    

    log = logger.bind(agent=agent)
    current_delay = delay

    for i in range(1, attempts + 1):
        try:
            log.debug(f"Attempt {i}/{attempts}")
            return operation()

        except retry_on as e:
            if i == attempts:
                log.error(f"Retry failed after {attempts} attempts: {e}")
                raise RetryLimitError(str(e)) from e

            sleep = max(0.0, current_delay + random.uniform(-jitter, jitter) * current_delay)
            log.warning(f"Attempt {i} failed: {e} | retrying in {sleep:.2f}s")
            time.sleep(sleep)
            current_delay *= backoff
