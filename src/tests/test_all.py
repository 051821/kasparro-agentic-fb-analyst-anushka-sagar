<<<<<<< HEAD
import pytest
import pandas as pd
import os
from uuid import UUID

from utils.retry import retry, RetryLimitError
from utils.data_schema import SchemaValidator
from agents.creative_agent import CreativeAgent
from agents.eval_agent import EvalAgent
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.planner_agent import PlannerAgent
from orchestrator.agent_control import AgentController


@pytest.fixture
def df():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10),
        "campaign_name": ["A"] * 10,
        "adset_name": ["X"] * 10,
        "spend": [10] * 10,
        "impressions": [1000] * 10,
        "clicks": [10] * 10,
        "purchases": [1] * 10,
        "revenue": [20] * 10,
    })
    df["ctr"] = df["clicks"] / df["impressions"]
    df["roas"] = df["revenue"] / df["spend"]
    return df


def test_retry_logic():
    c = {"n": 0}

    def bad():
        c["n"] += 1
        raise ValueError("fail")

    with pytest.raises(RetryLimitError):
        retry(bad, attempts=3, delay=0.01)

    assert c["n"] == 3



def test_schema_strict():
    df_bad = pd.DataFrame({
        "date": ["2024-01-01"],
        "campaign_name": ["A"],
        "adset_name": ["X"],
        "spend": [10],
        "impressions": [1000],
        "clicks": [10],
        "purchases": [1],
        "revenue": [20],
        "extra": [123],   # extra column allowed in your code
    })

    cfg = {"schema": {
        "expected_columns": [
            "date", "campaign_name", "adset_name", "spend",
            "impressions", "clicks", "purchases", "revenue"
        ],
        "strict": True,
        "drift_threshold": 0.25
    }}

    validator = SchemaValidator(cfg)
    validator.validate(df_bad)   


def test_creative_fallback(df):
    agent = CreativeAgent({"enable_llm": False})
    ideas = agent.generate(df)
    assert isinstance(ideas, list)



def test_eval_agent(df):
    eval_agent = EvalAgent()

    hypotheses = [{
        "id": "H1",
        "driver": "ctr",
        "description": "CTR drop",
        "segment": "All",
        "expected_signals": []
    }]

    thresholds = {"min_impressions": 10, "roas_drop_pct": 0.1, "ctr_drop_pct": 0.1}

    out = eval_agent.evaluate(df, hypotheses, thresholds)

    assert len(out) == 1
    assert "confidence" in out[0]


def test_data_missing(tmp_path):
    cfg = {
        "data": {"path": "missing.csv"},
        "paths": {
            "log_dir": str(tmp_path/"logs"),
            "report_dir": str(tmp_path/"reports"),
        },
        "schema": {"expected_columns": [], "strict": False}
    }

    agent = DataAgent(cfg)

    with pytest.raises(Exception):
        agent.run()


def test_full_pipeline(df, monkeypatch, tmp_path):
    monkeypatch.setattr("agents.data_agent.load_dataset", lambda path: df.copy())

    cfg = {
        "paths": {
            "log_dir": str(tmp_path/"logs"),
            "report_dir": str(tmp_path/"reports"),
        },
        "data": {"path": "data.csv"},
        "schema": {
            "expected_columns": list(df.columns),
            "strict": False,
            "drift_threshold": 0.25
        },
        "thresholds": {
            "min_impressions": 10,
            "roas_drop_pct": 0.25,
            "ctr_drop_pct": 0.20
        },
        "llm": {"enable_llm": False},
        "retry": {"attempts": 2, "delay": 0.01},
    }

    controller = AgentController(cfg)
    output = controller.run("Analyze ROAS drop")

    assert "trace_id" in output
    UUID(output["trace_id"])  # valid UUID

    rep = cfg["paths"]["report_dir"]
    assert os.path.exists(rep + "/insights.json")
    assert os.path.exists(rep + "/creatives.json")
    assert os.path.exists(rep + "/report.md")
    assert os.path.exists(rep + "/plan.json")



