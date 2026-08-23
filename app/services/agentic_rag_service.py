from __future__ import annotations
from uuid import uuid4

from app.dto.multi_agent_response import MultiAgentResponse
from app.dto.agent_execution import AgentExecutionEvent
class AgenticRAGService:

    def __init__(self,*,graph,max_retries: int = 2):
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative.")

        self.graph = graph
        self.max_retries = max_retries

    def answer(self,*,db,query: str,current_user) -> MultiAgentResponse:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        normalized_query = query.strip()

        request_id = str(uuid4())

        result = self.graph.invoke(
            {
                "original_query": normalized_query,
                "request_id": request_id,
                "attempt": 0,
                "max_retries": self.max_retries,
                "history": [],
            },
            context={
                "db": db,
                "current_user": current_user,
            },
        )

        answer = result.get("final_answer")

        if not answer:
            raise RuntimeError("Agentic RAG graph returned no final answer.")

        rag_result = result.get("rag_result")

        sources = (
            rag_result.sources
            if rag_result is not None
            else []
        )

        execution_trace = []

        for event in result.get(
            "history",
            [],
        ):

            if event.get(
                "node"
            ) != "agent_execution":
                continue

            execution_trace.append(
                AgentExecutionEvent(
                    request_id=event[
                        "request_id"
                    ],
                    agent_name=event[
                        "agent_name"
                    ],
                    route=event.get(
                        "route"
                    ),
                    attempt=event.get(
                        "attempt",
                        0,
                    ),
                    status=event[
                        "status"
                    ],
                    latency_ms=event[
                        "latency_ms"
                    ],
                    details=event.get(
                        "details",
                        {},
                    ),
                )
            )

        return MultiAgentResponse(
            query=normalized_query,
            answer=answer,
            sources=sources,
            execution_trace=execution_trace
        )


    def evaluate(self,*,db,query: str,current_user) -> dict:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
    
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
    
        answer = result.get("final_answer")
    
        if not answer:
            raise RuntimeError("Agentic RAG graph returned no final answer.")
    
        rag_result = result.get("rag_result")
    
        sources = (
            rag_result.sources
            if rag_result is not None
            else []
        )
    
        database_result = result.get("database_result")
    
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