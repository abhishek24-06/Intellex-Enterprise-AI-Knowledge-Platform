from __future__ import annotations

from app.dto.multi_agent_response import (
    MultiAgentResponse,
)


class AgenticRAGService:

    def __init__(
        self,
        *,
        graph,
        max_retries: int = 2,
    ):
        if max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )

        self.graph = graph
        self.max_retries = max_retries

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
                "max_retries": self.max_retries,
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

        rag_result = result.get(
            "rag_result"
        )

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

    def evaluate(self,*,db,query: str,current_user) -> dict:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )
    
        normalized_query = query.strip()
    
        result = self.graph.invoke(
            {
                "original_query": normalized_query,
                "attempt": 0,
                "max_retries": self.max_retries,
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
    
        rag_result = result.get(
            "rag_result"
        )
    
        sources = (
            rag_result.sources
            if rag_result is not None
            else []
        )
    
        database_result = result.get(
            "database_result"
        )
    
        return {
            "answer": answer,
            "route": result.get("route"),
            "rag_result": rag_result,
            "sources": sources,
            "database_result": database_result,
            "critique": result.get("critique"),
            "attempt": result.get("attempt", 0),
            "history": result.get(
                "history",
                [],
            ),
        }