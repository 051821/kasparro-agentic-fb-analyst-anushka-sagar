from typing import Dict, Any
import re
from loguru import logger as _log
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from utils.llm_client import get_llm
from utils.retry import retry
from utils.metrics import agent_metrics
from utils.logger import bind_trace

_log = _log

class PlannerAgent:
    def __init__(self, config: Dict[str, Any] | None = None):
        self.log = _log.bind(agent="plan")
        self.config = config or {}
        self.log.debug({"event": "planner_init", "config_keys": list(self.config.keys())})

        if self.config.get("enable_llm", True):
            try:
                llm_cfg = self.config.get("llm", {})
                self.llm = get_llm(
                    model=llm_cfg.get("model", "llama3.1"),
                    temperature=llm_cfg.get("temperature", 0.1),
                )
                self.log.info({"event": "planner_llm_initialized"})
            except Exception as e:
                self.log.error({"event": "planner_llm_init_failed", "error": str(e)})
                self.llm = None
        else:
            self.llm = None
            self.log.info({"event": "planner_llm_disabled"})

        try:
            with open("prompts/Planner.md", "r", encoding="utf-8") as f:
                template_text = f.read()
            self.prompt = PromptTemplate(template=template_text, input_variables=["query"])
            self.log.debug({"event": "planner_prompt_loaded"})
        except Exception as e:
            self.log.error({"event": "planner_prompt_load_failed", "error": str(e)})
            self.prompt = None

        self.parser = JsonOutputParser()
    @agent_metrics("plan")
    def plan(self, query: str, trace_id: str = None) -> Dict[str, Any]:
        log = bind_trace(trace_id).bind(agent="plan")

        log.info({
            "event": "planner_received_query",
            "trace_id": trace_id,
            "query": query
        })

        if not self.llm or not self.prompt:
            log.warning({
                "event": "planner_fallback_triggered",
                "trace_id": trace_id,
                "reason": "LLM_disabled_or_missing_prompt"
            })
            return self._fallback_plan(query)

        chain = self.prompt | self.llm | self.parser

        log.debug({
            "event": "planner_prompt_built",
            "trace_id": trace_id,
            "prompt_preview": self.prompt.template[:150]
        })
        try:
            result = retry(
                lambda: chain.invoke({"query": query}),
                attempts=self.config.get("retry", {}).get("attempts", 3),
                delay=self.config.get("retry", {}).get("delay", 1.0),
                agent="plan"
            )

            log.info({
                "event": "planner_llm_output_received",
                "trace_id": trace_id,
                "raw_preview": str(result)[:200]
            })

        except Exception as e:
            log.error({
                "event": "planner_llm_failure",
                "trace_id": trace_id,
                "error": str(e)
            })
            return self._fallback_plan(query)

        if not isinstance(result, dict):
            log.error({
                "event": "planner_invalid_output_type",
                "trace_id": trace_id,
                "output_type": str(type(result))
            })
            return self._fallback_plan(query)

        # Check required fields
        required = ["summary", "metrics", "segments", "hypotheses"]
        missing = [k for k in required if k not in result]

        if missing:
            log.warning({
                "event": "planner_missing_required_fields",
                "trace_id": trace_id,
                "missing": missing
            })
        else:
            log.info({
                "event": "planner_output_structure_validated",
                "trace_id": trace_id,
                "metrics_count": len(result.get("metrics", [])),
                "segments_count": len(result.get("segments", [])),
                "hypotheses_count": len(result.get("hypotheses", [])),
            })

        log.info({"event": "planner_success", "trace_id": trace_id})
        return result

    def _fallback_plan(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        time_window = "auto"

        match = re.search(r"last\s+(\d+)\s+day", q)
        if match:
            days = match.group(1)
            time_window = f"last_{days}_days"

        plan = {
            "original_query": query,
            "task": "analyze_roas_change",
            "steps": [
                "load_data",
                "summarize_dataset",
                "generate_hypotheses",
                "evaluate_hypotheses",
                "generate_creatives_for_low_ctr",
                "write_report",
            ],
            "focus": {
                "time_window": time_window,
                "filters": {
                    "campaign_name_contains": [],
                    "country_in": [],
                    "audience_type_in": [],
                },
            },
        }

        self.log.info({
            "event": "planner_fallback_plan_generated",
            "reason": "LLM_unavailable_or_failed",
            "plan": plan
        })

        return plan
