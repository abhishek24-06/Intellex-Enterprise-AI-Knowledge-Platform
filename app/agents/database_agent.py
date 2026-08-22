from __future__ import annotations
import os
from langchain.agents import create_agent
from langchain_openrouter import ChatOpenRouter

from app.agents.tools.user_data_tools import (
    DATA_AGENT_TOOLS,
    DataAgentContext,
)

class EnterpriseDataAgent:

    SYSTEM_PROMPT = """
You are Intellex's Enterprise Data Agent.

Your job is to answer questions about enterprise identity,
organization, department, team, and user information.

You have access ONLY to the supplied tools.

Rules:

1. Always use a tool for enterprise data.
2. Never invent user, department, team, or organization data.
3. Never generate SQL.
4. Never attempt to bypass tool restrictions.
5. Respect organization boundaries enforced by the tools.
6. SUPER_ADMIN users must never be exposed through user-search tools.
7. If a search returns multiple users, do not arbitrarily choose one.
   Explain the ambiguity and ask the user for clarification.
8. If no matching record is returned, say that the requested
   information was not found.
9. For questions about the authenticated user, prefer
   get_current_user.
10. Keep the final answer concise and factual.
"""

    def __init__(self,*,model: ChatOpenRouter):

        self.model = model
        self.tools = DATA_AGENT_TOOLS
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.SYSTEM_PROMPT,
        )

    def invoke(self,*,query: str,db,current_user) -> str:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        # Runtime-only context.
        # db and current_user are supplied by
        # the application, NOT by the LLM.

        context = DataAgentContext(
            db=db,
            current_user=current_user,
        )

        result = self.agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": query.strip(),
                    }
                ]
            },
            context=context,
        )

        messages = result.get("messages", [])

        if not messages:
            raise RuntimeError("Enterprise Data Agent returned no messages.")

        final_message = messages[-1]

        content = getattr(
            final_message,
            "content", #Get content from final_message else None
            None,
        )

        if not content:
            raise RuntimeError("Enterprise Data Agent returned an empty answer.")

        return content