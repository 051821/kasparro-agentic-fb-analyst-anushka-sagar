# src/utils/metrics.py
import os
import csv
import time
from functools import wraps


METRICS_DIR = "logs/metrics"
RUN_FILE = os.path.join(METRICS_DIR, "run_metrics.csv")
TEST_FILE = os.path.join(METRICS_DIR, "test_metrics.csv")


def is_pytest():
    return "PYTEST_CURRENT_TEST" in os.environ


def _ensure_files():
    os.makedirs(METRICS_DIR, exist_ok=True)

    # Choose correct file depending on mode
    target_file = TEST_FILE if is_pytest() else RUN_FILE

    if not os.path.exists(target_file):
        with open(target_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "trace_id",
                "agent",
                "function",
                "duration_ms",
                "input_size",
                "output_size",
                "confidence",
                "error_message"
            ])

    return target_file


def _size(obj):
    if obj is None:
        return 0
    if isinstance(obj, (str, bytes)):
        return len(obj)
    if hasattr(obj, "__len__"):
        return len(obj)
    return 1


def _write_row(row):
    target_file = _ensure_files()

    with open(target_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def agent_metrics(agent_name: str):
    """
    Decorator wrapping every agent function to log metrics.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            trace_id = kwargs.get("trace_id", "")

            input_size = sum(_size(a) for a in args)
            input_size += sum(_size(v) for v in kwargs.values())

            error_message = ""
            confidence = ""
            result = None
            caught_exception = None   # <-- FIX: capture exception safely

            try:
                result = fn(*args, **kwargs)

                # Extract confidence if present
                if isinstance(result, dict):
                    confidence = result.get("confidence", "")
                elif isinstance(result, list) and result and isinstance(result[0], dict):
                    confidence = result[0].get("confidence", "")

                output_size = _size(result)

            except Exception as e:
                caught_exception = e           # <-- FIX: store exception
                error_message = str(e)
                result = None
                output_size = 0

            end = time.time()
            duration_ms = round((end - start) * 1000, 2)
            timestamp = time.strftime("%d-%m-%Y %H:%M:%S")

            # Log the metrics
            row = [
                timestamp,
                trace_id,
                agent_name,
                fn.__name__,
                duration_ms,
                input_size,
                output_size,
                confidence,
                error_message
            ]

            _write_row(row)

            # If an exception was caught, re-raise it properly
            if caught_exception is not None:
                raise caught_exception   # <-- FIX: correct re-raise

            return result

        return wrapper
    return decorator
