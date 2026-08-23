from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from app.dependencies.observability import (
    require_observability_admin,
)
from app.enums.enums import UserRole


def make_user(role):
    return SimpleNamespace(
        user_id=9,
        organization_id=2,
        role=role,
    )


def test_org_admin_is_allowed():

    user = make_user(
        UserRole.ORG_ADMIN
    )

    result = require_observability_admin(
        current_user=user
    )

    assert result is user


def test_super_admin_is_allowed():

    user = make_user(
        UserRole.SUPER_ADMIN
    )

    result = require_observability_admin(
        current_user=user
    )

    assert result is user


def test_employee_is_rejected():

    user = make_user(
        UserRole.EMPLOYEE
    )

    with pytest.raises(
        HTTPException
    ) as exc:

        require_observability_admin(
            current_user=user
        )

    assert (
        exc.value.status_code
        == 403
    )