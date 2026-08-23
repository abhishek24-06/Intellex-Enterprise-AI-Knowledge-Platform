from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from app.agents.multi_agent_state import (
    MultiAgentContext,
)


def _build_details(
    *,
    agent_name: str,
    state: dict[str, Any],
    output: dict[str, Any],
) -> dict[str, Any]:

    details: dict[str, Any] = {}

    # --------------------------------------------------------------
    # Knowledge Agent
    # --------------------------------------------------------------

    if agent_name == "knowledge_agent":

        rag_result = output.get(
            "rag_result"
        )

        if rag_result is not None:

            sources = getattr(
                rag_result,
                "sources",
                [],
            )

            details["retrieved_chunks"] = (
                len(sources)
            )

            details["retrieved_documents"] = len(
                {
                    source.document_id
                    for source in sources
                    if getattr(
                        source,
                        "document_id",
                        None,
                    ) is not None
                }
            )

    # --------------------------------------------------------------
    # Database Agent
    # --------------------------------------------------------------

    elif agent_name == "database_agent":

        database_result = output.get(
            "database_result"
        )

        details["result_present"] = bool(
            database_result
        )

        if database_result is not None:

            details["result_chars"] = len(
                str(database_result)
            )

    # --------------------------------------------------------------
    # Orchestrator
    # --------------------------------------------------------------

    elif agent_name == "orchestrator":

        details["route"] = output.get(
            "route"
        )

        details["route_reason_present"] = bool(
            output.get("route_reason")
        )

    # --------------------------------------------------------------
    # Synthesis
    # --------------------------------------------------------------

    elif agent_name == "synthesis":

        final_answer = output.get(
            "final_answer"
        )

        details["answer_chars"] = len(
            final_answer or ""
        )

    # --------------------------------------------------------------
    # Critic
    # --------------------------------------------------------------

    elif agent_name == "multi_agent_critic":

        critique = output.get(
            "critique"
        )

        if critique is not None:

            details["decision"] = (
                critique.decision.value
            )

            details["context_relevance"] = (
                critique.context_relevance
            )

            details["faithfulness"] = (
                critique.faithfulness
            )

            details["answer_correctness"] = (
                critique.answer_correctness
            )

            details["retry_target"] = (
                critique.retry_target.value
                if critique.retry_target
                else None
            )

    # --------------------------------------------------------------
    # Retry Preparation
    # --------------------------------------------------------------

    elif agent_name == "multi_agent_prepare_retry":

        details["retry_target"] = (
            output.get("retry_target")
        )

        details["improved_query_present"] = bool(
            output.get("knowledge_query")
            or output.get("database_query")
        )

    return details


def _record_execution(
    *,
    agent_name: str,
    state: dict[str, Any],
    output: dict[str, Any],
    started_at: float,
) -> dict[str, Any]:

    latency_ms = (
        perf_counter()
        - started_at
    ) * 1000

    event = {
        "node": "agent_execution",
        "agent_name": agent_name,
        "request_id": state.get(
            "request_id",
            "unknown",
        ),
        "route": state.get(
            "route"
        ),
        "attempt": state.get(
            "attempt",
            0,
        ),
        "status": "SUCCESS",
        "latency_ms": round(
            latency_ms,
            3,
        ),
        "details": _build_details(
            agent_name=agent_name,
            state=state,
            output=output,
        ),
    }

    updated = dict(output)

    updated["history"] = [
        *output.get(
            "history",
            [],
        ),
        event,
    ]

    return updated


def timed_node(
    *,
    agent_name: str,
    node: Callable,
    with_runtime: bool = False,
):
    """
    Instrument a LangGraph node while preserving the
    runtime injection contract when required.

    with_runtime=False:
        node(state)

    with_runtime=True:
        node(state, runtime)
    """

    if with_runtime:

        def runtime_wrapper(
            state,
            runtime: Any,
        ):

            started_at = perf_counter()

            output = node(
                state,
                runtime,
            )

            return _record_execution(
                agent_name=agent_name,
                state=state,
                output=output,
                started_at=started_at,
            )

        return runtime_wrapper

    def state_wrapper(
        state,
    ):

        started_at = perf_counter()

        output = node(
            state
        )

        return _record_execution(
            agent_name=agent_name,
            state=state,
            output=output,
            started_at=started_at,
        )

    return state_wrapper