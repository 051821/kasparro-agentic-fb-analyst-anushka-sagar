# src/agents/data_agent.py
import json
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
        log.info(json.dumps({"event": "loading_dataset", "path": path}))

        try:
            df = retry(
                lambda: load_dataset(path),
                attempts=self.config.get("retry", {}).get("attempts", 3),
                delay=self.config.get("retry", {}).get("delay", 1.0),
                agent="data"
            )
        except Exception as e:
            log.error(json.dumps({"event": "data_load_failed", "error": str(e)}))
            raise

        if df.empty:
            log.error(json.dumps({"event": "empty_dataset"}))
            raise DataValidationError("Dataset empty")
        validator = SchemaValidator(self.config)

        try:
            validator.validate(df)
        except Exception as e:
            log.error(json.dumps({"event": "schema_invalid", "error": str(e)}))
            raise DataValidationError(str(e))

        try:
            drift = validator.detect_drift(
                df,
                drift_threshold=self.config.get("schema", {}).get("drift_threshold", 0.25)
            )

            if drift:
                log.warning(json.dumps({"event": "drift_detected", "details": drift}))

                if self.config.get("schema", {}).get("strict", False):
                    raise DriftDetectedWarning("Critical drift detected")

        except DriftDetectedWarning as dw:
            log.error(json.dumps({"event": "drift_critical", "error": str(dw)}))
            raise


        summary = dataset_summary(df)

        log.info(json.dumps({
            "event": "dataset_summary_computed",
            "top_campaigns": list(summary.get("top_campaigns_by_spend", {}).keys())
        }))

        return {"df": df, "summary": summary}
