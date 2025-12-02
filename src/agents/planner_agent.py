from typing import Dict, Any
import re
from loguru import logger as _log
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from utils.llm_client import get_llm
from utils.retry import retry
from utils.metrics import agent_metrics
from utils.logger import bind_trace

_log = _log

class PlannerAgent:
    def __init__(self, config: Dict[str, Any] | None = None):
        self.log = _log.bind(agent="plan")
        self.config = config or {}
        self.log.debug("PlannerAgent initialized with config.")

        # Load LLM
        if self.config.get("enable_llm", False):
            try:
                self.llm = get_llm(
                    model=self.config.get("llm", {}).get("model", "llama3.1"),
                    temperature=self.config.get("llm", {}).get("temperature", 0.1),
                )
                self.log.info("LLM client initialized successfully.")
            except Exception as e:
                self.log.error({"event": "llm_init_failed", "error": str(e)})
                self.llm = None
        else:
            self.llm = None
            self.log.info("Planner running in fallback mode (LLM disabled).")

        # Load prompt
        try:
            with open("prompts/Planner.md", "r", encoding="utf-8") as f:
                template_text = f.read()
            self.prompt = PromptTemplate(template=template_text, input_variables=["query"])
            self.log.debug("Planner prompt template loaded successfully.")
        except Exception as e:
            self.log.error({"event": "prompt_load_failed", "error": str(e)})
            self.prompt = None

        self.parser = JsonOutputParser()

    @agent_metrics("plan")
    def plan(self, query: str, trace_id: str = None) -> Dict[str, Any]:
        log = bind_trace(trace_id).bind(agent="plan")
        log.info({"event": "plan_request", "query": query})
        if not self.config.get("enable_llm", False):
            log.debug({"event": "llm_disabled", "note": "using fallback plan"})
            return self._fallback_plan(query)

        if self.llm and self.prompt:
            chain = self.prompt | self.llm | self.parser
            try:
                result = retry(
                    lambda: chain.invoke({"query": query}),
                    attempts=self.config.get("retry", {}).get("attempts", 3),
                    delay=self.config.get("retry", {}).get("delay", 1.0),
                    agent="plan"
                )
                log.debug({"event": "llm_raw_output", "raw": str(result)})
                if isinstance(result, dict):
                    log.info({"event": "planner_success"})
                    return result
                else:
                    log.error({"event": "planner_invalid_output", "output_type": str(type(result))})
            except Exception as e:
                log.error({"event": "planner_llm_failure", "error": str(e)})

        log.debug({"event": "fallback_plan_executing"})
        return self._fallback_plan(query)

    def _fallback_plan(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        time_window = "auto"
        match = re.search(r"last\s+(\d+)\s+day", q)
        if match:
            days = match.group(1)
            time_window = f"last_{days}_days"

        plan = {
            "original_query": query,
            "task": "analyze_roas_change",
            "steps": [
                "load_data",
                "summarize_dataset",
                "generate_hypotheses",
                "evaluate_hypotheses",
                "generate_creatives_for_low_ctr",
                "write_report",
            ],
            "focus": {
                "time_window": time_window,
                "filters": {
                    "campaign_name_contains": [],
                    "country_in": [],
                    "audience_type_in": [],
                },
            },
        }
        self.log.info({"event": "fallback_plan_generated", "plan_task": plan["task"]})
        return plan