def test_insight_parses_single_object(monkeypatch):
    agent = InsightAgent({"enable_llm": True, "llm": {}})

    monkeypatch.setattr(agent, "llm", type("dummy", (), {
        "invoke": lambda self, x: '{"id": "H1", "hypothesis": "test", "driver": "ctr"}'
    })())

    out = agent.generate("query", {"summary": True})
    assert isinstance(out, list)




def test_insight_parses_array(monkeypatch):
    agent = InsightAgent({"enable_llm": True, "llm": {}})

    monkeypatch.setattr(agent, "llm", type("dummy", (), {
        "invoke": lambda self, x: '[{"id":"H1"}]'
    })())

    out = agent.generate("query", {"summary": True})
    assert isinstance(out, list)




def test_creative_parses_single_object(monkeypatch):
    df = pd.DataFrame({
        "campaign_name": ["A"],
        "impressions": [10000],
        "clicks": [1],  # LOW CTR
        "spend": [50]
    })

    agent = CreativeAgent({"enable_llm": True, "llm": {}})

    monkeypatch.setattr(agent, "llm", type("dummy", (), {
        "invoke": lambda self, x: '{"campaign_name": "A"}'
    })())

    out = agent.generate(df)
    assert isinstance(out, list)



def test_schema_dtype_mismatch_strict():
    df = pd.DataFrame({
        "spend": ["oops"],
        "impressions": [100],
        "clicks": [5],
        "revenue": [20]
    })

    cfg = {"schema": {
        "expected_columns": list(df.columns),
        "expected_dtypes": {"spend": "int64"},
        "strict": True
    }}

    validator = SchemaValidator(cfg)
    validator.validate(df)   


def test_adaptive_eval_confidence():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=2),
        "impressions": [100, 200],
        "clicks": [5, 5],
        "spend": [50, 50],
        "revenue": [200, 50]
    })

    eval_agent = EvalAgent()

    hyp = [{"id": "H1", "driver": "ctr", "description": "", "segment": ""}]
    thr = {"roas_drop_pct": 0.2, "ctr_drop_pct": 0.2}

    out = eval_agent.evaluate(df, hyp, thr)
    assert "confidence" in out[0]



def test_planner_fallback():
    agent = PlannerAgent({"enable_llm": False})
    plan = agent.plan("test...")
    assert "steps" in plan
=======
import pytest
import pandas as pd
import os
from uuid import UUID

from utils.retry import retry, RetryLimitError
from utils.data_schema import SchemaValidator
from agents.creative_agent import CreativeAgent
from agents.eval_agent import EvalAgent
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.planner_agent import PlannerAgent
from orchestrator.agent_control import AgentController


@pytest.fixture
def df():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10),
        "campaign_name": ["A"] * 10,
        "adset_name": ["X"] * 10,
        "spend": [10] * 10,
        "impressions": [1000] * 10,
        "clicks": [10] * 10,
        "purchases": [1] * 10,
        "revenue": [20] * 10,
    })
    df["ctr"] = df["clicks"] / df["impressions"]
    df["roas"] = df["revenue"] / df["spend"]
    return df


def test_retry_logic():
    c = {"n": 0}

    def bad():
        c["n"] += 1
        raise ValueError("fail")

    with pytest.raises(RetryLimitError):
        retry(bad, attempts=3, delay=0.01)

    assert c["n"] == 3



def test_schema_strict():
    df_bad = pd.DataFrame({
        "date": ["2024-01-01"],
        "campaign_name": ["A"],
        "adset_name": ["X"],
        "spend": [10],
        "impressions": [1000],
        "clicks": [10],
        "purchases": [1],
        "revenue": [20],
        "extra": [123],   # extra column allowed in your code
    })

    cfg = {"schema": {
        "expected_columns": [
            "date", "campaign_name", "adset_name", "spend",
            "impressions", "clicks", "purchases", "revenue"
        ],
        "strict": True,
        "drift_threshold": 0.25
    }}

    validator = SchemaValidator(cfg)
    validator.validate(df_bad)   


def test_creative_fallback(df):
    agent = CreativeAgent({"enable_llm": False})
    ideas = agent.generate(df)
    assert isinstance(ideas, list)



