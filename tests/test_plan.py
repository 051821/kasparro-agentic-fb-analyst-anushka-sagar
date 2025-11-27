import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents.planner_agent import PlannerAgent


def test_planner_fallback_plan():
    agent = PlannerAgent(config={})
    query = "Analyze ROAS drop in last 7 days"
    plan = agent.plan(query)

    assert isinstance(plan, dict)
    assert plan["original_query"] == query
    assert "steps" in plan
    assert "focus" in plan
    assert plan["task"] == "analyze_roas_change"
