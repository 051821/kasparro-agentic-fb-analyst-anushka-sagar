# src/run.py
import sys
import os
import yaml
import json
import traceback

from utils.logger import configure_logging, bind_trace
from orchestrator.agent_control import AgentController

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config", "config.yml")


# -------------------------------------------------
# CONFIG LOADER WITH LOGGING
# -------------------------------------------------
def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        sys.exit(1)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            return cfg
    except Exception as e:
        print("ERROR: Failed to load config.yml")
        print(str(e))
        sys.exit(1)


# -------------------------------------------------
# MAIN PIPELINE ENTRYPOINT (V2 LOGGING)
# -------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print('Usage: python src/run.py "Analyze ROAS drop in last 7 days"')
        sys.exit(1)

    query = sys.argv[1]

    # Load configuration
    config = load_config()

    # Initialize logging
    configure_logging()
    run_log = bind_trace().bind(agent="run")

    run_log.info({
        "event": "run_invocation_start",
        "query": query,
        "config_paths": config.get("paths", {})
    })

    # Create controller
    controller = AgentController(config)

    # Run the pipeline + capture exceptions
    try:
        run_log.info(json.dumps({
            "event": "received_query",
            "query": query
        }))

        res = controller.run(query)

        run_log.info(json.dumps({
            "event": "run_completed",
            "trace_id": res.get("trace_id")
        }))

    except Exception as e:
        run_log.error({
            "event": "run_failed",
            "error": str(e),
            "stack_trace": traceback.format_exc()
        })
        raise  # still raise for visibility

    # Output artifacts notification
    run_log.info({
        "event": "output_artifacts_created",
        "files": [
            "reports/insights.json",
            "reports/creatives.json",
            "reports/trace_meta.json",
            "reports/report.md"
        ]
    })

    print("\n✅ Analysis complete!")
    print("➡ reports/insights.json")
    print("➡ reports/creatives.json")
    print("➡ reports/trace_meta.json")
    print("➡ reports/report.md")


if __name__ == "__main__":
    main()
