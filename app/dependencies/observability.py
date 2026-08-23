from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.enums.enums import UserRole
from app.models.users import User


def require_observability_admin(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:

    if current_user.role not in {
        UserRole.ORG_ADMIN,
        UserRole.SUPER_ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only organization administrators "
                "or super administrators can access "
                "observability data."
            ),
        )

    return current_user