# src/agents/eval_agent.py
from typing import Dict, Any, List
import pandas as pd
from loguru import logger
from utils.schemas import Hypothesis, EvaluatedHypothesis
from utils.validate import filter_significant_segments, global_before_after_split
from utils.metrics import agent_metrics
from utils.logger import bind_trace
import json

log = logger.bind(agent="evaluate")


def json_safe(obj):
    """Safe JSON for logging."""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except Exception:
        return str(obj)


class EvalAgent:
    def __init__(self):
        self.log = log

    @agent_metrics("evaluate")
    def evaluate(
        self,
        df: pd.DataFrame,
        hypotheses: List[Hypothesis],
        thresholds: Dict[str, Any],
        trace_id: str = None
    ) -> List[EvaluatedHypothesis]:

        lg = bind_trace(trace_id).bind(agent="evaluate")
        lg.info(json_safe({
            "event": "evaluation_start",
            "trace_id": trace_id,
            "num_hypotheses": len(hypotheses),
            "thresholds": thresholds
        }))

        df_filtered = filter_significant_segments(df, thresholds)
        before, after = global_before_after_split(df_filtered)

        lg.info(json_safe({
            "event": "evaluation_data_split",
            "trace_id": trace_id,
            "rows_before": len(before),
            "rows_after": len(after),
            "rows_filtered": len(df_filtered)
        }))

        def safe_div(a, b):
            return float(a)/float(b) if b and b != 0 else 0.0
        roas_b = safe_div(before["revenue"].sum(), before["spend"].sum())
        roas_a = safe_div(after["revenue"].sum(), after["spend"].sum())
        ctr_b = safe_div(before["clicks"].sum(), before["impressions"].sum())
        ctr_a = safe_div(after["clicks"].sum(), after["impressions"].sum())

        lg.info(json_safe({
            "event": "metric_comparison",
            "trace_id": trace_id,
            "roas_before": roas_b,
            "roas_after": roas_a,
            "ctr_before": ctr_b,
            "ctr_after": ctr_a
        }))

        base_roas_drop = thresholds.get("roas_drop_pct", 0.25)
        base_ctr_drop = thresholds.get("ctr_drop_pct", 0.20)

        spend_cv = 0.0
        if len(df_filtered) > 1 and df_filtered["spend"].mean() != 0:
            spend_cv = df_filtered["spend"].std() / (df_filtered["spend"].mean() + 1e-9)

        q75 = float(df_filtered["spend"].quantile(0.75)) if not df_filtered.empty else 0.0
        multiplier = (
            1.0 + min(1.0, q75 / (df_filtered["spend"].mean() + 1e-9))
            if df_filtered["spend"].mean()
            else 1.0
        )

        adapt_roas = base_roas_drop * (1 + spend_cv) * multiplier
        adapt_ctr = base_ctr_drop * (1 + spend_cv) * multiplier

        lg.info(json_safe({
            "event": "adaptive_thresholds",
            "trace_id": trace_id,
            "spend_cv": spend_cv,
            "q75_spend": q75,
            "multiplier": multiplier,
            "adaptive_roas_drop_threshold": adapt_roas,
            "adaptive_ctr_drop_threshold": adapt_ctr
        }))


        roas_change = (roas_a - roas_b) / roas_b if roas_b else (roas_a - roas_b)
        ctr_change = (ctr_a - ctr_b) / ctr_b if ctr_b else (ctr_a - ctr_b)

        lg.info(json_safe({
            "event": "metric_change_pct",
            "trace_id": trace_id,
            "roas_change_pct": roas_change,
            "ctr_change_pct": ctr_change
        }))

        evaluated: List[EvaluatedHypothesis] = []

        for hyp in hypotheses:
            conf = 0.5
            conf_reason = []

            if roas_change < -adapt_roas:
                conf += 0.25
                conf_reason.append("roas_drop_exceeded")

            if ctr_change < -adapt_ctr:
                conf += 0.25
                conf_reason.append("ctr_drop_exceeded")

            sample_factor = min(1.0, len(df_filtered) / 1000.0)
            conf = max(0.0, min(1.0, conf * (0.7 + 0.3 * sample_factor)))

            evidence = {
                "roas_before": roas_b,
                "roas_after": roas_a,
                "roas_change_pct": roas_change,
                "ctr_before": ctr_b,
                "ctr_after": ctr_a,
                "ctr_change_pct": ctr_change
            }
            evaluated_hyp = {
                "id": hyp.get("id", "unknown"),
                "driver": hyp.get("driver", "unknown"),
                "description": hyp.get("description", ""),
                "segment": hyp.get("segment", ""),
                "confidence": round(conf, 2),
                "evidence": evidence
            }
            evaluated.append(evaluated_hyp)
            lg.info(json_safe({
                "event": "hypothesis_evaluated",
                "trace_id": trace_id,
                "hypothesis_id": hyp.get("id"),
                "final_confidence": round(conf, 2),
                "confidence_reasons": conf_reason,
                "evidence_summary": evidence
            }))

        lg.info(json_safe({
            "event": "evaluation_complete",
            "trace_id": trace_id,
            "num_evaluated": len(evaluated)
        }))

        return evaluated
