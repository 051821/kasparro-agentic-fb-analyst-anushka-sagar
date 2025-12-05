# src/utils/data_schema.py
import numpy as np
import pandas as pd
from typing import Dict, Any
from loguru import logger
from utils.exceptions import DataValidationError, DriftDetectedWarning


class SchemaValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.schema_cfg = self.config.get("schema", {})
        self.expected_columns = self.schema_cfg.get("expected_columns", [])
        self.strict = self.schema_cfg.get("strict", False)

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        log = logger.bind(agent="schema")

        df_cols = set(df.columns)
        expected_cols = set(self.expected_columns)

        missing = list(expected_cols - df_cols)
        extra = list(df_cols - expected_cols)
        dtype_mismatches = []
        expected_dtypes = self.schema_cfg.get("expected_dtypes", {})

        for col, exp_type in expected_dtypes.items():
            if col in df.columns:
                actual = df[col].dtype
                if str(actual) != str(exp_type):
                    dtype_mismatches.append({
                        "column": col,
                        "expected": exp_type,
                        "actual": str(actual)
                    })
        null_issues = {}
        null_threshold = self.schema_cfg.get("null_threshold", 0.5)
        for col in df.columns:
            null_ratio = df[col].isna().mean()
            if null_ratio > null_threshold:
                null_issues[col] = round(null_ratio, 3)

        # Detailed log
        log.info({
            "event": "schema_validation_report",
            "missing_columns": missing,
            "extra_columns": extra,
            "dtype_mismatches": dtype_mismatches,
            "null_ratios_above_threshold": null_issues
        })

        if self.strict and missing:
            raise DataValidationError(f"Missing required columns: {missing}")
        if dtype_mismatches:
            log.warning({
                "event": "schema_dtype_mismatch_detected",
                "details": dtype_mismatches
            })

        return {
            "missing_columns": missing,
            "extra_columns": extra,
            "dtype_mismatches": dtype_mismatches,
            "null_issues": null_issues
        }
    def detect_drift(self, df: pd.DataFrame, drift_threshold: float = 0.25) -> Dict[str, float]:
        log = logger.bind(agent="schema")

        drift_report = {}
        baseline_path = self.schema_cfg.get("baseline_path", "schema_baseline.json")

        try:
            import json, os
            if os.path.exists(baseline_path):
                with open(baseline_path, "r") as f:
                    baseline = json.load(f)
            else:
                baseline = {}
        except:
            baseline = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            new_mean = float(df[col].mean())
            old_mean = baseline.get(col, new_mean)

            if old_mean != 0:
                shift_pct = abs(new_mean - old_mean) / abs(old_mean)
            else:
                shift_pct = 0
            baseline[col] = new_mean
            if shift_pct > drift_threshold:
                drift_report[col] = round(shift_pct, 4)
            log.info({
                "event": "drift_score",
                "column": col,
                "new_mean": new_mean,
                "old_mean": old_mean,
                "shift_pct": shift_pct
            })
        try:
            with open(baseline_path, "w") as f:
                json.dump(baseline, f, indent=2)
        except:
            pass

        if drift_report and self.strict:
            raise DriftDetectedWarning(f"Critical drift: {drift_report}")

        return drift_report
