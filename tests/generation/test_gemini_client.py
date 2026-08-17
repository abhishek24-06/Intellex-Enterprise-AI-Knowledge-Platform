from unittest.mock import Mock, patch

import pytest

from app.services.generation.gemini_client import (
    GeminiClient,
)


def test_missing_api_key_is_rejected():

    with patch.dict(
        "os.environ",
        {},
        clear=True,
    ):
        with pytest.raises(
            ValueError,
            match="GEMINI_API_KEY",
        ):
            GeminiClient()


def test_generate_returns_response_text():

    mock_response = Mock()

    mock_response.text = (
        "This is a generated answer."
    )

    mock_client = Mock()

    mock_client.models.generate_content.return_value = (
        mock_response
    )

    with patch(
        "app.services.generation.gemini_client.genai.Client",
        return_value=mock_client,
    ):

        client = GeminiClient(
            api_key="test-key",
        )

        result = client.generate(
            system_prompt="You are a helpful assistant.",
            user_prompt="Explain RAG.",
        )

    assert result == (
        "This is a generated answer."
    )

    mock_client.models.generate_content.assert_called_once()