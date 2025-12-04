# src/utils/llm_client.py
from langchain_community.chat_models import ChatOllama

def get_llm(model: str, temperature: float = 0.0, format: str = "json"):
    return ChatOllama(
        model=model,
        temperature=temperature,
        format=format   
    )
