from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from sqlalchemy.orm import Session

from app.database.database import (
    get_db,
)

from app.dependencies.observability import (
    require_observability_admin,
)

from app.dto.observability import (
    ChatExecutionTraceResponse,
    ObservabilitySummaryResponse,
)

from app.models.users import User

from app.services.observability.observability_service import (
    build_chat_trace,
    build_observability_summary,
)


router = APIRouter(
    prefix="/admin/observability",
    tags=["Observability"],
)


@router.get(
    "/chat/{chat_id}",
    response_model=ChatExecutionTraceResponse,
)
def get_chat_trace(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_observability_admin
    ),
):

    return build_chat_trace(
        db=db,
        chat_id=chat_id,
        current_user=current_user,
    )


@router.get(
    "/summary",
    response_model=ObservabilitySummaryResponse,
)
def get_observability_summary(
    window_hours: int = Query(
        default=24,
        ge=1,
        le=720,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_observability_admin
    ),
):

    return build_observability_summary(
        db=db,
        current_user=current_user,
        window_hours=window_hours,
    )