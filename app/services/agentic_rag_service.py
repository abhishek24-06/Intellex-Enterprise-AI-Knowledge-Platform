from __future__ import annotations

from app.dto.multi_agent_response import (
    MultiAgentResponse,
)


class AgenticRAGService:

    def __init__(
        self,
        *,
        graph,
    ):
        self.graph = graph

    def answer(
        self,
        *,
        db,
        query: str,
        current_user,
    ) -> MultiAgentResponse:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        normalized_query = query.strip()

        result = self.graph.invoke(
            {
                "original_query": normalized_query,
                "attempt": 0,
                "max_retries": 2,
                "history": [],
            },
            context={
                "db": db,
                "current_user": current_user,
            },
        )

        answer = result.get(
            "final_answer"
        )

        if not answer:
            raise RuntimeError(
                "Agentic RAG graph returned no final answer."
            )

        rag_result = result.get("rag_result")

        sources = (
            rag_result.sources
            if rag_result is not None
            else []
        )
        
        return MultiAgentResponse(
            query=normalized_query,
            answer=answer,
            sources=sources,
        )