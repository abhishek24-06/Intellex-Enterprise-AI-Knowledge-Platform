from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from sqlalchemy import select

from app.database.database import SessionLocal
from app.dependencies.agentic_rag import (
    get_agentic_rag_service,
)
from app.models.users import User


EVALUATION_ROOT = (
    PROJECT_ROOT / "evaluation"
)

DATASET_PATH = (
    EVALUATION_ROOT
    / "evals"
    / "datasets"
    / "rag_eval_dataset.json"
)

RUNTIME_OUTPUT_PATH = (
    EVALUATION_ROOT
    / "evals"
    / "results"
    / "runtime_evaluation_records.json"
)

DEBUG_CASE_IDS = {
    "knowledge_001",
    "database_001",
    "hybrid_001",
}


def load_dataset(
    path: Path,
) -> list[dict[str, Any]]:

    if not path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Evaluation dataset must be a JSON list."
        )

    return data


def get_evaluation_user(
    db,
) -> User:

    user = db.execute(
        select(User)
        .where(
            User.user_id == 9,
            User.organization_id == 2,
            User.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if user is None:
        raise RuntimeError(
            "Evaluation user_id=9 with "
            "organization_id=2 was not found."
        )

    return user


def serialize_source(
    source,
) -> dict[str, Any]:

    return {
        "document_id": source.document_id,
        "original_filename": (
            source.original_filename
        ),
        "chunk_id": getattr(
            source,
            "chunk_id",
            None,
        ),
        "chunk_index": getattr(
            source,
            "chunk_index",
            None,
        ),
        "chunk_text": source.chunk_text,
    }


def run_case(
    *,
    agentic_rag_service,
    db,
    user,
    case,
) -> dict[str, Any]:

    result = agentic_rag_service.evaluate(
        db=db,
        query=case["user_input"],
        current_user=user,
    )

    sources = [
        serialize_source(source)
        for source in result["sources"]
    ]

    database_evidence = result.get(
        "database_result"
    )

    if database_evidence is not None:
        database_evidence = str(
            database_evidence
        )

    record = {
        "id": case["id"],
        "category": case["category"],
        "user_input": case["user_input"],
        "retrieved_contexts": [
            source["chunk_text"]
            for source in sources
            if source["chunk_text"]
        ],
        "database_evidence": database_evidence,
        "response": result["answer"],
        "reference": case["reference"],
        "route": result.get("route"),
        "attempt": result.get(
            "attempt",
            0,
        ),
        "source_count": len(sources),
        "sources": sources,
    }

    print()
    print("=" * 80)
    print(
        f"{record['id']} "
        f"[{record['category']}]"
    )
    print("=" * 80)

    print(
        "Route:",
        record["route"],
    )

    print(
        "Source count:",
        record["source_count"],
    )

    print(
        "Database evidence:",
        record["database_evidence"],
    )

    print()
    print(
        "Answer:"
    )
    print(
        record["response"]
    )

    return record


def main():

    print(
        "INTELLEX MULTI-SOURCE EVALUATION"
    )

    cases = load_dataset(
        DATASET_PATH
    )

    cases = [
        case
        for case in cases
        if case["id"]
        in DEBUG_CASE_IDS
    ]

    db = SessionLocal()

    try:

        user = get_evaluation_user(
            db
        )

        print(
            f"user_id={user.user_id}"
        )

        print(
            f"organization_id="
            f"{user.organization_id}"
        )

        agentic_rag_service = (
            get_agentic_rag_service()
        )

        records = []

        for case in cases:

            records.append(
                run_case(
                    agentic_rag_service=(
                        agentic_rag_service
                    ),
                    db=db,
                    user=user,
                    case=case,
                )
            )

        RUNTIME_OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with RUNTIME_OUTPUT_PATH.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                records,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print()
        print(
            "Runtime records saved:"
        )

        print(
            RUNTIME_OUTPUT_PATH
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()