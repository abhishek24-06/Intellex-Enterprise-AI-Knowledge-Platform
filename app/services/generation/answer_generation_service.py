from __future__ import annotations

from app.dto.retrieved_chunk import RetrievedChunk
from app.services.generation.llm_client import LLMClient
from app.services.generation.prompt_builder import RAGPromptBuilder

class AnswerGenerationService:

    def __init__(self,*,llm_client: LLMClient,prompt_builder: RAGPromptBuilder | None = None):

        self.llm_client = llm_client
        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else RAGPromptBuilder()
        )

    def generate(self,*,query:str,chunks:list[RetrievedChunk]) -> str:

            if not query or not query.strip():
                raise ValueError("Query cannot be empty.")

            if not chunks:
                raise ValueError("At least one retrieved chunk is required.")

            system_prompt, user_prompt = (
                self.prompt_builder.build(
                    query=query,
                    chunks=chunks,
            )
        )
            answer = self.llm_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
        )
            if not answer or not answer.strip():
                raise RuntimeError("LLM returned an empty answer.")

            return answer.strip()