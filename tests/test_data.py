import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents.data_agent import DataAgent
import pandas as pd


def test_data_loading_and_summary():
    config = {
        "data": {
            "path": "data/Synthetic_fb_ads.csv"
        }
    }

    agent = DataAgent()
    output = agent.run(config)

    assert "df" in output
    assert "summary" in output

    df = output["df"]
    summary = output["summary"]

    assert isinstance(df, pd.DataFrame)
    assert "spend" in df.columns
    assert "revenue" in df.columns
