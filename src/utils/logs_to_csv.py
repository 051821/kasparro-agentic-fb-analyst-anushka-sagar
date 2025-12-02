import os
import re
import yaml
import glob
import pandas as pd


def load_config():
    """Load config.yml safely from root."""
    root_path = os.path.abspath(os.getcwd())
    config_path = os.path.join(root_path, "config", "config.yml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"config.yml not found at {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


LOG_PATTERN = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| '
    r'(?P<level>\w+) \| '
    r'(?P<agent>\w+) \| '
    r'(?P<message>.*)$'
)


def parse_line(line):
    match = LOG_PATTERN.match(line.strip())
    return match.groupdict() if match else None


def collect():
    """Convert simple logs → CSV with auto path detection."""

    config = load_config()

    log_dir = config["paths"]["log_dir"]
    metrics_dir = config["paths"]["metrics_dir"]

    # Ensure folders exist
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)

    output_csv = os.path.join(metrics_dir, "metrics_dashboard.csv")

    rows = []

    # Read .log files only
    for fp in glob.glob(os.path.join(log_dir, "*.log")):
        with open(fp, "r", encoding="utf-8") as file:
            for line in file:
                parsed = parse_line(line)
                if parsed:
                    rows.append(parsed)

    if not rows:
        print("⚠ No log lines matched.")
        return None

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)

    print(f"✅ CSV saved at: {output_csv}")
    print(df.head())

    return output_csv


if __name__ == "__main__":
    collect()
