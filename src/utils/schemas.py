from typing import TypedDict, List, Dict, Any


class Hypothesis(TypedDict):
    id: str
    driver: str
    description: str
    segment: str
    expected_signals: List[str]


class EvaluatedHypothesis(TypedDict):
    id: str
    driver: str
    description: str
    segment: str
    confidence: float
    evidence: Dict[str, Any]


class CreativeRecommendation(TypedDict):
    headline: str
    primary_text: str
    cta: str


class CreativeIdea(TypedDict):
    campaign_name: str
    issue: str
    current_message: str
    recommendation: CreativeRecommendation


InsightsList = List[EvaluatedHypothesis]
CreativesList = List[CreativeIdea]
