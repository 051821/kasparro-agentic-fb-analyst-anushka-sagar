# src/utils/data_schema.py
from loguru import logger
import pandas as pd
from typing import Dict, Any, List

class SchemaValidator:
    def __init__(self, config: Dict[str, Any]):
        self.schema_version = config.get("schema", {}).get("version", 1)
        self.expected_columns = set(config.get("schema", {}).get("expected_columns", []))
        self.strict = config.get("schema", {}).get("strict", False)
        self.log = logger.bind(agent="schema")

    def validate(self, df: pd.DataFrame) -> None:
        self.log.info(f"Validating dataset against schema v{self.schema_version}")
        actual = set(df.columns)
        missing = self.expected_columns - actual
        extra = actual - self.expected_columns
        if missing:
            self.log.error({"event": "missing_columns", "missing": list(missing)})
            raise ValueError(f"Missing required columns: {missing}")
        if extra:
            self.log.warning({"event": "extra_columns", "extra": list(extra)})
            if self.strict:
                raise ValueError(f"Unexpected extra columns: {extra}")
        self.log.info("Schema validation passed")

    def detect_drift(self, df: pd.DataFrame, drift_threshold: float = 0.25) -> List[Dict[str, Any]]:
        self.log.info("Running drift detection")
        numeric_cols = [c for c in ["spend", "impressions", "clicks", "revenue", "ctr", "roas"] if c in df.columns]
        if "date" not in df.columns or df["date"].isna().all():
            self.log.warning("No date column or all dates missing; skipping drift detection")
            return []
        mid = df["date"].median()
        before = df[df["date"] <= mid]
        after = df[df["date"] > mid]
        issues = []
        for col in numeric_cols:
            before_mean = before[col].mean() if not before.empty else 0.0
            after_mean = after[col].mean() if not after.empty else 0.0
            if before_mean == 0:
                continue
            shift = abs((after_mean - before_mean) / before_mean)
            if shift > drift_threshold:
                issues.append({"column": col, "shift": shift})
                self.log.warning({"event": "drift", "column": col, "shift_pct": shift * 100.0})
            else:
                self.log.debug({"event": "no_drift", "column": col, "shift_pct": shift * 100.0})
        return issues
