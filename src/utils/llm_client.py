from langchain_community.llms import Ollama


def get_llm(model: str = "llama3.1", temperature: float = 0.2):
    return Ollama(
        model=model,
        temperature=temperature,
        keep_alive="5m",  # keep the model warm for repeated calls
    )
