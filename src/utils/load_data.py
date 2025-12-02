import pandas as pd


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
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

    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "ctr" not in df.columns:
        df["ctr"] = df["clicks"] / df["impressions"].replace(0, 1)

    if "roas" not in df.columns:
        df["roas"] = df["revenue"] / df["spend"].replace(0, 1)

    return df
