from __future__ import annotations

import os

from openai import OpenAI


class OpenRouterClient:
    """
    Application-level text generation client.

    All LLM generation in Intellex should go through this
    abstraction rather than calling a provider SDK directly.
    """

    DEFAULT_BASE_URL = (
        "https://openrouter.ai/api/v1"
    )

    DEFAULT_MODEL = (
        "google/gemini-2.5-flash"
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_tokens: int = 1024
    ):
        resolved_api_key = (
            api_key
            or os.getenv("OPENROUTER_API_KEY")
        )

        if not resolved_api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not configured."
            )

        self.model = (
            model
            or os.getenv(
                "OPENROUTER_MODEL",
                self.DEFAULT_MODEL,
            )
        )

        self.client = OpenAI(
            api_key=resolved_api_key,
            base_url=(
                base_url
                or os.getenv(
                    "OPENROUTER_BASE_URL",
                    self.DEFAULT_BASE_URL,
                )
            ),
            timeout=timeout,
        )
        self.max_tokens = max_tokens

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
                     model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        },
                    ],
                    max_tokens=self.max_tokens,
                )

        if not response.choices:
            raise RuntimeError(
                "OpenRouter returned no choices."
            )

        content = (
            response.choices[0]
            .message
            .content
        )

        if not content:
            raise RuntimeError(
                "OpenRouter returned an empty response."
            )

        return content