import sys
import os
import yaml
from utils.logger import configure_logging, logger
from orchestrator.agent_control import AgentController

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python src/run.py "Analyze ROAS drop in last 7 days"')
        sys.exit(1)

    query = sys.argv[1]

    # Load config
    config_path = os.path.join(PARENT_DIR, "config", "config.yml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Configure logging
    log_dir = config.get("paths", {}).get("log_dir", "logs")
    configure_logging(log_dir=log_dir)

    run_log = logger.bind(agent="run")
    run_log.info(f"Received query: {query}")

    controller = AgentController(config)

    try:
        controller.run(query)
        run_log.info("Run completed successfully.")
    except Exception as e:
        run_log.error(f"Run failed due to error: {e}")
        raise

    print("Analysis complete. See reports/insights.json, reports/creatives.json, and reports/report.md.")


if __name__ == "__main__":
    main()
