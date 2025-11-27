# src/agents/planner_agent.py

from typing import Dict, Any
import re
from loguru import logger

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from utils.llm_client import get_llm


class PlannerAgent:

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

        # Load LLM only if enabled
        if self.config.get("enable_llm", False):
            self.llm = get_llm(
                model=self.config.get("llm", {}).get("model", "llama3.1"),
                temperature=self.config.get("llm", {}).get("temperature", 0.1),
            )
        else:
            self.llm = None

        try:
            with open("prompts/Planner.md", "r", encoding="utf-8") as f:
                template_text = f.read()
            self.prompt = PromptTemplate(template=template_text, input_variables=["query"])
        except Exception as e:
            logger.error(f"Failed to load Planner.md template: {e}")
            self.prompt = None

        self.parser = JsonOutputParser()

    def plan(self, query: str) -> Dict[str, Any]:

        if not self.config.get("enable_llm", False):
            return self._fallback_plan(query)

        if self.llm and self.prompt:
            chain = self.prompt | self.llm | self.parser

            try:
                result = chain.invoke({"query": query})
                if isinstance(result, dict):
                    return result
            except Exception as e:
                logger.error(f"PlannerAgent LLM failed, using fallback. Error: {e}")

        return self._fallback_plan(query)


    def _fallback_plan(self, query: str) -> Dict[str, Any]:

        q = query.lower()
        time_window = "auto"

        match = re.search(r"last\s+(\d+)\s+day", q)
        if match:
            days = match.group(1)
            time_window = f"last_{days}_days"

        return {
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
