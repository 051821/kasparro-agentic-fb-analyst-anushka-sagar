import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","src")))
from agents.creative_agent import CreativeAgent
import pandas as pd
def test_creative_fallback_output():
    cfg={"enable_llm":False,"retry":{"attempts":1,"delay":0}}
    a = CreativeAgent(cfg)
    df=pd.DataFrame({"campaign_name":["a","b"],"impressions":[1000,2000],"clicks":[1,5],"spend":[10,20]})
    res = a.generate(df, trace_id="t")
    assert isinstance(res, list)
