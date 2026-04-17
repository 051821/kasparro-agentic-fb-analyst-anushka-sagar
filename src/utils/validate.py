"""Project file: src/utils/validate.py."""

from typing import Dict, Any, Tuple
import pandas as pd


def filter_significant_segments(df: pd.DataFrame, thresholds: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter to rows with enough impressions to matter.
    """
    min_impressions = thresholds.get("min_impressions", 1000)
    return df[df["impressions"] >= min_impressions]


def global_before_after_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split into 'before' and 'after' using median date.
    """
    if df["date"].isna().all():
        return df, df

    median_date = df["date"].median()
    before_df = df[df["date"] <= median_date]
    after_df = df[df["date"] > median_date]
    if after_df.empty:
        after_df = before_df
    return before_df, after_df
