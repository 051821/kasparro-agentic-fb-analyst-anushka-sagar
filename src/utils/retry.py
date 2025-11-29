import time
from typing import Callable, Any
from loguru import logger


def retry(operation: Callable, attempts: int = 3, delay: float = 1.0, agent: str = "llm") -> Any:
    log = logger.bind(agent=agent)

    for a in range(1, attempts + 1):
        try:
            log.debug(f"Attempts {a}/{attempts}")
            return operation()
        except Exception as e:
            log.warning(f"Attempt {a} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

    try:
        return operation()
    except Exception as final_error:
        log.error(f"All {attempts} attempts failed. Last error: {final_error}")
        raise final_error
