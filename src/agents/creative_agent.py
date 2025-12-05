# src/agents/creative_agent.py
import json
from typing import Dict, Any, List
import pandas as pd
from loguru import logger

from utils.llm_client import get_llm
from utils.retry import retry
from utils.metrics import agent_metrics
from utils.logger import bind_trace

log = logger.bind(agent="creative")


def safe_json(text: str):
    if not text or not isinstance(text, str):
        return None

    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    start_brace = text.find("{")
    start_bracket = text.find("[")

    if start_brace == -1 and start_bracket == -1:
        return None

    start = min(x for x in [start_brace, start_bracket] if x != -1)
    raw = text[start:].strip()

    try:
        return json.loads(raw)
    except:
        return None


def normalize_creatives(lst):
    for c in lst:
        c.setdefault("issue", "low_ctr")
        c.setdefault("diagnosed_driver", "generic_performance_issue")
        rec = c.setdefault("recommendation", {})
        rec.setdefault("headline", "")
        rec.setdefault("primary_text", "")
        rec.setdefault("cta", "Learn More")
    return lst


class CreativeAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enable_llm = config.get("enable_llm", True)
        self.llm = None

        if self.enable_llm:
            try:
                llm_cfg = config.get("llm", {})
                self.llm = get_llm(
                    model=llm_cfg.get("model", "llama3.1"),
                    temperature=llm_cfg.get("temperature", 0.0),
                    format=llm_cfg.get("format", "json")
                )
                log.info({"event": "creative_llm_initialized"})
            except Exception as e:
                log.error({"event": "creative_llm_init_failed", "error": str(e)})
                self.enable_llm = False

        # Load template
        try:
            with open("prompts/creative_generator_prompt.md", "r", encoding="utf-8") as f:
                self.template = f.read()
            log.info({"event": "creative_prompt_loaded"})
        except Exception as e:
            log.error({"event": "creative_prompt_load_failed", "error": str(e)})
            self.template = None
            self.enable_llm = False

    @agent_metrics("creative")
    def generate(self, df: pd.DataFrame, trace_id: str = None) -> List[Dict]:
        lg = bind_trace(trace_id).bind(agent="creative")
        grouped = df.groupby("campaign_name").agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            spend=("spend", "sum")
        ).reset_index()

        grouped["ctr"] = grouped["clicks"] / grouped["impressions"].replace(0, 1)
        low = grouped[grouped["ctr"] < 0.01]

        lg.info({
            "event": "creative_low_ctr_detected",
            "trace_id": trace_id,
            "num_low_ctr_campaigns": len(low),
            "campaigns": low["campaign_name"].tolist()
        })

        if low.empty:
            lg.info({
                "event": "creative_no_low_ctr_campaigns",
                "trace_id": trace_id
            })
            return []

        payload = [
            {"campaign_name": r["campaign_name"], "ctr": float(r["ctr"])}
            for _, r in low.head(5).iterrows()
        ]
        if not self.enable_llm or not self.template:
            lg.warning({
                "event": "creative_fallback_triggered",
                "reason": "LLM_disabled_or_missing_prompt",
                "trace_id": trace_id
            })
            return self._fallback(low)

        prompt_text = self.template.replace("{low_ctr}", json.dumps(payload))
        lg.info({
            "event": "creative_prompt_built",
            "trace_id": trace_id,
            "prompt_preview": prompt_text[:120]
        })
        try:
            raw = retry(
                lambda: self.llm.invoke(prompt_text),
                attempts=3,
                delay=1.0,
                agent="creative"
            )
            raw_text = raw if isinstance(raw, str) else getattr(raw, "content", "")

            lg.info({
                "event": "creative_llm_output_received",
                "trace_id": trace_id,
                "raw_preview": raw_text[:150],
                "raw_length": len(raw_text)
            })

        except Exception as e:
            lg.error({
                "event": "creative_llm_failed",
                "trace_id": trace_id,
                "error": str(e)
            })
            return self._fallback(low)
        parsed = safe_json(raw_text)

        if isinstance(parsed, list):
            lg.info({
                "event": "creative_json_parsed_array",
                "trace_id": trace_id,
                "count": len(parsed)
            })
            return normalize_creatives(parsed)

        if isinstance(parsed, dict) and "campaigns" in parsed:
            lg.info({
                "event": "creative_json_parsed_dict_list",
                "trace_id": trace_id,
                "count": len(parsed["campaigns"])
            })
            return normalize_creatives(parsed["campaigns"])

        if isinstance(parsed, dict) and "campaign_name" in parsed:
            lg.info({
                "event": "creative_single_object_parsed",
                "trace_id": trace_id,
                "campaign_name": parsed["campaign_name"]
            })
            return normalize_creatives([parsed])

        lg.error({
            "event": "creative_invalid_output",
            "trace_id": trace_id,
            "raw": raw_text
        })
        return self._fallback(low)
    def _fallback(self, low_df: pd.DataFrame):
        ideas = []
        for _, r in low_df.head(5).iterrows():
            ideas.append({
                "campaign_name": r["campaign_name"],
                "issue": "low_ctr",
                "diagnosed_driver": "generic_performance_issue",
                "recommendation": {
                    "headline": f"Improve hook for {r['campaign_name']}",
                    "primary_text": "Use a stronger lead benefit and simplify message.",
                    "cta": "Learn More"
                }
            })
        return ideas
