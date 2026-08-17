from abc import ABC, abstractmethod

class EmbeddingService(ABC):

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        raise NotImplementedError

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens using the embedding model tokenizer."""
        raise NotImplementedError