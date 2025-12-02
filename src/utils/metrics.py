# src/utils/metrics.py
import time
import functools
import traceback
from uuid import uuid4
from typing import Any, Callable, Optional, Dict

from loguru import logger
from utils.logger import bind_trace


def _size_meta(obj) -> Dict[str, int]:
    """Estimate size of data structures for logging."""
    meta = {}
    try:
        if hasattr(obj, "shape"):
            meta["rows"] = obj.shape[0]
        elif isinstance(obj, (list, tuple, set, dict)):
            meta["len"] = len(obj)
    except Exception:
        pass
    return meta


def agent_metrics(agent_name: str):
    """
    Decorator that logs:
    - start
    - end
    - duration
    - input size
    - output size
    - trace_id
    """

    def decorator(fn: Callable):

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            trace_id = kwargs.get("trace_id") or str(uuid4())
            log = bind_trace(trace_id).bind(agent=agent_name, fn=fn.__name__)

            start = time.time()
            log.info(f"[START] {fn.__name__}")

            # Input size metadata
            for idx, a in enumerate(args):
                log.debug(f"input arg{idx} size: {_size_meta(a)}")
            for key, val in kwargs.items():
                if key != "trace_id":
                    log.debug(f"input {key} size: {_size_meta(val)}")

            try:
                result = fn(*args, **kwargs)
                end = time.time()
                duration = round((end - start) * 1000, 2)

                log.info(f"[END] {fn.__name__} | duration={duration}ms")
                log.debug(f"output size: {_size_meta(result)}")

                return result

            except Exception as e:
                log.error(f"[ERROR] {fn.__name__} | {str(e)}")
                log.error(traceback.format_exc())
                raise

        return wrapper

    return decorator
