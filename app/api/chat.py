from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncIterator
import json
import asyncio

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.rag import get_rag_service
from app.dependencies.agentic_rag import get_agentic_rag_service
from app.dto.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSource,
)
from app.models.users import User
from app.services.rag.rag_service import RAGService
from app.services.agentic_rag_service import AgenticRAGService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/query",
    response_model=ChatQueryResponse,
)
def query_knowledge_base(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatQueryResponse:

    result = rag_service.answer(
        db=db,
        query=request.query,
        current_user=current_user,
    )

    sources: list[ChatSource] = []

    seen_document_ids: set[int] = set()

    for chunk in result.sources:

        if chunk.document_id in seen_document_ids:
            continue

        seen_document_ids.add(chunk.document_id)

        sources.append(
            ChatSource(
                document_id=chunk.document_id,
                original_filename=chunk.original_filename,
            )
        )

    return ChatQueryResponse(
        query=result.query,
        answer=result.answer,
        sources=sources,
    )


@router.post(
    "/query/stream",
)
async def query_knowledge_base_stream(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
    agentic_rag_service: AgenticRAGService = Depends(get_agentic_rag_service),
):
    """
    Stream the chat response using Server-Sent Events (SSE).

    The stream yields JSON objects with the following structure:
    - {"type": "metadata", "sources": [...]} - Initial metadata with sources
    - {"type": "token", "content": "..."} - Individual tokens
    - {"type": "done"} - End of stream
    """

    async def generate_stream() -> AsyncIterator[str]:
        # First, run the full agentic RAG pipeline to get the answer and sources
        # This is the non-streaming part (retrieval, synthesis, etc.)
        result = agentic_rag_service.answer(
            db=db,
            query=request.query,
            current_user=current_user,
        )

        # Send metadata with sources first
        sources = []
        seen_document_ids: set[int] = set()

        # Get sources from the execution trace
        for event in result.execution_trace:
            if event.agent_name == "knowledge_agent" and event.details.get("retrieved_documents"):
                # We'll need to fetch sources differently - for now send empty
                pass

        metadata = {
            "type": "metadata",
            "query": result.query,
            "sources": sources,
        }
        yield f"data: {json.dumps(metadata)}\n\n"

        # Now stream the final answer using the synthesis/generation LLM
        # We need to reconstruct the prompt that would be sent to the LLM
        # For simplicity, we'll stream the already-computed answer token by token
        # In a full implementation, we'd stream the actual LLM call
        answer = result.answer

        # Simulate token streaming by yielding words
        words = answer.split()
        for i, word in enumerate(words):
            token_data = {
                "type": "token",
                "content": word + (" " if i < len(words) - 1 else ""),
            }
            yield f"data: {json.dumps(token_data)}\n\n"
            # Small delay to simulate streaming
            await asyncio.sleep(0.01)

        # End marker
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )