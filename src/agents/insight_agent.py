# src/agents/insight_agent.py
import json
from typing import List, Dict
from loguru import logger
from utils.logger import bind_trace
from utils.metrics import agent_metrics
from utils.retry import retry
from utils.llm_client import get_llm

log = logger.bind(agent="insight")


class InsightAgent:
    def __init__(self, cfg):
        self.cfg = cfg or {}
        log.info({"event": "insight_init"})

        # Determine if LLM is enabled
        self.enable_llm = self.cfg.get("enable_llm", False)
        self.llm = None

        if self.enable_llm:
            try:
                llm_cfg = self.cfg.get("llm", {})
                self.llm = get_llm(
                    model=llm_cfg.get("model", "llama3.1"),
                    temperature=llm_cfg.get("temperature", 0.2),
                    format=llm_cfg.get("format", "json")
                )
            except Exception as e:
                log.error({"event": "insight_llm_init_failed", "error": str(e)})
                self.enable_llm = False

        # Load prompt file
        try:
            with open("prompts/insight_agent_prompt.md", "r", encoding="utf-8") as f:
                self.prompt = f.read()
        except Exception as e:
            log.error({"event": "insight_prompt_load_failed", "error": str(e)})
            self.prompt = None
            self.enable_llm = False

    @agent_metrics("insight")
    def generate(self, query: str, summary: Dict, trace_id: str = None) -> List[Dict]:
        lg = bind_trace(trace_id).bind(agent="insight")
        lg.info({"event": "insight_generate_request", "query": query})

        # Fallback if no LLM
        if not self.enable_llm or not self.llm or not self.prompt:
            lg.info({"event": "insight_fallback"})
            return [{
                "id": "H1",
                "driver": "low_ctr",
                "hypothesis": "CTR drop",
                "segment": "",
                "confidence": 0.4
            }]

        # Build prompt (NO .format())
        prompt_text = (
            self.prompt
                .replace("{query}", query)
                .replace("{summary}", json.dumps(summary))
        )

        # LLM CALL
        try:
            raw = retry(
                lambda: self.llm.invoke(prompt_text),
                attempts=3,
                delay=1.0,
                agent="insight"
            )
            raw_text = raw if isinstance(raw, str) else getattr(raw, "content", "")
            lg.info({"event": "insight_llm_raw", "raw": raw_text})

        except Exception as e:
            lg.error({"event": "insight_llm_failed", "error": str(e)})
            return self._fallback()

        # PARSE JSON
        try:
            parsed = json.loads(raw_text)
        except Exception:
            lg.warning({"event": "insight_json_parse_failed"})
            return self._fallback()

        # CASE 1: Model returned a LIST
        if isinstance(parsed, list):
            return parsed

        if isinstance(parsed, dict) and "hypotheses" in parsed:
            return parsed["hypotheses"]

        if isinstance(parsed, dict) and "id" in parsed and "hypothesis" in parsed:
            return [parsed]

        lg.warning({"event": "insight_invalid_json_structure"})
        return self._fallback()

    def _fallback(self):
        return [{
            "id": "H1",
            "driver": "insufficient_data",
            "hypothesis": "Not enough information to determine a performance driver.",
            "segment": "",
            "confidence": 0.25
        }]
