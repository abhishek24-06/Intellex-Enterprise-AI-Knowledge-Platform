from __future__ import annotations

from typing import Protocol, AsyncIterator


class LLMClient(Protocol):

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        ...

    async def generate_stream(self, *, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        """Stream the response token by token. Default implementation yields full response."""
        yield self.generate(system_prompt=system_prompt, user_prompt=user_prompt)