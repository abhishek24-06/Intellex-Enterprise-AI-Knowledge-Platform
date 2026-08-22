from unittest.mock import Mock

import pytest

from app.services.generation.openrouter_client import (
    OpenRouterClient,
)


def test_generate_returns_message_content(
    monkeypatch,
):

    fake_client = Mock()

    fake_client.chat.completions.create.return_value = (
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="Hello from OpenRouter."
                    )
                )
            ]
        )
    )

    client = OpenRouterClient(
        api_key="test-key",
        model="test/model",
    )

    client.client = fake_client

    result = client.generate(
        system_prompt="You are helpful.",
        user_prompt="Say hello.",
    )

    assert result == (
        "Hello from OpenRouter."
    )

    fake_client.chat.completions.create.assert_called_once()