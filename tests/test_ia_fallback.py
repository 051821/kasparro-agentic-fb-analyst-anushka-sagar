import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","src")))
from agents.insight_agent import InsightAgent
def test_insight_fallback_no_llm():
    cfg={"enable_llm":False,"retry":{"attempts":1,"delay":0}}
    a = InsightAgent(cfg)
    res = a.generate("q",{"date_range":{}}, trace_id="t")
    assert isinstance(res, list)
