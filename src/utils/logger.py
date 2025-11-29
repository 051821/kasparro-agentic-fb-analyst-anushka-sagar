from loguru import logger
from pathlib import Path
import os


def configure_logging(log_dir: str) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Log file paths
    run_log = os.path.join(log_dir, "run.log")
    insight_log = os.path.join(log_dir, "insight.log")
    plan_log = os.path.join(log_dir, "plan.log")
    evaluate_log = os.path.join(log_dir, "evaluate.log")
    data_log = os.path.join(log_dir, "data.log")            
    creative_log = os.path.join(log_dir, "creative.log")    
    schema_log = os.path.join(log_dir, "schema.log")
    logger.add(
        run_log,
        rotation="1 MB",
        backtrace=True,
        diagnose=True,
    )

    logger.add(
        insight_log,
        rotation="1 MB",
        backtrace=True,
        diagnose=True,
        filter=lambda r: r["extra"].get("agent") == "insight"
    )
    logger.add(
        evaluate_log,
        rotation="1 MB",
        backtrace=True,
        diagnose=True,
        filter=lambda r: r["extra"].get("agent") == "evaluate"
    )
    logger.add(
        plan_log,
        rotation="1 MB",
        backtrace=True,
        diagnose=True,
        filter=lambda r: r["extra"].get("agent") == "plan"
    )
    logger.add(
        data_log,
        rotation="1 MB",
        backtrace=True,
        diagnose=True,
        filter=lambda r: r["extra"].get("agent") == "data"
    )
    logger.add(
        creative_log,
        rotation="1 MB",
        backtrace=True,
        diagnose=True,
        filter=lambda r: r["extra"].get("agent") == "creative"
    )
    logger.add(
        schema_log,
        rotation="1 MB",
        backtrace=True,
        diagnose=True,
        filter=lambda r: r["extra"].get("agent") == "schema"
    )


    logger.bind(agent="run").info("Logger initialized")


__all__ = ["logger", "configure_logging"]

