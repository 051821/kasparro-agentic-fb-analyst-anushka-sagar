# src/orchestrator/agent_control.py

from typing import Dict, Any
import os
import json
from uuid import uuid4
import yaml

from utils.logger import configure_logging, bind_trace
from agents.planner_agent import PlannerAgent
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.eval_agent import EvalAgent
from agents.creative_agent import CreativeAgent

CONFIG_PATH = os.path.join("config", "config.yml")
config = yaml.safe_load(open(CONFIG_PATH, "r", encoding="utf-8"))
configure_logging(config["paths"]["log_dir"])     # <---- FIXED


class AgentController:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

        self.planner = PlannerAgent(config)
        self.data_agent = DataAgent(config)
        self.insight_agent = InsightAgent(config)
        self.eval_agent = EvalAgent()
        self.creative_agent = CreativeAgent(config)

    def run(self, query: str) -> Dict[str, Any]:
        trace_id = str(uuid4())
        root = bind_trace(trace_id=trace_id, agent="run")

        root.info({"event": "pipeline_start", "query": query})
        self.planner.plan(query, trace_id=trace_id)
        data_bundle = self.data_agent.run(trace_id=trace_id)
        df = data_bundle["df"]
        summary = data_bundle["summary"]
        hypotheses = self.insight_agent.generate(
            query, summary, trace_id=trace_id
        )
        insights = self.eval_agent.evaluate(
            df,
            hypotheses,
            self.config.get("thresholds", {}),
            trace_id=trace_id
        )
        creatives = self.creative_agent.generate(df, trace_id=trace_id)
        report_dir = self.config["paths"].get("report_dir", "reports")
        os.makedirs(report_dir, exist_ok=True)

        with open(os.path.join(report_dir, "insights.json"), "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2)

        with open(os.path.join(report_dir, "creatives.json"), "w", encoding="utf-8") as f:
            json.dump(creatives, f, indent=2)

        with open(os.path.join(report_dir, "trace_meta.json"), "w", encoding="utf-8") as f:
            json.dump({"trace_id": trace_id}, f, indent=2)

        root.info({"event": "pipeline_end", "trace_id": trace_id})

        return {
            "insights": insights,
            "creatives": creatives,
            "trace_id": trace_id,
        }
