from typing import Dict, Any
import pandas as pd


def dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build a compact summary dictionary to be used in LLM prompts.
    """
    date_min = df["date"].min()
    date_max = df["date"].max()

    total_spend = float(df["spend"].sum())
    total_revenue = float(df["revenue"].sum())
    overall_roas = float(total_revenue / total_spend) if total_spend > 0 else 0.0

    top_campaigns = (
        df.groupby("campaign_name")["spend"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    top_countries = {}
    if "country" in df.columns:
        top_countries = (
            df.groupby("country")["spend"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .to_dict()
        )

    return {
        "date_range": {
            "min": None if pd.isna(date_min) else str(date_min.date()),
            "max": None if pd.isna(date_max) else str(date_max.date()),
        },
        "totals": {
            "spend": total_spend,
            "revenue": total_revenue,
            "overall_roas": overall_roas,
        },
        "top_campaigns_by_spend": top_campaigns,
        "top_countries_by_spend": top_countries,
    }
