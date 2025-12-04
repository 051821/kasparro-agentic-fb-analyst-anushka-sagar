# src/agents/eval_agent.py
from typing import Dict, Any, List
import pandas as pd
from loguru import logger
from utils.schemas import Hypothesis, EvaluatedHypothesis
from utils.validate import filter_significant_segments, global_before_after_split
from utils.metrics import agent_metrics
from utils.logger import bind_trace

log = logger.bind(agent="evaluate")

def json_safe(obj):
    try:
        import json
        return json.dumps(obj, default=str, ensure_ascii=False)
    except Exception:
        return str(obj)

class EvalAgent:
    def __init__(self):
        self.log = log

    @agent_metrics("evaluate")
    def evaluate(self, df: pd.DataFrame, hypotheses: List[Hypothesis], thresholds: Dict[str, Any], trace_id: str = None) -> List[EvaluatedHypothesis]:
        lg = bind_trace(trace_id).bind(agent="evaluate")
        lg.info(json_safe({"event": "evaluation_start", "num_hypotheses": len(hypotheses)}))

        df_filtered = filter_significant_segments(df, thresholds)
        before, after = global_before_after_split(df_filtered)

        def safe_div(a, b):
            return float(a)/float(b) if b and b != 0 else 0.0

        roas_b = safe_div(before["revenue"].sum(), before["spend"].sum())
        roas_a = safe_div(after["revenue"].sum(), after["spend"].sum())
        ctr_b = safe_div(before["clicks"].sum(), before["impressions"].sum())
        ctr_a = safe_div(after["clicks"].sum(), after["impressions"].sum())

        base_roas_drop = thresholds.get("roas_drop_pct", 0.25)
        base_ctr_drop = thresholds.get("ctr_drop_pct", 0.20)

        spend_cv = 0.0
        if len(df_filtered) > 1 and df_filtered["spend"].mean() != 0:
            spend_cv = (df_filtered["spend"].std() / (df_filtered["spend"].mean() + 1e-9))

        q75 = float(df_filtered["spend"].quantile(0.75)) if not df_filtered.empty else 0.0
        multiplier = 1.0 + min(1.0, q75 / (df_filtered["spend"].mean() + 1e-9)) if df_filtered["spend"].mean() else 1.0

        adapt_roas = base_roas_drop * (1 + spend_cv) * multiplier
        adapt_ctr = base_ctr_drop * (1 + spend_cv) * multiplier

        roas_change = (roas_a - roas_b) / roas_b if roas_b else (roas_a - roas_b)
        ctr_change = (ctr_a - ctr_b) / ctr_b if ctr_b else (ctr_a - ctr_b)

        evaluated: List[EvaluatedHypothesis] = []
        for hyp in hypotheses:
            conf = 0.5
            if roas_change < -adapt_roas:
                conf += 0.25
            if ctr_change < -adapt_ctr:
                conf += 0.25

            sample_factor = min(1.0, len(df_filtered) / 1000.0)
            conf = max(0.0, min(1.0, conf * (0.7 + 0.3 * sample_factor)))

            evidence = {
                "roas_before": roas_b, "roas_after": roas_a, "roas_change_pct": roas_change,
                "ctr_before": ctr_b, "ctr_after": ctr_a, "ctr_change_pct": ctr_change
            }

            evaluated.append({
                "id": hyp.get("id", "unknown"),
                "driver": hyp.get("driver", "unknown"),
                "description": hyp.get("description", ""),
                "segment": hyp.get("segment", ""),
                "confidence": round(conf, 2),
                "evidence": evidence
            })
            lg.info(json_safe({"event": "hyp_eval", "id": hyp.get("id"), "confidence": round(conf, 2)}))

        lg.info(json_safe({"event": "evaluation_complete", "count": len(evaluated)}))
        return evaluated
