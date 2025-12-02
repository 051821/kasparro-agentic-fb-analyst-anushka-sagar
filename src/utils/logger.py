from loguru import logger
from pathlib import Path
import os
from typing import Any, Optional

DEFAULT_ROTATION = "2 MB"


def is_pytest_running() -> bool:
    """Detect pytest reliably using environment variable."""
    return "PYTEST_CURRENT_TEST" in os.environ


def configure_logging(base_log_dir: str) -> None:
    """
    Configure logging.
    Run mode → logs/run/
    Test mode → logs/tests/
    """

    # Auto-select correct folder
    if is_pytest_running():
        log_dir = os.path.join(base_log_dir, "tests")
    else:
        log_dir = os.path.join(base_log_dir, "run")

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Reset all previous handlers
    logger.remove()

    # Main run log
    logger.add(
        os.path.join(log_dir, "run.log"),
        rotation=DEFAULT_ROTATION,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level}</level> | {extra[agent]} | {message}"
    )

    # Per-agent logs
    agents = ["insight", "plan", "evaluate", "data", "creative", "schema"]

    for agent in agents:
        logger.add(
            os.path.join(log_dir, f"{agent}.log"),
            rotation=DEFAULT_ROTATION,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            level="DEBUG",
            filter=lambda record, a=agent: record["extra"].get("agent") == a,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level}</level> | {extra[agent]} | {message}"
        )

    logger.bind(agent="run").info(f"Logger initialized in: {log_dir}")


def bind_trace(trace_id: Optional[str] = None, **extras) -> Any:
    bound = logger
    if trace_id:
        bound = bound.bind(trace_id=trace_id)
    if extras:
        bound = bound.bind(**extras)
    return bound
