from typing import Dict, Any
import re
from loguru import logger

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from utils.llm_client import get_llm


class PlannerAgent:

    def __init__(self, config: Dict[str, Any] | None = None):
        # Attach per-agent logger
        self.log = logger.bind(agent="plan")

        self.config = config or {}
        self.log.trace("PlannerAgent initialized with config.")

        # Load LLM
        if self.config.get("enable_llm", False):
            try:
                self.llm = get_llm(
                    model=self.config.get("llm", {}).get("model", "llama3.1"),
                    temperature=self.config.get("llm", {}).get("temperature", 0.1),
                )
                self.log.info("LLM client initialized successfully.")
            except Exception as e:
                self.log.error(f"Failed to initialize LLM client: {e}")
                self.llm = None
        else:
            self.llm = None
            self.log.info("Planner running in fallback mode (LLM disabled).")

        # Load prompt
        try:
            with open("prompts/Planner.md", "r", encoding="utf-8") as f:
                template_text = f.read()
            self.prompt = PromptTemplate(template=template_text, input_variables=["query"])
            self.log.trace("Planner prompt template loaded successfully.")
        except Exception as e:
            self.log.error(f"Failed to load Planner.md template: {e}")
            self.prompt = None

        self.parser = JsonOutputParser()


    def plan(self, query: str) -> Dict[str, Any]:
        self.log.info(f"Received query for planning: {query}")
        self.log.trace("Planner starting LLM reasoning pipeline.")

        if not self.config.get("enable_llm", False):
            self.log.debug("LLM disabled. Using fallback plan.")
            return self._fallback_plan(query)

        if self.llm and self.prompt:
            chain = self.prompt | self.llm | self.parser

            try:
                result = chain.invoke({"query": query})
                self.log.trace(f"Raw LLM output received: {result}")

                if isinstance(result, dict):
                    self.log.info("Planner LLM produced a valid plan.")
                    return result

                self.log.error("Planner LLM returned non-dict output. Switching to fallback.")
            except Exception as e:
                self.log.error(
                    f"PlannerAgent LLM failed while generating plan. "
                    f"Query='{query}', Error='{e}'"
                )

        # Fallback execution
        self.log.debug("Executing fallback plan due to LLM failure or invalid output.")
        return self._fallback_plan(query)


    def _fallback_plan(self, query: str) -> Dict[str, Any]:
        self.log.trace("Entering fallback planning logic.")

        q = query.lower()
        time_window = "auto"

        match = re.search(r"last\s+(\d+)\s+day", q)
        if match:
            days = match.group(1)
            time_window = f"last_{days}_days"
            self.log.debug(f"Extracted time window from query: {time_window}")

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

        self.log.info(f"Generated fallback plan: {plan}")
        return plan
