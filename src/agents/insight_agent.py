from typing import Dict, Any, List
from loguru import logger
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from utils.llm_client import get_llm
from utils.retry import retry
from utils.schemas import Hypothesis
from utils.metrics import agent_metrics
from utils.logger import bind_trace
from utils.exceptions import LLMError

log = logger.bind(agent="insight")

class InsightAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log = log
        try:
            if config.get("enable_llm", False):
                self.llm = get_llm(model=config["llm"]["model"], temperature=config["llm"].get("temperature", 0.2))
            else:
                self.llm = None
        except Exception as e:
            self.log.error({"event":"llm_init_failed","error":str(e)})
            self.llm = None

        try:
            with open("prompts/insight_agent_prompt.md","r",encoding="utf-8") as f:
                template = f.read()
            self.prompt = PromptTemplate(template=template, input_variables=["query","summary"])
        except Exception as e:
            self.log.error({"event":"prompt_load_failed","error":str(e)})
            self.prompt = None
        self.parser = JsonOutputParser()

    @agent_metrics("insight")
    def generate(self, query: str, summary: Dict[str, Any], trace_id: str = None) -> List[Hypothesis]:
        lg = bind_trace(trace_id).bind(agent="insight")
        lg.info({"event":"insight_generate_request","query":query})
        if not self.llm or not self.prompt:
            lg.warning({"event":"llm_or_prompt_missing","note":"using fallback hypotheses"})
            return self._fallback_hypotheses()

        chain = self.prompt | self.llm | self.parser
        try:
            result = retry(lambda: chain.invoke({"query": query, "summary": summary}),
                           attempts=self.config.get("retry", {}).get("attempts", 3),
                           delay=self.config.get("retry", {}).get("delay", 1.0),
                           backoff=2.0, jitter=0.1, agent="insight",
                           retry_on=(Exception,))
            if isinstance(result, list):

                for r in result:
                    if isinstance(r, dict) and "confidence" in r:
                        lg.info({"event":"hypothesis_confidence_reported","id": r.get("id"), "confidence": r.get("confidence")})
                return result
            else:
                lg.error({"event":"insight_invalid_output","type":str(type(result))})
                return self._fallback_hypotheses()
        except Exception as e:
            lg.error({"event":"insight_llm_failed","error":str(e)})
            raise LLMError(str(e))

    def _fallback_hypotheses(self) -> List[Hypothesis]:
        lg = logger.bind(agent="insight")
        fallback = [
            {"id":"H1","driver":"Audience fatigue","description":"ROAS dropped while impressions increased and CTR decreased","segment":"broad","expected_signals":["impressions_up","ctr_down","roas_down"]},
            {"id":"H2","driver":"Creative fatigue","description":"Repeated creative messaging causing CTR decline","segment":"top_spend","expected_signals":["ctr_down","spend_stable_or_up"]}
        ]
        lg.info({"event":"fallback_hypotheses_returned","count":len(fallback)})
        return fallback

