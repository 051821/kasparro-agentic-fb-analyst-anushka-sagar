import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents.data_agent import DataAgent
import pandas as pd


def test_data_loading_and_summary():
    config = {
        "data": {
            "path": "data/Synthetic_fb_ads.csv"
        },
        "retry": {
            "attempts": 1,
            "delay": 0
        },
        "schema": {
            "version": 1,
            "expected_columns": [
                "date", "spend", "impressions", "clicks", "revenue",
                "ctr", "roas", "campaign_name", "creative_message"
            ]
        }
    }

    agent = DataAgent(config)     # ✅ FIXED
    output = agent.run()          # ✅ FIXED

    assert "df" in output
    assert "summary" in output

    df = output["df"]

    assert isinstance(df, pd.DataFrame)
    assert "spend" in df.columns
    assert "revenue" in df.columns
