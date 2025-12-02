import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","src")))
from agents.planner_agent import PlannerAgent
def test_planner_fallback():
    a=PlannerAgent(config={})
    p=a.plan("Analyze ROAS drop in last 7 days")
    assert p["task"]=="analyze_roas_change"
