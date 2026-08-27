import os
import asyncio
from typing import AsyncIterator

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.generation.llm_factory import get_chat_model
from app.services.generation.llm_client import LLMClient

load_dotenv()


class ProviderLLMClient:
    """LLM client using LangChain with both sync and async streaming support."""

    def __init__(
        self,
        *,
        model: BaseChatModel | None = None,
        temperature: float = 0.0,
    ):
        self.model = model or get_chat_model(
            temperature=temperature,
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        kwargs = {
            "max_tokens": max_tokens,
        }

        if response_format is not None:
            kwargs["response_format"] = response_format

        response = self.model.invoke(
            messages,
            **kwargs,
        )

        print("\n========== LLM RESPONSE DEBUG ==========")
        print("Response type:", type(response))
        print("Content:", repr(getattr(response, "content", None)))
        print(
            "Additional kwargs:",
            getattr(response, "additional_kwargs", None),
        )
        print(
            "Response metadata:",
            getattr(response, "response_metadata", None),
        )
        print("Usage metadata:", getattr(response, "usage_metadata", None))
        print("========================================\n")

        content = getattr(
            response,
            "content",
            None,
        )

        if not content:
            raise RuntimeError(
                "LLM provider returned an empty response."
            )

        return content

    async def generate_stream(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> AsyncIterator[str]:
        """Stream the response token by token using LangChain's astream."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        kwargs = {
            "max_tokens": max_tokens,
        }

        if response_format is not None:
            kwargs["response_format"] = response_format

        # Use LangChain's astream for true async streaming
        async for chunk in self.model.astream(messages, **kwargs):
            content = getattr(chunk, "content", None)
            if content:
                yield content