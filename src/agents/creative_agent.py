from typing import Dict, Any, List
from loguru import logger
import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from utils.llm_client import get_llm
from utils.retry import retry
from utils.metrics import agent_metrics
from utils.logger import bind_trace
from utils.schemas import CreativeIdea

log = logger.bind(agent="creative")

class CreativeAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log = log
        try:
            if config.get("enable_llm", False):
                self.llm = get_llm(model=config["llm"]["model"], temperature=config["llm"].get("temperature",0.2))
            else:
                self.llm = None
        except Exception as e:
            self.log.error({"event":"llm_init_failed","error":str(e)})
            self.llm = None

        try:
            with open("prompts/creative_generator_prompt.md","r",encoding="utf-8") as f:
                template = f.read()
            self.prompt = PromptTemplate(template=template, input_variables=["low_ctr"])
            self.parser = JsonOutputParser()
        except Exception as e:
            self.log.error({"event":"creative_prompt_load_failed","error":str(e)})
            self.prompt = None
            self.parser = None

    def _find_low_ctr_campaigns(self, df: pd.DataFrame, threshold: float = 0.01) -> pd.DataFrame:
        grouped = df.groupby("campaign_name").agg(impressions=("impressions","sum"), clicks=("clicks","sum"), spend=("spend","sum")).reset_index()
        grouped["ctr"] = grouped["clicks"] / grouped["impressions"].replace(0,1)
        return grouped[grouped["ctr"] < threshold]

    def _fallback(self, df: pd.DataFrame, low_df: pd.DataFrame) -> List[CreativeIdea]:
        ideas = []
        for _, r in low_df.head(5).iterrows():
            cname = r["campaign_name"]
            rec = {"headline": f"Try a fresh angle for {cname}", "primary_text": "Highlight benefits + short CTA", "cta":"Learn More"}
            ideas.append({"campaign_name": cname, "issue":"Low CTR", "current_message":"", "recommendation":rec})
        self.log.info({"event":"fallback_creatives_generated","count":len(ideas)})
        return ideas

    @agent_metrics("creative")
    def generate(self, df: pd.DataFrame, trace_id: str = None) -> List[CreativeIdea]:
        lg = bind_trace(trace_id).bind(agent="creative")
        low = self._find_low_ctr_campaigns(df)
        if low.empty:
            lg.info({"event":"no_low_ctr"})
            return []

        payload = []
        for _, r in low.head(5).iterrows():
            payload.append({"campaign_name": r["campaign_name"], "ctr": float(r["ctr"])})

        lg.debug({"event":"creative_payload_size","size":len(payload)})
        if not (self.llm and self.prompt and self.parser):
            return self._fallback(df, low)

        try:
            chain = self.prompt | self.llm | self.parser
            result = retry(lambda: chain.invoke({"low_ctr": payload}),
                           attempts=self.config.get("retry", {}).get("attempts", 3),
                           delay=self.config.get("retry", {}).get("delay", 1.0),
                           backoff=2.0, jitter=0.1, agent="creative")
            if isinstance(result, list):
                lg.info({"event":"creative_generated","count":len(result)})
                return result
            lg.error({"event":"creative_invalid_output"})
            return self._fallback(df, low)
        except Exception as e:
            lg.error({"event":"creative_llm_failed","error":str(e)})
            return self._fallback(df, low)
