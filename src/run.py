import sys
import os
import yaml
from utils.logger import configure_logging, logger
from orchestrator.agent_control import AgentController

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config", "config.yml")


def load_config():
    """Load config/config.yml safely."""
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print('Usage: python src/run.py "Analyze ROAS drop in last 7 days"')
        sys.exit(1)

    query = sys.argv[1]

    # Load config
    config = load_config()
    log_dir = config["paths"].get("log_dir", "logs")
    configure_logging(log_dir)        

    run_log = logger.bind(agent="run")
    run_log.info(f"Received query: {query}")

    controller = AgentController(config)

    try:
        controller.run(query)
        run_log.info("Run completed successfully.")
    except Exception as e:
        run_log.error(f"Run failed due to error: {e}")
        raise  

    print("\nAnalysis complete!")
    print("➡ reports/insights.json")
    print("➡ reports/creatives.json")
    print("➡ reports/trace_meta.json")
    print()


if __name__ == "__main__":
    main()

