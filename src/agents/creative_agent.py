from typing import Dict, Any, List

import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from utils.llm_client import get_llm
from utils.schemas import CreativeIdea, CreativeRecommendation


class CreativeAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = get_llm(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"],
        )
        with open("prompts/creative_generator_prompt.md", "r", encoding="utf-8") as f:
            template = f.read()
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["low_ctr"],
        )
        self.parser = JsonOutputParser()

    def _find_low_ctr_campaigns(self, df: pd.DataFrame, ctr_threshold: float = 0.01) -> pd.DataFrame:
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
        return grouped[grouped["ctr"] < ctr_threshold]

    def _fallback_creatives(self, df: pd.DataFrame, low_df: pd.DataFrame) -> List[CreativeIdea]:
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
                "primary_text": "Test a new angle that focuses on clear value, comfort, and urgency, with strong first-line hooks.",
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
        return ideas

    def generate(self, df: pd.DataFrame) -> List[CreativeIdea]:
        low_df = self._find_low_ctr_campaigns(df)
        if low_df.empty:
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

        chain = self.prompt | self.llm | self.parser
        try:
            result = chain.invoke({"low_ctr": payload})
            if isinstance(result, list):
                return result  # type: ignore[return-value]
        except Exception as e:
            logger.error(f"CreativeAgent LLM failed, using fallback creatives. Error: {e}")

        return self._fallback_creatives(df, low_df)
