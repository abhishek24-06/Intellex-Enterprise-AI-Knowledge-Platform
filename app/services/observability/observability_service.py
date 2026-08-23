from __future__ import annotations

from collections import defaultdict

from app.dto.observability import (
    AgentLatencySummary,
    ChatExecutionTraceResponse,
    ObservabilitySummaryResponse,
    RouteSummary,
)
from app.services.observability.agent_execution_queries import (
    get_chat_execution_trace,
    get_observability_executions,
)


def build_chat_trace(
    *,
    db,
    chat_id: int,
    current_user,
) -> ChatExecutionTraceResponse:

    rows = get_chat_execution_trace(
        db=db,
        chat_id=chat_id,
        current_user=current_user,
    )

    return ChatExecutionTraceResponse(
        chat_id=chat_id,
        execution_count=len(rows),
        executions=rows,
    )


def build_observability_summary(
    *,
    db,
    current_user,
    window_hours: int,
) -> ObservabilitySummaryResponse:

    rows = get_observability_executions(
        db=db,
        current_user=current_user,
        window_hours=window_hours,
    )

    total = len(rows)

    successful = sum(
        row.status == "SUCCESS"
        for row in rows
    )

    failed = total - successful

    total_latency = sum(
        row.latency_ms
        for row in rows
    )

    average_latency = (
        total_latency / total
        if total
        else 0.0
    )

    # --------------------------------------------------------------
    # Retry metrics
    # --------------------------------------------------------------

    retry_count = sum(
        row.attempt > 0
        for row in rows
    )

    retry_rate = (
        retry_count / total
        if total
        else 0.0
    )

    # --------------------------------------------------------------
    # Critic decisions
    # --------------------------------------------------------------

    critic_accept_count = 0
    critic_retry_count = 0

    for row in rows:

        if row.agent_name != (
            "multi_agent_critic"
        ):
            continue

        decision = (
            row.details or {}
        ).get("decision")

        if decision == "ACCEPT":
            critic_accept_count += 1

        elif decision == "RETRY":
            critic_retry_count += 1

    critic_total = (
        critic_accept_count
        + critic_retry_count
    )

    critic_acceptance_rate = (
        critic_accept_count
        / critic_total
        if critic_total
        else 0.0
    )

    # --------------------------------------------------------------
    # Agent latency
    # --------------------------------------------------------------

    latency_data: dict[
        str,
        list[float],
    ] = defaultdict(list)

    for row in rows:

        latency_data[
            row.agent_name
        ].append(
            row.latency_ms
        )

    agent_latency = []

    for (
        agent_name,
        values,
    ) in sorted(
        latency_data.items()
    ):

        agent_latency.append(
            AgentLatencySummary(
                agent_name=agent_name,
                execution_count=len(
                    values
                ),
                average_latency_ms=round(
                    sum(values)
                    / len(values),
                    3,
                ),
                min_latency_ms=round(
                    min(values),
                    3,
                ),
                max_latency_ms=round(
                    max(values),
                    3,
                ),
            )
        )

    # --------------------------------------------------------------
    # Routes
    # --------------------------------------------------------------

    route_counts: dict[
        str,
        int,
    ] = defaultdict(int)

    for row in rows:

        if row.route:
            route_counts[
                row.route
            ] += 1

    routes = [
        RouteSummary(
            route=route,
            execution_count=count,
        )
        for route, count in sorted(
            route_counts.items()
        )
    ]

    return ObservabilitySummaryResponse(
        window_hours=window_hours,
        total_executions=total,
        successful_executions=successful,
        failed_executions=failed,
        average_latency_ms=round(
            average_latency,
            3,
        ),
        retry_count=retry_count,
        retry_rate=round(
            retry_rate,
            4,
        ),
        critic_accept_count=(
            critic_accept_count
        ),
        critic_retry_count=(
            critic_retry_count
        ),
        critic_acceptance_rate=round(
            critic_acceptance_rate,
            4,
        ),
        agent_latency=agent_latency,
        routes=routes,
    )