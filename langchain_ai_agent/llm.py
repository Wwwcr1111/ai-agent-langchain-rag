import os

from langchain_openai import ChatOpenAI


DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def get_llm(*, temperature: float = 0.3, max_tokens: int = 1024) -> ChatOpenAI:
    api_key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or "missing-deepseek-api-key"
    )

    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
    )
