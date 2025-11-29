from typing import Dict, Any, List

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from utils.llm_client import get_llm
from utils.schemas import Hypothesis


class InsightAgent:

    def __init__(self, config: Dict[str, Any]):
        # Structured per-agent logger
        self.log = logger.bind(agent="insight")

        self.config = config
        self.log.trace("Initializing InsightAgent with config.")

        # LLM init
        try:
            self.llm = get_llm(
                model=config["llm"]["model"],
                temperature=config["llm"]["temperature"],
            )
            self.log.info("LLM client initialized successfully for InsightAgent.")
        except Exception as e:
            self.log.error(f"Failed to initialize LLM: {e}")
            self.llm = None

        # Load prompt
        try:
            with open("prompts/insight_agent_prompt.md", "r", encoding="utf-8") as f:
                template = f.read()
            self.prompt = PromptTemplate(
                template=template,
                input_variables=["query", "summary"],
            )
            self.log.trace("InsightAgent prompt template loaded successfully.")
        except Exception as e:
            self.log.error(f"Failed to load insight_agent_prompt.md template: {e}")
            self.prompt = None

        self.parser = JsonOutputParser()


    def generate(self, query: str, summary: Dict[str, Any]) -> List[Hypothesis]:
        self.log.info(f"Generating insights for query: {query}")
        self.log.debug(f"Summary received for insight generation: {summary}")

        if not self.llm or not self.prompt:
            self.log.error("LLM or prompt missing — using fallback hypotheses.")
            return self._fallback_hypotheses()

        chain = self.prompt | self.llm | self.parser

        try:
            self.log.trace("Sending insight generation request to LLM...")
            result = chain.invoke({"query": query, "summary": summary})
            self.log.trace(f"Raw LLM output received: {result}")

            if isinstance(result, list):
                self.log.info("InsightAgent generated hypotheses successfully.")
                return result

            self.log.error("InsightAgent LLM returned non-list output. Using fallback.")
        except Exception as e:
            self.log.error(
                f"InsightAgent LLM failed while generating hypotheses. "
                f"Query='{query}', Error='{e}'"
            )

        return self._fallback_hypotheses()


    def _fallback_hypotheses(self) -> List[Hypothesis]:
        self.log.trace("Executing fallback hypotheses logic.")

        fallback: List[Hypothesis] = [
            {
                "id": "H1",
                "driver": "Audience fatigue",
                "description": "ROAS dropped while impressions increased and CTR decreased, suggesting audience fatigue.",
                "segment": "High-spend evergreen campaigns",
                "expected_signals": ["impressions_up", "ctr_down", "roas_down"],
            },
            {
                "id": "H2",
                "driver": "Creative fatigue",
                "description": "ROAS dropped in campaigns reusing the same creative messages for a long time.",
                "segment": "Top-spend campaigns with repeated creative_message",
                "expected_signals": ["ctr_down", "spend_stable_or_up"],
            },
        ]

        self.log.info("Fallback hypotheses returned due to LLM failure.")
        return fallback
