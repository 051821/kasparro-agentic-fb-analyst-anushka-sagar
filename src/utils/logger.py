# src/utils/logger.py
from loguru import logger
from pathlib import Path
import os
import uuid

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[agent]} | {message}"

AGENTS = [
    "run", "plan", "data", "insight",
    "evaluate", "creative", "schema", "retry"
]


def is_pytest_running() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_ROOT = PROJECT_ROOT / "logs"


def configure_logging() -> None:
    mode = "tests" if is_pytest_running() else "run"
    log_dir = LOG_ROOT / mode
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    master_path = log_dir / "run.log"
    logger.add(
        master_path,
        format=LOG_FORMAT,
        level="DEBUG",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    # PER-AGENT LOGS
    for agent in AGENTS:
        path = log_dir / f"{agent}.log"
        logger.add(
            path,
            format=LOG_FORMAT,
            level="DEBUG",
            enqueue=True,
            backtrace=False,
            diagnose=False,
            filter=lambda record, a=agent: record["extra"].get("agent") == a
        )

    logger.bind(agent="run").info(f"Logger initialized → {log_dir}")


def bind_trace(trace_id: str = None):
    """Attach a trace_id to all logs for this run."""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    return logger.bind(trace_id=trace_id)
