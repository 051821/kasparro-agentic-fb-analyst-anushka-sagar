# src/agents/insight_agent.py
import json
import re
from typing import Any, Dict, List, Optional

from loguru import logger
from langchain_core.prompts import PromptTemplate

from utils.llm_client import get_llm
from utils.retry import retry
from utils.metrics import agent_metrics
from utils.logger import bind_trace

log = logger.bind(agent="insight")


def safe_extract_json(text: str):
    """Extract JSON even from extremely broken text. Always returns dict/list."""
    if not text:
        return None

    # Try simple extraction
    m = re.search(r"[\{\[][^\0]*", text, re.DOTALL)
    raw = m.group(0) if m else None

    if raw:
        raw = re.sub(r",\s*([\]}])", r"\1", raw)  # remove trailing commas

        # Balance braces
        while raw.count("{") > raw.count("}"):
            raw += "}"
        while raw.count("[") > raw.count("]"):
            raw += "]"

        try:
            return json.loads(raw)
        except Exception:
            pass

    if "hypotheses" in text:
        return {
            "hypotheses": [
                {"id": "H1", "driver": "unknown", "hypothesis": "Unknown issue"}
            ]
        }

    return None


def normalize_payload(payload: Any) -> Optional[List[Dict[str, Any]]]:
    """Turn raw JSON payload into list of hypotheses."""
    if payload is None:
        return None

    # Various valid shapes
    if isinstance(payload, dict) and isinstance(payload.get("hypotheses"), list):
        items = payload["hypotheses"]
    elif isinstance(payload, list):
        items = payload
    else:
        return None

    out = []
    for i, h in enumerate(items, start=1):
        if not isinstance(h, dict):
            continue
        out.append({
            "id": h.get("id", f"H{i}"),
            "driver": h.get("driver", h.get("metric", "unknown")),
            "hypothesis": h.get("hypothesis", h.get("description", "")),
            "segment_name": h.get("segment_name", h.get("segment", "All Campaigns")),
            "segment_filters": h.get("segment_filters", {})
        })
    return out or None



class InsightAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}

        # Load LLM (optional)
        llm_cfg = self.config.get("llm", {})
        if llm_cfg.get("enable_llm", False):
            self.llm = get_llm(
                model=llm_cfg.get("model"),
                temperature=llm_cfg.get("temperature", 0.0)
            )
        else:
            self.llm = None

        # Load prompt (optional)
        try:
            path = self.config.get("prompt_path", "prompts/insight_agent_prompt.md")
            with open(path, "r", encoding="utf-8") as f:
                template = f.read()
            self.prompt = PromptTemplate(
                template=template,
                input_variables=["query", "summary"],
                template_format="f-string"
            )
        except:
            self.prompt = None

        log.info({"event": "insight_agent_init"})

    # -----------------------------------------------------------
    @agent_metrics("insight")
    def generate(self, query: str, summary: Dict[str, Any], trace_id: str = None) -> List[Dict[str, Any]]:

        logger_ = bind_trace(trace_id).bind(agent="insight")
        logger_.info(json.dumps({"event": "insight_generate_request", "query": query}))

        # If no LLM → fallback
        if not (self.llm and self.prompt):
            logger_.warning(json.dumps({"event": "fallback_triggered"}))
            return self._fallback()

        # Build prompt
        try:
            prompt_text = self.prompt.format(query=query, summary=summary)
        except:
            return self._fallback()

        # LLM
        try:
            def ask():
                raw = self.llm.invoke(prompt_text)
                return raw if isinstance(raw, str) else raw.content

            raw_text = retry(ask, attempts=2, delay=1.0, agent="insight")
        except:
            return self._fallback()

        # Repair JSON
        payload = safe_extract_json(raw_text)
        normalized = normalize_payload(payload)

        if normalized:
            return normalized
        return self._fallback()

    def _fallback(self) -> List[Dict[str, Any]]:
        """Very small, simple fallback."""
        return [{
            "id": "H1",
            "driver": "low_ctr",
            "hypothesis": "ROAS drop driven by CTR decline",
            "segment_name": "All Campaigns",
            "segment_filters": {}
        }]
