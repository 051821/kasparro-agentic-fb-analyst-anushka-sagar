from typing import Dict, Any, List

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from utils.llm_client import get_llm
from utils.schemas import Hypothesis


class InsightAgent:

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = get_llm(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"],
        )
        with open("prompts/insight_agent_prompt.md", "r", encoding="utf-8") as f:
            template = f.read()
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["query", "summary"],
        )
        self.parser = JsonOutputParser()

    def generate(self, query: str, summary: Dict[str, Any]) -> List[Hypothesis]:
        chain = self.prompt | self.llm | self.parser
        try:
            result = chain.invoke({"query": query, "summary": summary})
            if isinstance(result, list):
                return result  # type: ignore[return-value]
        except Exception as e:
            logger.error(f"InsightAgent LLM failed, using fallback hypotheses. Error: {e}")

        # fallback static hypotheses
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
        return fallback
