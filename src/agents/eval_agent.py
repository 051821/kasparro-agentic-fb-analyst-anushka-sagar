from typing import Dict, Any, List
import pandas as pd
from loguru import logger

from utils.schemas import Hypothesis, EvaluatedHypothesis
from utils.validate import filter_significant_segments, global_before_after_split


class EvalAgent:

    def __init__(self):
        self.log = logger.bind(agent="evaluate")
        self.log.trace("EvalAgent initialized.")

    def evaluate(
        self,
        df: pd.DataFrame,
        hypotheses: List[Hypothesis],
        thresholds: Dict[str, Any],
    ) -> List[EvaluatedHypothesis]:

        self.log.info("Starting evaluation of hypotheses.")
        self.log.debug(f"Received {len(hypotheses)} hypotheses for evaluation.")
        self.log.trace(f"Thresholds applied: {thresholds}")

        try:
            df_filtered = filter_significant_segments(df, thresholds)
            self.log.trace(f"Filtered dataset shape: {df_filtered.shape}")

            before_df, after_df = global_before_after_split(df_filtered)
            self.log.trace(
                f"Before period rows: {before_df.shape[0]}, "
                f"After period rows: {after_df.shape[0]}"
            )
        except Exception as e:
            self.log.error(f"Dataset preparation failed during evaluation: {e}")
            raise

        # Compute metrics
        try:
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

            self.log.debug(
                "Computed metrics: "
                f"ROAS_before={roas_before}, ROAS_after={roas_after}, "
                f"CTR_before={ctr_before}, CTR_after={ctr_after}"
            )
        except Exception as e:
            self.log.error(f"Failed to compute metrics for evaluator: {e}")
            raise

        evaluated: List[EvaluatedHypothesis] = []

        # Evaluate each hypothesis
        for hyp in hypotheses:
            try:
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

                self.log.trace(
                    f"Evaluated hypothesis {hyp['id']} with confidence={round(confidence,2)}"
                )

            except Exception as e:
                self.log.error(
                    f"Failed evaluating hypothesis {hyp.get('id', 'UNKNOWN')} — Error: {e}"
                )

        self.log.info("Evaluation completed successfully.")
        return evaluated
