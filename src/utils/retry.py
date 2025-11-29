import time
from typing import Callable , Any
from loguru import logger

def retry(operation : Callable, attempts : int = 3, delay : float = 1.0 , agent : str = "llm") -> Any:
    Last_exp = None
    log = logger.bind(agent=agent)
    for  a in range(1, attempts + 1):
        try:
            log.debug(f"Attempts {a}/{attempts}")
            return operation()
        except Exception as e:
            last_exp = e
            log.warning(f"Attempt {a} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    log.error(f"All {attempts} attempts failed. Last error: {last_exception}")
    raise last_exp           