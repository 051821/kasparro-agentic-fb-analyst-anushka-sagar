# src/run.py
import sys
import os
import yaml
import json
from utils.logger import configure_logging, bind_trace
from orchestrator.agent_control import AgentController

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config", "config.yml")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    if len(sys.argv) < 2:
        print('Usage: python src/run.py "Analyze ROAS drop in last 7 days"')
        sys.exit(1)

    query = sys.argv[1]
    config = load_config()

    log_dir = config["paths"].get("log_dir", "logs")
    configure_logging()

    run_log = bind_trace().bind(agent="run")
    run_log.info(json.dumps({"event": "received_query", "query": query}))

    controller = AgentController(config)
    try:
        res = controller.run(query)
        run_log.info(json.dumps({"event": "run_completed", "trace_id": res.get("trace_id")}))
    except Exception as e:
        run_log.info(json.dumps({"event": "run_failed", "error": str(e)}))
        raise

    print("\nAnalysis complete!")
    print("➡ reports/insights.json")
    print("➡ reports/creatives.json")
    print("➡ reports/trace_meta.json")
    print("➡ reports/report.md")

if __name__ == "__main__":
    main()

