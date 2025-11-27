from loguru import logger
from pathlib import Path
import os


def configure_logging(log_dir: str) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(log_dir, "run.log")
    logger.add(log_path, rotation="1 MB", backtrace=True, diagnose=True)
    logger.info("Logger initialized")


__all__ = ["logger", "configure_logging"]
