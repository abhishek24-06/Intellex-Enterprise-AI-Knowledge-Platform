import pytest

from app.services.embedding.bge_m3_embedding_service import (
    BGEM3EmbeddingService,
)


@pytest.fixture(scope="session")
def embedding_service():
    """
    Load BGE-M3 once for the entire pytest session.

    This avoids downloading/loading the model separately
    for every test.
    """
    return BGEM3EmbeddingService()


def test_bge_m3_single_embedding(embedding_service):

    text = "Intellex is an enterprise knowledge intelligence platform."

    vector = embedding_service.embed_text(text)

    print("\n========== BGE-M3 SINGLE EMBEDDING ==========")
    print(f"Text: {text}")
    print(f"Vector length: {len(vector)}")
    print("Vector:")
    print(vector)
    print("=============================================")

    assert isinstance(vector, list)
    assert len(vector) == 1024
    assert all(isinstance(value, float) for value in vector)


def test_bge_m3_token_count(embedding_service):

    text = (
        "Intellex retrieves information "
        "from authorized enterprise documents."
    )

    token_count = embedding_service.count_tokens(text)

    print("\n========== BGE-M3 TOKEN COUNT ==========")
    print(f"Text: {text}")
    print(f"Token count: {token_count}")
    print("========================================")

    assert isinstance(token_count, int)
    assert token_count > 0


def test_bge_m3_batch_embedding(embedding_service):

    texts = [
        "Document retrieval",
        "Employee contact information",
        "Enterprise knowledge base",
    ]

    vectors = embedding_service.embed_texts(texts)

    print("\n========== BGE-M3 BATCH EMBEDDINGS ==========")

    for i, (text, vector) in enumerate(zip(texts, vectors), start=1):
        print(f"\n--- Vector {i} ---")
        print(f"Text: {text}")
        print(f"Vector length: {len(vector)}")
        print("Vector:")
        print(vector)

    print("\n==============================================")

    assert len(vectors) == len(texts)

    for vector in vectors:
        assert isinstance(vector, list)
        assert len(vector) == 1024
        assert all(isinstance(value, float) for value in vector)