from app.dto.boundary_response import BoundaryResponse
from app.services.chunking.llm_chunker.gemini_client import GeminiClient


def test_gemini_boundary_detection():

    client = GeminiClient()

    prompt = """
You are a semantic boundary detector.

Your job is to identify where a new semantic topic begins.

Do NOT rewrite, summarize, or modify the text.

Return the order_index of the first element of every semantic group.

Document elements:

Element 0:
Intellex uses PostgreSQL for persistent storage.

Element 1:
PostgreSQL stores document metadata and user information.

Element 2:
The system uses pgvector for semantic retrieval.

Element 3:
Docker is used to containerize the application.

Element 4:
FastAPI provides the backend API.
W
Return only the structured JSON response.
"""

    result = client.detect_boundaries(prompt)

    print("\nGemini response:")
    print(result)

    assert isinstance(result, BoundaryResponse)

    assert isinstance(result.boundaries, list)

    assert all(
        isinstance(index, int)
        for index in result.boundaries
    )

    assert len(result.boundaries) > 0

    assert result.boundaries == sorted(
        set(result.boundaries)
    )