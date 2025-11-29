from loguru import logger
import pandas as pd
from typing import Dict, Any


class SchemaValidator:

    def __init__(self, config: Dict[str, Any]):
        self.schema_version = config.get("schema", {}).get("version", 1)
        self.expected_columns = set(config.get("schema", {}).get("expected_columns", []))
        self.log = logger.bind(agent="schema")

    def validate(self, df: pd.DataFrame) -> None:
        self.log.info(f"Validating dataset against schema version {self.schema_version}...")

        actual_columns = set(df.columns)
        missing = self.expected_columns - actual_columns
        extra = actual_columns - self.expected_columns

        if missing:
            self.log.error(f"Missing required columns: {missing}")
            raise ValueError(f"Critical schema error: missing columns {missing}")

        if extra:
            self.log.warning(f"Dataset contains extra unexpected columns: {extra}")

        self.log.info("Schema validation successful.")

    def detect_drift(self, df: pd.DataFrame, drift_threshold: float = 0.25) -> None:
        self.log.info("Running drift detection...")

        numeric_cols = ["spend", "impressions", "clicks", "revenue", "ctr", "roas"]

        if "date" not in df.columns:
            self.log.warning("No `date` column found — drift detection skipped.")
            return

        mid = df["date"].median()

        before = df[df["date"] <= mid]
        after = df[df["date"] > mid]

        for col in numeric_cols:
            if col not in df.columns:
                continue

            before_mean = before[col].mean()
            after_mean = after[col].mean()

            if before_mean == 0:
                continue

            shift = abs((after_mean - before_mean) / before_mean)

            if shift > drift_threshold:
                self.log.warning(
                    f"Drift detected in `{col}`: {shift*100:.1f}% shift"
                )
            else:
                self.log.debug(f"No drift in `{col}`: {shift*100:.1f}%")
