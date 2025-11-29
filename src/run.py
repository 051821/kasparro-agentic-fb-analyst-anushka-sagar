import sys
import os
import yaml

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from utils.logger import configure_logging, logger
from orchestrator.agent_control import AgentController


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python src/run.py "Analyze ROAS drop in last 7 days"')
        sys.exit(1)

    query = sys.argv[1]

    # Load config
    with open(os.path.join(PARENT_DIR, "config", "config.yml"), "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    log_dir = config.get("paths", {}).get("log_dir", "logs")
    configure_logging(log_dir=log_dir)

    logger.bind(agent="run").info(f"Received query: {query}")
    controller = AgentController(config)

    try:
        controller.run(query)
        logger.bind(agent="run").info("Run completed successfully.")
    except Exception as e:
        logger.bind(agent="run").error(f"Run failed due to error: {e}")
        raise

    print("Analysis complete. See reports/insights.json, reports/creatives.json, and reports/report.md.")


if __name__ == "__main__":
    main()
