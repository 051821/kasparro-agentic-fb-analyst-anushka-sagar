from typing import Dict, Any
import json
import os

from agents.planner_agent import PlannerAgent
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.eval_agent import EvalAgent
from agents.creative_agent import CreativeAgent
from utils.logger import logger
from utils.schemas import InsightsList, CreativesList


class AgentController:
 

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.planner = PlannerAgent(config)
        self.data_agent = DataAgent()
        self.insight_agent = InsightAgent(config)
        self.eval_agent = EvalAgent()
        self.creative_agent = CreativeAgent(config)

    def run(self, query: str) -> Dict[str, Any]:
        logger.info(f"Received query: {query}")

        plan = self.planner.plan(query)
        logger.info(f"Planner output: {plan}")

        data_bundle = self.data_agent.run(self.config)
        df = data_bundle["df"]
        summary = data_bundle["summary"]
        logger.info("Data loaded and summarized.")

        hypotheses = self.insight_agent.generate(query, summary)
        logger.info(f"Generated {len(hypotheses)} hypotheses.")

        thresholds = self.config.get("thresholds", {})
        insights: InsightsList = self.eval_agent.evaluate(df, hypotheses, thresholds)
        logger.info(f"Evaluated {len(insights)} hypotheses.")

        creatives: CreativesList = self.creative_agent.generate(df)
        logger.info(f"Generated {len(creatives)} creative ideas.")

        self._save_outputs(insights, creatives)

        return {"insights": insights, "creatives": creatives}

    def _save_outputs(self, insights: InsightsList, creatives: CreativesList) -> None:
        report_dir = self.config["paths"].get("report_dir", "reports")
        os.makedirs(report_dir, exist_ok=True)

        insights_path = os.path.join(report_dir, "insights.json")
        creatives_path = os.path.join(report_dir, "creatives.json")
        report_md_path = os.path.join(report_dir, "report.md")

        with open(insights_path, "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2)

        with open(creatives_path, "w", encoding="utf-8") as f:
            json.dump(creatives, f, indent=2)

        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write("# Facebook Ads Performance Report\n\n")
            f.write("## Key Insights\n\n")
            if not insights:
                f.write("- No significant ROAS changes detected based on thresholds.\n")
            else:
                for ins in insights:
                    ev = ins["evidence"]
                    f.write(
                        f"- **{ins['driver']}** in segment `{ins['segment']}` "
                        f"(confidence: {ins['confidence']:.2f}) — "
                        f"ROAS change: {ev['roas_change_pct']:.2%}, "
                        f"CTR change: {ev['ctr_change_pct']:.2%}\n"
                    )

            f.write("\n## Creative Recommendations\n\n")
            if not creatives:
                f.write("No low-CTR campaigns detected above the volume threshold.\n")
            else:
                for c in creatives:
                    rec = c["recommendation"]
                    f.write(
                        f"- **{c['campaign_name']}**\n"
                        f"  - Issue: {c['issue']}\n"
                        f"  - Current: {c['current_message']}\n"
                        f"  - Headline: {rec['headline']}\n"
                        f"  - Primary: {rec['primary_text']}\n"
                        f"  - CTA: {rec['cta']}\n\n"
                    )

        logger.info(f"Saved outputs to {report_dir}")
