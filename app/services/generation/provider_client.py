import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

from app.services.generation.llm_factory import get_chat_model

load_dotenv()


class ProviderLLMClient:

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
        max_tokens: int = 1024,
        response_format: dict | None = None,
    ) -> str:
    
        messages = [
            (
                "system",
                system_prompt,
            ),
            (
                "human",
                user_prompt,
            ),
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