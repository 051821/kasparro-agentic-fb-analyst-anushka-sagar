from typing import Dict, Any, List

import pandas as pd

from utils.schemas import Hypothesis, EvaluatedHypothesis
from utils.validate import filter_significant_segments, global_before_after_split


class EvalAgent:
    def evaluate(
        self,
        df: pd.DataFrame,
        hypotheses: List[Hypothesis],
        thresholds: Dict[str, Any],
    ) -> List[EvaluatedHypothesis]:
        df_filtered = filter_significant_segments(df, thresholds)
        before_df, after_df = global_before_after_split(df_filtered)

        roas_before = (
            before_df["revenue"].sum() / before_df["spend"].sum()
            if before_df["spend"].sum() > 0
            else 0.0
        )
        roas_after = (
            after_df["revenue"].sum() / after_df["spend"].sum()
            if after_df["spend"].sum() > 0
            else 0.0
        )

        ctr_before = (
            before_df["clicks"].sum() / before_df["impressions"].sum()
            if before_df["impressions"].sum() > 0
            else 0.0
        )
        ctr_after = (
            after_df["clicks"].sum() / after_df["impressions"].sum()
            if after_df["impressions"].sum() > 0
            else 0.0
        )

        roas_change_pct = (
            (roas_after - roas_before) / roas_before if roas_before > 0 else 0.0
        )
        ctr_change_pct = (
            (ctr_after - ctr_before) / ctr_before if ctr_before > 0 else 0.0
        )

        evaluated: List[EvaluatedHypothesis] = []

        for hyp in hypotheses:
            confidence = 0.5
            if roas_change_pct < 0:
                confidence += 0.25
            if ctr_change_pct < 0:
                confidence += 0.25

            confidence = max(0.0, min(1.0, confidence))

            evaluated.append(
                {
                    "id": hyp["id"],
                    "driver": hyp["driver"],
                    "description": hyp["description"],
                    "segment": hyp["segment"],
                    "confidence": round(confidence, 2),
                    "evidence": {
                        "roas_before": roas_before,
                        "roas_after": roas_after,
                        "roas_change_pct": roas_change_pct,
                        "ctr_before": ctr_before,
                        "ctr_after": ctr_after,
                        "ctr_change_pct": ctr_change_pct,
                    },
                }
            )

        return evaluated
