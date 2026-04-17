"""Project file: src/agents/data_agent.py."""

from typing import Dict, Any
from loguru import logger
from utils.load_data import load_dataset
from utils.retry import retry
from utils.summary import dataset_summary
from utils.data_schema import SchemaValidator
from utils.metrics import agent_metrics
from utils.logger import bind_trace
from utils.exceptions import DataValidationError, DriftDetectedWarning


class DataAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.log = logger.bind(agent="data")

    @agent_metrics("data")
    def run(self, trace_id: str = None) -> Dict[str, Any]:
        log = bind_trace(trace_id).bind(agent="data")

        path = self.config.get("data", {}).get("path", "")
        log.info({
            "event": "data_loading_start",
            "trace_id": trace_id,
            "path": path,
        })
        try:
            df = retry(
                lambda: load_dataset(path),
                attempts=self.config.get("retry", {}).get("attempts", 3),
                delay=self.config.get("retry", {}).get("delay", 1.0),
                agent="data"
            )

            log.info({
                "event": "data_loaded_successfully",
                "trace_id": trace_id,
                "num_rows": len(df),
                "num_columns": len(df.columns),
                "columns": list(df.columns)
            })

        except Exception as e:
            log.error({
                "event": "data_load_failed",
                "trace_id": trace_id,
                "error": str(e)
            })
            raise DataValidationError(f"Failed to load dataset: {e}")
        if df.empty:
            log.error({
                "event": "empty_dataset",
                "trace_id": trace_id
            })
            raise DataValidationError("Dataset empty")
        validator = SchemaValidator(self.config)

        try:
            schema_report = validator.validate(df)

            # Detailed schema validation logs
            log.info({
                "event": "schema_validation_passed",
                "trace_id": trace_id,
                "missing_columns": schema_report.get("missing_columns"),
                "extra_columns": schema_report.get("extra_columns"),
                "dtype_mismatches": schema_report.get("dtype_mismatches")
            })

        except Exception as e:
            log.error({
                "event": "schema_invalid",
                "trace_id": trace_id,
                "error": str(e)
            })
            raise DataValidationError(str(e))

        try:
            drift_report = validator.detect_drift(
                df,
                drift_threshold=self.config.get("schema", {}).get("drift_threshold", 0.25)
            )

            if drift_report:

                # log ALL drift scores per column
                for col, shift in drift_report.items():
                    log.warning({
                        "event": "data_column_drift_detected",
                        "trace_id": trace_id,
                        "column": col,
                        "shift_pct": shift,
                        "severity": (
                            "critical" if shift > 0.5
                            else "high" if shift > 0.3
                            else "medium" if shift > 0.15
                            else "low"
                        )
                    })

                log.warning({
                    "event": "data_drift_summary",
                    "trace_id": trace_id,
                    "num_columns_drifted": len(drift_report),
                    "drift_details": drift_report
                })

                # strict mode raises error
                if self.config.get("schema", {}).get("strict", False):
                    raise DriftDetectedWarning(
                        f"Critical drift detected in columns: {list(drift_report.keys())}"
                    )

        except DriftDetectedWarning as dw:
            log.error({
                "event": "drift_critical",
                "trace_id": trace_id,
                "error": str(dw)
            })
            raise
        summary = dataset_summary(df)

        log.info({
            "event": "dataset_summary_computed",
            "trace_id": trace_id,
            "row_count": len(df),
            "top_campaigns_by_spend": list(summary.get("top_campaigns_by_spend", {}).keys()),
            "spend_range": [
                summary.get("min_spend"), 
                summary.get("max_spend")
            ],
            "ctr_range": [
                summary.get("min_ctr"), 
                summary.get("max_ctr")
            ]
        })

        log.info({
            "event": "data_agent_complete",
            "trace_id": trace_id,
            "summary_keys": list(summary.keys())
        })

        return {"df": df, "summary": summary}
