from __future__ import annotations

import os

from langchain_openrouter import ChatOpenRouter

from app.services.generation.openrouter_client import (
    OpenRouterClient,
)


def get_openrouter_client() -> OpenRouterClient:
    return OpenRouterClient(
        model=os.getenv(
            "OPENROUTER_MODEL",
            "z-ai/glm-5.2:free",
        )
    )

def get_openrouter_chat_model(
    *,
    model: str | None = None,
    temperature: float = 0.0,
) -> ChatOpenRouter:

    return ChatOpenRouter(
        model=(
            model
            or os.getenv(
                "OPENROUTER_DATABASE_MODEL",
                "z-ai/glm-5.2:free",
            )
        ),
        temperature=temperature,
        max_tokens=2048,
        api_key=os.environ[
            "OPENROUTER_API_KEY"
        ],
    )