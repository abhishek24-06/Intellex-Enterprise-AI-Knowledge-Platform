from __future__ import annotations

from typing import Sequence

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from app.dto.retrieved_chunk import RetrievedChunk


class BGERerankerService:

    MODEL_NAME = "BAAI/bge-reranker-v2-m3"

    DEFAULT_BATCH_SIZE = 8

    # Raw BGE reranker logit threshold.
    # Start conservatively and tune using real Intellex queries.
    DEFAULT_RELEVANCE_THRESHOLD = 0.0

    def __init__(
        self,
        *,
        model_name: str = MODEL_NAME,
        batch_size: int = DEFAULT_BATCH_SIZE,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        device: str | None = None,
    ):

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        self.model_name = model_name
        self.batch_size = batch_size
        self.relevance_threshold = relevance_threshold

        if device is None:
            self.device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        else:
            self.device = device

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                self.model_name
            )
        )

        self.model = (
            AutoModelForSequenceClassification
            .from_pretrained(self.model_name)
        )

        self.model.to(self.device)
        self.model.eval()

    def rerank(
        self,
        *,
        query: str,
        chunks: Sequence[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not chunks:
            return []

        if top_k is not None and top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        pairs = [
            (query, chunk.chunk_text)
            for chunk in chunks
        ]

        scores = self._score_pairs(pairs)

        reranked_chunks = []

        for chunk, score in zip(chunks, scores):

            chunk.rerank_score = float(score)

            reranked_chunks.append(chunk)

        # Highest relevance first
        reranked_chunks.sort(
            key=lambda chunk: chunk.rerank_score,
            reverse=True,
        )

        # ---------------------------------------------------------
        # Relevance gate
        # ---------------------------------------------------------

        relevant_chunks = [
            chunk
            for chunk in reranked_chunks
            if chunk.rerank_score
            >= self.relevance_threshold
        ]

        # ---------------------------------------------------------
        # Final top-k
        # ---------------------------------------------------------

        if top_k is not None:
            return relevant_chunks[:top_k]

        return relevant_chunks

    def _score_pairs(
        self,
        pairs: Sequence[tuple[str, str]],
    ) -> list[float]:

        scores: list[float] = []

        for start in range(
            0,
            len(pairs),
            self.batch_size,
        ):

            batch_pairs = pairs[
                start:start + self.batch_size
            ]

            queries = [
                pair[0]
                for pair in batch_pairs
            ]

            documents = [
                pair[1]
                for pair in batch_pairs
            ]

            encoded = self.tokenizer(
                queries,
                documents,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )

            encoded = {
                key: value.to(self.device)
                for key, value in encoded.items()
            }

            with torch.inference_mode():

                outputs = self.model(
                    **encoded
                )

                logits = outputs.logits

            batch_scores = (
                logits
                .view(-1)
                .detach()
                .cpu()
                .tolist()
            )

            scores.extend(
                float(score)
                for score in batch_scores
            )

        return scores