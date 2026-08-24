import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

from app.services.generation.openrouter_models import (
    get_openrouter_chat_model,
)

load_dotenv()


def get_chat_model(
    *,
    temperature: float = 0.0,
) -> BaseChatModel:

    provider = os.getenv(
        "LLM_PROVIDER",
        "openrouter",
    ).lower()

    if provider == "openrouter":
        return get_openrouter_chat_model(
            temperature=temperature,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile",
        )

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = os.getenv(
            "OLLAMA_MODEL",
            "qwen3:8b",
        )

        return ChatOllama(
            model=model,
            temperature=temperature,
        )

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER: {provider}"
    )