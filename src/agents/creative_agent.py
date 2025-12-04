# src/agents/creative_agent.py
from typing import Dict, Any, List
from loguru import logger
import pandas as pd
import json, re

from utils.llm_client import get_llm
from utils.retry import retry
from utils.metrics import agent_metrics
from utils.logger import bind_trace
from utils.schemas import CreativeIdea

log = logger.bind(agent="creative")

def safe_json(text: str):
    if not text:
        return None
    m = re.search(r"\{[\s\S]*", text)
    if not m:
        return None
    raw = m.group(0)
    if raw.count("{") > raw.count("}"):
        raw += "}" * (raw.count("{") - raw.count("}"))
    if raw.count("[") > raw.count("]"):
        raw += "]" * (raw.count("[") - raw.count("]"))
    try:
        return json.loads(raw)
    except:
        return None

class CreativeAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        try:
            if config.get("enable_llm", False):
                self.llm = get_llm(model=config["llm"]["model"], temperature=config["llm"].get("temperature", 0.0), format=config["llm"].get("format"))
            else:
                self.llm = None
        except Exception as e:
            log.error({"event": "creative_llm_init_failed", "error": str(e)})
            self.llm = None

        try:
            with open("prompts/creative_generator_prompt.md", "r", encoding="utf-8") as f:
                template = f.read()
            # simple templating via f-string format
            self.template = template
        except Exception as e:
            log.error({"event": "creative_prompt_load_failed", "error": str(e)})
            self.template = None

    @agent_metrics("creative")
    def generate(self, df: pd.DataFrame, trace_id: str = None) -> List[CreativeIdea]:
        lg = bind_trace(trace_id).bind(agent="creative")
        grouped = df.groupby("campaign_name").agg(impressions=("impressions", "sum"), clicks=("clicks", "sum"), spend=("spend", "sum")).reset_index()
        grouped["ctr"] = grouped["clicks"] / grouped["impressions"].replace(0, 1)
        low = grouped[grouped["ctr"] < 0.01]

        if low.empty:
            lg.info(json.dumps({"event": "no_low_ctr"}))
            return []

        payload = [{"campaign_name": r["campaign_name"], "ctr": float(r["ctr"])} for _, r in low.head(5).iterrows()]

        if not (self.llm and self.template):
            return self._fallback(low)

        try:
            def _invoke():
                prompt_text = self.template.format(low_ctr=payload)
                raw = self.llm.invoke(prompt_text)
                raw_text = raw if isinstance(raw, str) else getattr(raw, "content", "")
                return raw_text
            raw_text = retry(_invoke, attempts=self.config.get("retry", {}).get("attempts", 3), delay=self.config.get("retry", {}).get("delay", 1.0), agent="creative")
            parsed = safe_json(raw_text)
            if parsed and isinstance(parsed, dict) and "campaigns" in parsed:
                campaigns = parsed["campaigns"]
                # attach light confidence if present
                for c in campaigns:
                    if "confidence" not in c:
                        c["confidence"] = 0.5
                lg.info(json.dumps({"event": "creative_generated", "count": len(campaigns)}))
                return campaigns
            else:
                lg.error(json.dumps({"event": "creative_invalid_output"}))
                return self._fallback(low)
        except Exception as e:
            lg.error(json.dumps({"event": "creative_llm_failed", "error": str(e)}))
            return self._fallback(low)

    def _fallback(self, low_df: pd.DataFrame) -> List[CreativeIdea]:
        ideas = []
        for _, r in low_df.head(5).iterrows():
            cname = r["campaign_name"]
            rec = {"headline": f"Try benefit-driven headline for {cname}", "primary_text": "Highlight benefit + clear CTA.", "cta": "Learn More"}
            ideas.append({"campaign_name": cname, "issue": "Low CTR", "current_message": "", "recommendation": rec, "confidence": 0.4})
        log.info(json.dumps({"event": "creative_fallback_generated", "count": len(ideas)}))
        return ideas