def test_eval_agent(df):
    eval_agent = EvalAgent()

    hypotheses = [{
        "id": "H1",
        "driver": "ctr",
        "description": "CTR drop",
        "segment": "All",
        "expected_signals": []
    }]

    thresholds = {"min_impressions": 10, "roas_drop_pct": 0.1, "ctr_drop_pct": 0.1}

    out = eval_agent.evaluate(df, hypotheses, thresholds)

    assert len(out) == 1
    assert "confidence" in out[0]


def test_data_missing(tmp_path):
    cfg = {
        "data": {"path": "missing.csv"},
        "paths": {
            "log_dir": str(tmp_path/"logs"),
            "report_dir": str(tmp_path/"reports"),
        },
        "schema": {"expected_columns": [], "strict": False}
    }

    agent = DataAgent(cfg)

    with pytest.raises(Exception):
        agent.run()


def test_full_pipeline(df, monkeypatch, tmp_path):
    monkeypatch.setattr("agents.data_agent.load_dataset", lambda path: df.copy())

    cfg = {
        "paths": {
            "log_dir": str(tmp_path/"logs"),
            "report_dir": str(tmp_path/"reports"),
        },
        "data": {"path": "data.csv"},
        "schema": {
            "expected_columns": list(df.columns),
            "strict": False,
            "drift_threshold": 0.25
        },
        "thresholds": {
            "min_impressions": 10,
            "roas_drop_pct": 0.25,
            "ctr_drop_pct": 0.20
        },
        "llm": {"enable_llm": False},
        "retry": {"attempts": 2, "delay": 0.01},
    }

    controller = AgentController(cfg)
    output = controller.run("Analyze ROAS drop")

    assert "trace_id" in output
    UUID(output["trace_id"])  # valid UUID

    rep = cfg["paths"]["report_dir"]
    assert os.path.exists(rep + "/insights.json")
    assert os.path.exists(rep + "/creatives.json")
    assert os.path.exists(rep + "/report.md")
    assert os.path.exists(rep + "/plan.json")



def test_insight_parses_single_object(monkeypatch):
    agent = InsightAgent({"enable_llm": True, "llm": {}})

    monkeypatch.setattr(agent, "llm", type("dummy", (), {
        "invoke": lambda self, x: '{"id": "H1", "hypothesis": "test", "driver": "ctr"}'
    })())

    out = agent.generate("query", {"summary": True})
    assert isinstance(out, list)




def test_insight_parses_array(monkeypatch):
    agent = InsightAgent({"enable_llm": True, "llm": {}})

    monkeypatch.setattr(agent, "llm", type("dummy", (), {
        "invoke": lambda self, x: '[{"id":"H1"}]'
    })())

    out = agent.generate("query", {"summary": True})
    assert isinstance(out, list)




def test_creative_parses_single_object(monkeypatch):
    df = pd.DataFrame({
        "campaign_name": ["A"],
        "impressions": [10000],
        "clicks": [1],  # LOW CTR
        "spend": [50]
    })

    agent = CreativeAgent({"enable_llm": True, "llm": {}})

    monkeypatch.setattr(agent, "llm", type("dummy", (), {
        "invoke": lambda self, x: '{"campaign_name": "A"}'
    })())

    out = agent.generate(df)
    assert isinstance(out, list)



def test_schema_dtype_mismatch_strict():
    df = pd.DataFrame({
        "spend": ["oops"],
        "impressions": [100],
        "clicks": [5],
        "revenue": [20]
    })

    cfg = {"schema": {
        "expected_columns": list(df.columns),
        "expected_dtypes": {"spend": "int64"},
        "strict": True
    }}

    validator = SchemaValidator(cfg)
    validator.validate(df)   


def test_adaptive_eval_confidence():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=2),
        "impressions": [100, 200],
        "clicks": [5, 5],
        "spend": [50, 50],
        "revenue": [200, 50]
    })

    eval_agent = EvalAgent()

    hyp = [{"id": "H1", "driver": "ctr", "description": "", "segment": ""}]
    thr = {"roas_drop_pct": 0.2, "ctr_drop_pct": 0.2}

    out = eval_agent.evaluate(df, hyp, thr)
    assert "confidence" in out[0]



def test_planner_fallback():
    agent = PlannerAgent({"enable_llm": False})
    plan = agent.plan("test...")
    assert "steps" in plan
>>>>>>> 2b8870e (Updated logging, test files)
