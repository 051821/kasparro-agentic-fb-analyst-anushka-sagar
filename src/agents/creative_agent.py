from typing import Dict, Any, List

import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from utils.llm_client import get_llm
from utils.schemas import CreativeIdea, CreativeRecommendation


class CreativeAgent:
    def __init__(self, config: Dict[str, Any]):
        self.log = logger.bind(agent="creative")  # ← IMPORTANT
        self.config = config

        self.llm = get_llm(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"],
        )
        self.log.info("CreativeAgent LLM initialized successfully.")

        with open("prompts/creative_generator_prompt.md", "r", encoding="utf-8") as f:
            template = f.read()

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["low_ctr"],
        )
        self.parser = JsonOutputParser()


    def _find_low_ctr_campaigns(self, df: pd.DataFrame, ctr_threshold: float = 0.01) -> pd.DataFrame:
        self.log.debug(f"Finding low CTR campaigns with threshold {ctr_threshold}")
        grouped = (
            df.groupby("campaign_name")
            .agg(
                impressions=("impressions", "sum"),
                clicks=("clicks", "sum"),
                revenue=("revenue", "sum"),
                spend=("spend", "sum"),
            )
            .reset_index()
        )
        grouped["ctr"] = grouped["clicks"] / grouped["impressions"].replace(0, 1)
        low_df = grouped[grouped["ctr"] < ctr_threshold]
        self.log.info(f"Found {len(low_df)} low CTR campaigns.")
        return low_df


    def _fallback_creatives(self, df: pd.DataFrame, low_df: pd.DataFrame) -> List[CreativeIdea]:
        self.log.warning("Using fallback creative generation.")
        ideas: List[CreativeIdea] = []

        for _, row in low_df.head(5).iterrows():
            campaign_name = row["campaign_name"]
            cdf = df[df["campaign_name"] == campaign_name]
            current_message = (
                cdf["creative_message"].iloc[0]
                if "creative_message" in cdf.columns and not cdf.empty
                else ""
            )
            rec: CreativeRecommendation = {
                "headline": f"Refresh your {campaign_name} ads",
                "primary_text": "Test a new angle focusing on clarity, urgency and benefit.",
                "cta": "Shop Now",
            }
            ideas.append(
                {
                    "campaign_name": campaign_name,
                    "issue": "Low CTR vs global threshold",
                    "current_message": current_message,
                    "recommendation": rec,
                }
            )

        self.log.info(f"Generated {len(ideas)} fallback creative ideas.")
        return ideas


    def generate(self, df: pd.DataFrame) -> List[CreativeIdea]:
        self.log.info("Starting creative generation pipeline.")
        low_df = self._find_low_ctr_campaigns(df)

        if low_df.empty:
            self.log.warning("No low CTR campaigns found. Returning empty list.")
            return []

        payload = []
        for _, row in low_df.head(5).iterrows():
            campaign_name = row["campaign_name"]
            cdf = df[df["campaign_name"] == campaign_name]
            current_message = (
                cdf["creative_message"].iloc[0]
                if "creative_message" in cdf.columns and not cdf.empty
                else ""
            )
            payload.append(
                {
                    "campaign_name": campaign_name,
                    "ctr": float(row["ctr"]),
                    "current_message": current_message,
                }
            )

        self.log.debug(f"Payload for creative generation: {payload}")

        chain = self.prompt | self.llm | self.parser
        try:
            result = chain.invoke({"low_ctr": payload})
            self.log.info("CreativeAgent LLM produced valid creative ideas.")
            if isinstance(result, list):
                return result
        except Exception as e:
            self.log.error(f"CreativeAgent LLM failed, using fallback. Error: {e}")

        return self._fallback_creatives(df, low_df)
