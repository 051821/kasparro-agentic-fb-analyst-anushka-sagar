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
        self.enable_llm = self.cfg.get("enable_llm", True)
        self.llm = None

        if self.enable_llm:
            try:
                llm_cfg = self.cfg.get("llm", {})
                self.llm = get_llm(
                    model=llm_cfg.get("model", "llama3.1"),
                    temperature=llm_cfg.get("temperature", 0.2),
                    format=llm_cfg.get("format", "json")
                )
                log.info({"event": "insight_llm_initialized"})
            except Exception as e:
                log.error({"event": "insight_llm_init_failed", "error": str(e)})
                self.enable_llm = False

        try:
            with open("prompts/insight_agent_prompt.md", "r", encoding="utf-8") as f:
                self.prompt = f.read()
            log.info({"event": "insight_prompt_loaded"})
        except Exception as e:
            log.error({"event": "insight_prompt_load_failed", "error": str(e)})
            self.prompt = None
            self.enable_llm = False

    @agent_metrics("insight")
    def generate(self, query: str, summary: Dict, trace_id: str = None) -> List[Dict]:
        lg = bind_trace(trace_id).bind(agent="insight")

        # Log input
        lg.info({
            "event": "insight_generate_request",
            "trace_id": trace_id,
            "query": query,
            "summary_keys": list(summary.keys())
        })

        if not self.enable_llm or not self.llm or not self.prompt:
            lg.warning({
                "event": "insight_fallback_triggered",
                "trace_id": trace_id,
                "reason": "LLM_disabled_or_prompt_missing"
            })
            return self._fallback()

        prompt_text = (
            self.prompt
                .replace("{query}", query)
                .replace("{summary}", json.dumps(summary))
        )
        lg.info({
            "event": "insight_prompt_built",
            "trace_id": trace_id,
            "prompt_preview": prompt_text[:120]
        })

        try:
            raw = retry(
                lambda: self.llm.invoke(prompt_text),
                attempts=3,
                delay=1.0,
                agent="insight"
            )

            raw_text = raw if isinstance(raw, str) else getattr(raw, "content", "")
            lg.info({
                "event": "insight_llm_output_received",
                "trace_id": trace_id,
                "raw_preview": raw_text[:150],
                "raw_length": len(raw_text)
            })

        except Exception as e:
            lg.error({
                "event": "insight_llm_failed",
                "trace_id": trace_id,
                "error": str(e)
            })
            return self._fallback()

        try:
            parsed = json.loads(raw_text)
        except Exception:
            lg.warning({
                "event": "insight_json_parse_failed",
                "trace_id": trace_id
            })
            return self._fallback()

        if isinstance(parsed, list):
            lg.info({
                "event": "insight_json_parsed",
                "trace_id": trace_id,
                "num_hypotheses": len(parsed)
            })
            return parsed

        if isinstance(parsed, dict) and "hypotheses" in parsed:
            hyps = parsed["hypotheses"]
            lg.info({
                "event": "insight_json_parsed_dict_list",
                "trace_id": trace_id,
                "num_hypotheses": len(hyps)
            })
            return hyps

        if isinstance(parsed, dict) and "id" in parsed and "hypothesis" in parsed:
            lg.info({
                "event": "insight_single_hypothesis_parsed",
                "trace_id": trace_id,
                "confidence": parsed.get("confidence")
            })
            return [parsed]

        lg.warning({
            "event": "insight_invalid_json_structure",
            "trace_id": trace_id,
            "type": type(parsed).__name__
        })
        return self._fallback()

    def _fallback(self):
        return [{
            "id": "H1",
            "driver": "insufficient_data",
            "hypothesis": "Not enough information to determine a performance driver.",
            "segment": "",
            "confidence": 0.25
        }]
