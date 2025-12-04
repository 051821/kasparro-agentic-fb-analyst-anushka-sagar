# src/agents/insight_agent.py (trimmed simplified)
import json, re
from typing import Optional, Any, List, Dict
from loguru import logger
from utils.logger import bind_trace
from utils.metrics import agent_metrics

log = logger.bind(agent="insight")

def normalize_payload(payload: Any) -> Optional[List[Dict]]:
    if not payload: return None
    items = payload.get("hypotheses") if isinstance(payload, dict) else payload
    if not isinstance(items, list): items = [items]
    out = []
    for i, h in enumerate(items, 1):
        if not isinstance(h, dict): continue
        out.append({
            "id": h.get("id", f"H{i}"),
            "driver": h.get("driver", "undetermined"),
            "hypothesis": h.get("hypothesis", h.get("description","")),
            "confidence": float(h.get("confidence") or 0.5)  # default confidence
        })
    return out or None

class InsightAgent:
    def __init__(self, cfg):
        self.cfg = cfg or {}
        log.info({"event":"insight_init"})

    @agent_metrics("insight")
    def generate(self, query: str, summary: Dict, trace_id: str = None) -> List[Dict]:
        lg = bind_trace(trace_id).bind(agent="insight")
        lg.info({"event":"insight_generate_request", "query": query})
        # fallback if no llm
        if not self.cfg.get("llm", {}).get("enable_llm", False):
            return [{"id":"H1","driver":"low_ctr","hypothesis":"CTR drop","confidence":0.4}]
        # actual LLM call omitted for short version
        return [{"id":"H1","driver":"low_ctr","hypothesis":"CTR drop","confidence":0.6}]
