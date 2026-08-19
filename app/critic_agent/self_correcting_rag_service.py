from __future__ import annotations

from app.critic_agent.critic_agent import CriticAgent,CriticDecision
from app.dto.rag_response import RAGResult

class SelfCorrectingRAGService:

    def __init__(self,*,rag_service,critic_agent:CriticAgent,max_retries:int = 2):

        if max_retries < 0:
            raise ValueError("max_retries cannot be negative.")

        self.rag_service = rag_service
        self.critic_agent = critic_agent
        self.max_retries = max_retries

    def answer(self,*,db,query:str,current_user)->RAGResult:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        current_query = query.strip()

        last_result: RAGResult | None = None

        for attempt in range(
            self.max_retries + 1
        ):

            result = self.rag_service.answer(
                db=db,
                query=current_query,
                current_user=current_user
            )

            last_result = result

            if not result.sources:
                return result

            critique = self.critique_agent.evaluate(
                query=current_query,
                answer=result.answer,
                chunks=result.sources
            )
            if (
                critique.decision
                == CriticDecision.ACCEPT
            ):
                return result

            # No more retries available.
            if attempt >= self.max_retries:
                return result

            next_query = (
                critique.improved_query.strip()
                if critique.improved_query
                else current_query
            )

            # Safety against useless retry loops.
            if next_query == current_query:
                return result

            current_query = next_query

        # Defensive fallback.
        assert last_result is not None
        return last_result


