import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","src")))
from agents.data_agent import DataAgent
import pandas as pd
import pytest

def test_data_agent_reads_and_summarizes(tmp_path):
    cfg = {"data":{"path":"data/Synthetic_fb_ads.csv"},"retry":{"attempts":1,"delay":0},"schema":{"expected_columns":["date","spend","impressions","clicks","ctr","revenue","roas","campaign_name","creative_message"],"strict":False}}
    a = DataAgent(cfg)
    out = a.run()
    assert "df" in out and "summary" in out
    assert isinstance(out["df"], pd.DataFrame)

def test_data_agent_missing_file_raises(tmp_path):
    cfg = {"data":{"path":"data/THIS_FILE_DOES_NOT_EXIST.csv"},"retry":{"attempts":1,"delay":0},"schema":{"expected_columns":[]}}
    a = DataAgent(cfg)
    with pytest.raises(Exception):
        a.run()
