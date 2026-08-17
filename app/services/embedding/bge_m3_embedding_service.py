from sentence_transformers import SentenceTransformer

class BGEM3EmbeddingService:

    MODEL_NAME = "BAAI/bge-m3"
    EMBEDDING_DIMENSION = 1024
    MAX_TOKENS = 8192

    def __init__(self,model_name: str = MODEL_NAME,device: str | None = None):

        self.model = SentenceTransformer(model_name,device=device)

        self.tokenizer = self.model.tokenizer

    def embed_text(self, text: str) -> list[float]:

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not text.strip():
            raise ValueError("text cannot be empty")

        embedding = self.model.encode(text,normalize_embeddings=True)

        vector = embedding.tolist()

        if len(vector) != self.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension "
                f"{self.EMBEDDING_DIMENSION}, "
                f"got {len(vector)}"
            )

        return vector

    def embed_texts(self,texts: list[str],batch_size: int = 8) -> list[list[float]]:

        if not isinstance(texts, list):
            raise TypeError("texts must be a list")

        if not texts:
            return []

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError("texts cannot contain empty or non-string values")

        embeddings = self.model.encode(texts,batch_size=batch_size,normalize_embeddings=True)

        vectors = embeddings.tolist()

        for vector in vectors:
            if len(vector) != self.EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Expected embedding dimension "
                    f"{self.EMBEDDING_DIMENSION}, "
                    f"got {len(vector)}"
                )

        return vectors

    def count_tokens(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        encoded = self.tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
        )

        return len(encoded["input_ids"])

                