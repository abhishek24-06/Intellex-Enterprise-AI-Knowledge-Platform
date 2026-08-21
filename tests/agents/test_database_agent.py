from __future__ import annotations

from unittest.mock import Mock

import pytest

import app.agents.database_agent as database_agent_module
from app.agents.database_agent import EnterpriseDataAgent

# Fake model / fake graph

class FakeAgent:

    def __init__(self):
        self.calls = []

        self.response = {
            "messages": [
                Mock(
                    content="Your email is abhishek@example.com."
                )
            ]
        }

    def invoke(
        self,
        payload,
        *,
        context,
    ):
        self.calls.append(
            {
                "payload": payload,
                "context": context,
            }
        )

        return self.response

# Fixtures

@pytest.fixture
def fake_agent(monkeypatch):

    agent = FakeAgent()

    def fake_create_agent(
        *,
        model,
        tools,
        system_prompt,
    ):
        assert model is fake_model

        assert tools is database_agent_module.DATA_AGENT_TOOLS

        assert isinstance(
            system_prompt,
            str,
        )

        assert (
            "Never generate SQL"
            in system_prompt
        )

        return agent

    fake_model = Mock()

    monkeypatch.setattr(
        database_agent_module,
        "create_agent",
        fake_create_agent,
    )

    enterprise_agent = EnterpriseDataAgent(
        model=fake_model,
    )

    return enterprise_agent, agent

# Constructor

def test_agent_uses_data_agent_tools(
    monkeypatch,
):

    fake_model = Mock()
    fake_created_agent = Mock()

    captured = {}

    def fake_create_agent(
        *,
        model,
        tools,
        system_prompt,
    ):
        captured["model"] = model
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt

        return fake_created_agent

    monkeypatch.setattr(
        database_agent_module,
        "create_agent",
        fake_create_agent,
    )

    agent = EnterpriseDataAgent(
        model=fake_model,
    )

    assert agent.model is fake_model

    assert (
        agent.tools
        is database_agent_module.DATA_AGENT_TOOLS
    )

    assert (
        captured["tools"]
        is database_agent_module.DATA_AGENT_TOOLS
    )

    assert captured["model"] is fake_model

    assert (
        "Never generate SQL"
        in captured["system_prompt"]
    )

# Query validation

def test_empty_query_is_rejected(
    fake_agent,
):

    agent, _ = fake_agent

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        agent.invoke(
            query="",
            db=Mock(),
            current_user=Mock(),
        )


def test_whitespace_query_is_rejected(
    fake_agent,
):

    agent, _ = fake_agent

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        agent.invoke(
            query="   ",
            db=Mock(),
            current_user=Mock(),
        )

# Invocation

def test_invoke_passes_query_to_langchain_agent(
    fake_agent,
):

    agent, underlying_agent = fake_agent

    db = Mock()

    current_user = Mock(
        user_id=7,
        organization_id=2,
    )

    result = agent.invoke(
        query="What is my email?",
        db=db,
        current_user=current_user,
    )

    assert result == (
        "Your email is abhishek@example.com."
    )

    assert len(
        underlying_agent.calls
    ) == 1

    call = underlying_agent.calls[0]

    assert call["payload"] == {
        "messages": [
            {
                "role": "user",
                "content": "What is my email?",
            }
        ]
    }

    context = call["context"]

    assert context.db is db
    assert context.current_user is current_user


def test_query_is_trimmed_before_invocation(
    fake_agent,
):

    agent, underlying_agent = fake_agent

    agent.invoke(
        query="   What is my email?   ",
        db=Mock(),
        current_user=Mock(),
    )

    call = underlying_agent.calls[0]

    assert call["payload"] == {
        "messages": [
            {
                "role": "user",
                "content": "What is my email?",
            }
        ]
    }

# Invalid agent response

def test_no_messages_raises_runtime_error(
    fake_agent,
):

    agent, underlying_agent = fake_agent

    underlying_agent.response = {
        "messages": []
    }

    with pytest.raises(
        RuntimeError,
        match="returned no messages",
    ):
        agent.invoke(
            query="What is my email?",
            db=Mock(),
            current_user=Mock(),
        )


def test_empty_final_message_raises_runtime_error(
    fake_agent,
):

    agent, underlying_agent = fake_agent

    underlying_agent.response = {
        "messages": [
            Mock(content="")
        ]
    }

    with pytest.raises(
        RuntimeError,
        match="returned an empty answer",
    ):
        agent.invoke(
            query="What is my email?",
            db=Mock(),
            current_user=Mock(),
        )


def test_none_content_raises_runtime_error(
    fake_agent,
):

    agent, underlying_agent = fake_agent

    underlying_agent.response = {
        "messages": [
            Mock(content=None)
        ]
    }

    with pytest.raises(
        RuntimeError,
        match="returned an empty answer",
    ):
        agent.invoke(
            query="What is my email?",
            db=Mock(),
            current_user=Mock(),
        )

# Runtime context isolation

def test_db_and_current_user_are_passed_as_runtime_context(
    fake_agent,
):

    agent, underlying_agent = fake_agent

    db = Mock(
        name="supabase_session"
    )

    current_user = Mock(
        name="authenticated_user"
    )

    agent.invoke(
        query="Which department am I in?",
        db=db,
        current_user=current_user,
    )

    context = (
        underlying_agent.calls[0]["context"]
    )

    assert context.db is db
    assert context.current_user is current_user

# Tool-driven query examples

@pytest.mark.parametrize(
    "query",
    [
        "What is my email?",
        "What is my department?",
        "Who is in the Platform team?",
        "Find Rahul Sharma.",
        "What departments exist?",
        "What teams exist?",
        "Who works in Engineering?",
        "What is my organization's industry?",
    ],
)
def test_supported_enterprise_queries_can_be_sent_to_agent(
    fake_agent,
    query,
):

    agent, underlying_agent = fake_agent

    result = agent.invoke(
        query=query,
        db=Mock(),
        current_user=Mock(),
    )

    assert result

    assert (
        underlying_agent.calls[-1]["payload"]
        ["messages"][0]["content"]
        == query
    )