import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents.eval_agent import EvalAgent
import pandas as pd


def test_eval_agent_basic():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        "impressions": [1000, 2000],
        "clicks": [10, 20],
        "spend": [100, 200],
        "revenue": [300, 400],
    })

    hypotheses = [{
        "id": "H1",
        "driver": "CTR drop",
        "description": "Test hyp",
        "segment": "Test",
        "expected_signals": ["ctr_down"]
    }]

    evaluator = EvalAgent()
    results = evaluator.evaluate(df, hypotheses, {"min_impressions": 0})

    assert isinstance(results, list)
    assert len(results) == 1
    assert "confidence" in results[0]
