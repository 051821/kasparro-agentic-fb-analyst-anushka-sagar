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
    """Robust JSON extractor supporting arrays, objects, and single-object output."""
    if not text or not isinstance(text, str):
        return None

    text = text.strip()

    # Try direct load first
    try:
        return json.loads(text)
    except:
        pass

    # Extract from first JSON bracket
    start_brace = text.find("{")
    start_bracket = text.find("[")

    if start_brace == -1 and start_bracket == -1:
        return None

    start = min(x for x in [start_brace, start_bracket] if x != -1)
    raw = text[start:].strip()

    # Try loading again
    try:
        return json.loads(raw)
    except:
        return None


def normalize_creatives(lst):
    """Normalize creative objects to ensure required fields exist."""
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
        self.enable_llm = config.get("enable_llm", False)
        self.llm = None

        if self.enable_llm:
            try:
                llm_cfg = config.get("llm", {})
                self.llm = get_llm(
                    model=llm_cfg.get("model", "llama3.1"),
                    temperature=llm_cfg.get("temperature", 0.0),
                    format=llm_cfg.get("format", "json")
                )
            except:
                self.enable_llm = False

        # Load template
        try:
            with open("prompts/creative_generator_prompt.md", "r", encoding="utf-8") as f:
                self.template = f.read()
        except:
            self.template = None
            self.enable_llm = False

    @agent_metrics("creative")
    def generate(self, df: pd.DataFrame, trace_id: str = None) -> List[Dict]:
        lg = bind_trace(trace_id).bind(agent="creative")

        # Identify low-CTR campaigns
        grouped = df.groupby("campaign_name").agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            spend=("spend", "sum")
        ).reset_index()

        grouped["ctr"] = grouped["clicks"] / grouped["impressions"].replace(0, 1)
        low = grouped[grouped["ctr"] < 0.01]

        if low.empty:
            return []

        payload = [
            {"campaign_name": r["campaign_name"], "ctr": float(r["ctr"])}
            for _, r in low.head(5).iterrows()
        ]

        # FALLBACK if LLM disabled
        if not self.enable_llm or not self.template:
            return self._fallback(low)

        # Build prompt
        prompt_text = self.template.replace("{low_ctr}", json.dumps(payload))

        # LLM CALL
        try:
            raw = retry(lambda: self.llm.invoke(prompt_text), attempts=3, delay=1.0, agent="creative")
            raw_text = raw if isinstance(raw, str) else getattr(raw, "content", "")
        except Exception:
            return self._fallback(low)

        # Parse JSON
        parsed = safe_json(raw_text)

        # CASE 1: JSON array
        if isinstance(parsed, list):
            return normalize_creatives(parsed)

        # CASE 2: dict with campaigns
        if isinstance(parsed, dict) and "campaigns" in parsed:
            return normalize_creatives(parsed["campaigns"])

        # CASE 3: SINGLE creative object
        if isinstance(parsed, dict) and "campaign_name" in parsed:
            return normalize_creatives([parsed])

        # INVALID → fallback
        lg.error({"event": "creative_invalid_output", "raw": raw_text})
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
