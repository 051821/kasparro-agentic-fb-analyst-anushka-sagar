import pandas as pd


def load_dataset(path: str) -> pd.DataFrame:
    """Load and minimally preprocess the FB Ads dataset."""
    df = pd.read_csv(path)

    # Basic safety: normalize column names
    df.columns = [c.strip() for c in df.columns]

    required = [
        "date",
        "campaign_name",
        "adset_name",
        "spend",
        "impressions",
        "clicks",
        "purchases",
        "revenue",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    # Parse date if it's not already datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Compute CTR and ROAS if not present
    if "ctr" not in df.columns:
        df["ctr"] = df["clicks"] / df["impressions"].replace(0, 1)

    if "roas" not in df.columns:
        df["roas"] = df["revenue"] / df["spend"].replace(0, 1)

    return df
