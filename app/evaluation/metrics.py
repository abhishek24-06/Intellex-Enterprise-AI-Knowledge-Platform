from __future__ import annotations


def hit_at_k(
    retrieved_ids: list[int],
    relevant_ids: set[int],
) -> float:

    return float(
        any(
            document_id in relevant_ids
            for document_id in retrieved_ids
        )
    )


def precision_at_k(
    retrieved_ids: list[int],
    relevant_ids: set[int],
) -> float:

    if not retrieved_ids:
        return 0.0

    relevant_count = sum(
        document_id in relevant_ids
        for document_id in retrieved_ids
    )

    return relevant_count / len(
        retrieved_ids
    )


def recall_at_k(
    retrieved_ids: list[int],
    relevant_ids: set[int],
) -> float:

    if not relevant_ids:
        return 0.0

    relevant_count = sum(
        document_id in relevant_ids
        for document_id in set(retrieved_ids)
    )

    return relevant_count / len(
        relevant_ids
    )


def reciprocal_rank(
    retrieved_ids: list[int],
    relevant_ids: set[int],
) -> float:

    for index, document_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if document_id in relevant_ids:
            return 1.0 / index

    return 0.0