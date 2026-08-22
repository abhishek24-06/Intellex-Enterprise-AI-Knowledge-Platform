from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas import EvaluationDataset, evaluate
from ragas.llms import llm_factory
from ragas.metrics import (
    FactualCorrectness,
    Faithfulness,
    LLMContextRecall,
)
from ragas.run_config import RunConfig


load_dotenv()


class RagasEvaluator:

    DEFAULT_MODEL = "google/gemini-2.5-flash"

    def __init__(
        self,
        *,
        model: str | None = None,
    ):

        api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not configured."
            )

        self.model = (
            model
            or os.getenv(
                "RAGAS_EVALUATOR_MODEL",
                self.DEFAULT_MODEL,
            )
        )

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # IMPORTANT:
        # RunConfig belongs to Ragas evaluation execution.
        # Do NOT pass it into llm_factory().
        self.run_config = RunConfig(
            max_workers=1,
            timeout=120,
            max_retries=2,
        )

        self.llm = llm_factory(
            self.model,
            client=self.client,
        )

    # ------------------------------------------------------------------
    # Load runtime records
    # ------------------------------------------------------------------

    @staticmethod
    def load_runtime_records(
        path: str | Path,
    ) -> list[dict[str, Any]]:

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Runtime evaluation records not found: "
                f"{file_path}"
            )

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                "Runtime evaluation records "
                "must be a JSON list."
            )

        return data

    # ------------------------------------------------------------------
    # Build Ragas dataset
    # ------------------------------------------------------------------

    @staticmethod
    def build_runtime_dataset(
        records: list[dict[str, Any]],
    ) -> EvaluationDataset:

        ragas_records: list[
            dict[str, Any]
        ] = []

        for record in records:

            contexts = record.get(
                "retrieved_contexts",
                [],
            )

            # Database-only requests don't have document
            # contexts and therefore aren't included in
            # these RAG metrics.
            if not contexts:
                continue

            response = record.get(
                "response"
            )

            reference = record.get(
                "reference"
            )

            if not response:
                continue

            if not reference:
                continue

            ragas_records.append(
                {
                    "user_input": record[
                        "user_input"
                    ],
                    "retrieved_contexts": contexts,
                    "response": response,
                    "reference": reference,
                }
            )

        if not ragas_records:
            raise ValueError(
                "No valid records with retrieved "
                "contexts were found."
            )

        return EvaluationDataset.from_list(
            ragas_records
        )

    # ------------------------------------------------------------------
    # Evaluate
    # ------------------------------------------------------------------

    def evaluate(
        self,
        dataset: EvaluationDataset,
    ):

        metrics = [
            LLMContextRecall(),
            Faithfulness(),
            FactualCorrectness(),
        ]

        return evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=self.llm,
            run_config=self.run_config,
            batch_size=1,
        )