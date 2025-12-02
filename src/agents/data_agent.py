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
        self.config = config
        self.log = logger.bind(agent="data")

    @agent_metrics("data")
    def run(self, trace_id: str = None) -> Dict[str, Any]:
        log = bind_trace(trace_id).bind(agent="data")
        path = self.config["data"]["path"]
        log.info({"event": "loading_dataset", "path": path})

        try:
            df = retry(lambda: load_dataset(path),
                       attempts=self.config.get("retry", {}).get("attempts", 3),
                       delay=self.config.get("retry", {}).get("delay", 1.0),
                       backoff=2.0, jitter=0.1, agent="data")
        except Exception as e:
            log.error({"event": "data_load_failed", "error": str(e)})
            raise
        if df.empty:
            log.error({"event": "empty_dataset"})
            raise DataValidationError("Dataset empty")

        # Validate schema
        validator = SchemaValidator(self.config)
        try:
            validator.validate(df)
        except Exception as e:
            log.error({"event": "schema_invalid", "error": str(e)})
            raise DataValidationError(str(e))
        try:
            drift_issues = validator.detect_drift(df, drift_threshold=self.config.get("schema", {}).get("drift_threshold", 0.25))
            if drift_issues:
                log.warning({"event": "drift_detected", "details": drift_issues})
                if self.config.get("schema", {}).get("strict", False):
                    raise DriftDetectedWarning("Critical drift detected")
        except DriftDetectedWarning as dw:
            log.error({"event": "drift_critical", "error": str(dw)})
            raise
        except Exception:
            pass

        summary = dataset_summary(df)
        log.info({"event": "dataset_summary_computed", "top_campaigns": list(summary.get("top_campaigns_by_spend", {}).keys())})
        return {"df": df, "summary": summary}
