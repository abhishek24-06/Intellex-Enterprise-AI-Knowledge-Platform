from __future__ import annotations

from app.services.generation.llm_client import LLMClient

class QueryContextualizer:

    SYSTEM_PROMPT = """\
        You rewrite conversational questions into standalone search queries.
        
        Rules:
        1. Preserve the user's intent.
        2. Use conversation history only to resolve references such as
           "it", "they", "that policy", or "how do I apply".
        3. Do not answer the question.
        4. Do not invent facts.
        5. Return only the standalone query.
        """

    def __init__(self,*,llm_client:LLMClient):

        self.llm_client = llm_client

    def contextualize(self,*,query:str,history:list[tuple[tuple[str,str]]])->str:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        query = query.strip()

        if not history:
            return query

        if len(history) > 0 and self._is_standalone_query(query):
            return query

        history_text = "\n\n".join(
            f"USER:{question}\nASSISTANT: {answer}"
            for question, answer in history
        )

        user_prompt = f"""\

CONVERSATION HISTORY:
{history_text}

CURRENT USER QUERY:
{query.strip()}

Rewrite the current user query as a standalone query.
Return only the rewritten query.
"""
        try:
            rewritten = self.llm_client.generate(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
        except Exception:

            return query 
        if not rewritten or not rewritten.strip():
            raise RuntimeError(
                "Query contextualizer returned an empty query."
            )

        return rewritten.strip()

    @staticmethod
    def _is_standalone_query(query: str) -> bool:
    
        lowered = query.lower().strip()
    
        conversational_queries = {
            "hi",
            "hello",
            "hey",
            "hello!",
            "hi!",
            "hey!",
            "thanks",
            "thank you",
            "ok",
            "okay",
            "bye",
            "good morning",
            "good afternoon",
            "good evening",
        }
    
        return lowered in conversational_queries