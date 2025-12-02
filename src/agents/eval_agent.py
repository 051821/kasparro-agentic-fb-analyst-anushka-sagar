from typing import Dict, Any, List
import pandas as pd
from loguru import logger
from utils.schemas import Hypothesis, EvaluatedHypothesis
from utils.validate import filter_significant_segments, global_before_after_split
from utils.metrics import agent_metrics
from utils.logger import bind_trace

log = logger.bind(agent="evaluate")

class EvalAgent:
    def __init__(self):
        self.log = log

    @agent_metrics("evaluate")
    def evaluate(self, df: pd.DataFrame, hypotheses: List[Hypothesis], thresholds: Dict[str, Any], trace_id: str = None) -> List[EvaluatedHypothesis]:
        lg = bind_trace(trace_id).bind(agent="evaluate")
        lg.info({"event": "evaluation_start", "hypotheses": len(hypotheses)})
        try:
            df_filtered = filter_significant_segments(df, thresholds)
            lg.debug({"event": "filtering", "rows_after": int(df_filtered.shape[0])})
            before, after = global_before_after_split(df_filtered)
        except Exception as e:
            lg.error({"event": "preparation_failed", "error": str(e)})
            raise

        def safe_div(a,b):
            return float(a)/float(b) if b and b != 0 else 0.0

        roas_b = safe_div(before["revenue"].sum(), before["spend"].sum())
        roas_a = safe_div(after["revenue"].sum(), after["spend"].sum())
        ctr_b = safe_div(before["clicks"].sum(), before["impressions"].sum())
        ctr_a = safe_div(after["clicks"].sum(), after["impressions"].sum())

        adapt = {}
        if len(df_filtered) > 50:
            spend_cv = (df_filtered["spend"].std() / (df_filtered["spend"].mean() + 1e-9))
            adapt["roas_drop_pct"] = thresholds.get("roas_drop_pct", 0.25) * (1 + spend_cv)
            adapt["ctr_drop_pct"] = thresholds.get("ctr_drop_pct", 0.20) * (1 + spend_cv)
        else:
            adapt["roas_drop_pct"] = thresholds.get("roas_drop_pct", 0.25)
            adapt["ctr_drop_pct"] = thresholds.get("ctr_drop_pct", 0.20)

        roas_change = (roas_a - roas_b) / roas_b if roas_b else (roas_a - roas_b)
        ctr_change = (ctr_a - ctr_b) / ctr_b if ctr_b else (ctr_a - ctr_b)
        lg.debug({"event":"computed", "roas_b":roas_b, "roas_a":roas_a, "roas_change":roas_change, "ctr_change":ctr_change, "adapt":adapt})

        evaluated = []
        for hyp in hypotheses:
            try:
                conf = 0.5
                if roas_change < -adapt["roas_drop_pct"]:
                    conf += 0.25
                if ctr_change < -adapt["ctr_drop_pct"]:
                    conf += 0.25
                
                sample_factor = min(1.0, len(df_filtered) / 1000.0)
                conf = max(0.0, min(1.0, conf * (0.7 + 0.3 * sample_factor)))
                evidence = {
                    "roas_before": roas_b, "roas_after": roas_a, "roas_change_pct": roas_change,
                    "ctr_before": ctr_b, "ctr_after": ctr_a, "ctr_change_pct": ctr_change
                }
                evaluated.append({
                    "id": hyp.get("id","unknown"),
                    "driver": hyp.get("driver","unknown"),
                    "description": hyp.get("description",""),
                    "segment": hyp.get("segment",""),
                    "confidence": round(conf, 2),
                    "evidence": evidence
                })
                lg.info({"event": "hyp_eval", "id": hyp.get("id"), "confidence": round(conf,2)})
            except Exception as e:
                lg.error({"event": "hyp_eval_failed", "id": hyp.get("id","unknown"), "error": str(e)})
        lg.info({"event": "evaluation_complete", "count": len(evaluated)})
        return evaluated
