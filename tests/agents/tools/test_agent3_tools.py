from __future__ import annotations

from enum import Enum
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.agents.tools.user_data_tools import (
    DATA_AGENT_TOOLS,
    DataAgentContext,
    get_current_user,
    get_department,
    get_organization,
    get_team,
    list_department_users,
    list_team_users,
    search_departments,
    search_teams,
    search_users,
)


# ======================================================================
# Helpers
# ======================================================================


class FakeRole(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    ORG_ADMIN = "ORG_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


def make_user(
    *,
    user_id: int = 1,
    organization_id: int = 1,
    name: str = "Abhishek",
    email: str = "abhishek@example.com",
    role=FakeRole.EMPLOYEE,
    department_id: int | None = None,
    team_id: int | None = None,
):
    return SimpleNamespace(
        user_id=user_id,
        organization_id=organization_id,
        name=name,
        email=email,
        role=role,
        department_id=department_id,
        team_id=team_id,
    )


def make_department(
    *,
    department_id: int = 1,
    organization_id: int = 1,
    name: str = "Engineering",
    description: str = "Engineering department",
):
    return SimpleNamespace(
        department_id=department_id,
        organization_id=organization_id,
        name=name,
        description=description,
    )


def make_team(
    *,
    team_id: int = 1,
    organization_id: int = 1,
    name: str = "Platform",
    description: str = "Platform team",
    department_id: int = 1,
):
    return SimpleNamespace(
        team_id=team_id,
        organization_id=organization_id,
        name=name,
        description=description,
        department_id=department_id,
    )


def make_organization(
    *,
    organization_id: int = 1,
    name: str = "Intellex",
    industry: str = "Technology",
):
    return SimpleNamespace(
        organization_id=organization_id,
        name=name,
        industry=industry,
    )


def make_runtime(
    *,
    db=None,
    current_user=None,
):
    return SimpleNamespace(
        context=DataAgentContext(
            db=db or Mock(),
            current_user=current_user or make_user(),
        )
    )


def make_scalar_result(value):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def make_scalars_result(values):
    result = Mock()
    result.scalars.return_value.all.return_value = values
    return result


# ======================================================================
# Tool collection
# ======================================================================


def test_all_expected_tools_are_registered():

    tool_names = {
        tool.name
        for tool in DATA_AGENT_TOOLS
    }

    assert tool_names == {
        "get_current_user",
        "search_users",
        "get_department",
        "search_departments",
        "list_department_users",
        "get_team",
        "search_teams",
        "list_team_users",
        "get_organization",
    }


# ======================================================================
# Runtime injection / schema
# ======================================================================


@pytest.mark.parametrize(
    "data_tool",
    DATA_AGENT_TOOLS,
)
def test_runtime_dependencies_are_not_model_arguments(
    data_tool,
):

    schema = data_tool.args

    assert "runtime" not in schema
    assert "db" not in schema
    assert "current_user" not in schema


# ======================================================================
# Current user
# ======================================================================


def test_get_current_user_uses_runtime_context():

    db = Mock()

    current_user = make_user(
        user_id=10,
        organization_id=2,
        name="Abhishek",
        email="abhishek@example.com",
        department_id=None,
        team_id=None,
    )

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    result = get_current_user.func(
        runtime=runtime,
    )

    assert result["user_id"] == 10
    assert result["name"] == "Abhishek"
    assert result["email"] == "abhishek@example.com"
    assert result["organization_id"] == 2

    db.execute.assert_not_called()


# ======================================================================
# Search users
# ======================================================================


def test_search_users_returns_same_organization_users():

    db = Mock()

    current_user = make_user(
        user_id=1,
        organization_id=1,
    )

    matched_user = make_user(
        user_id=7,
        organization_id=1,
        name="Rahul Sharma",
        email="rahul@example.com",
    )

    db.execute.return_value = make_scalars_result(
        [matched_user]
    )

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    result = search_users.func(
        name="Rahul Sharma",
        runtime=runtime,
    )

    assert result["found"] is True
    assert result["match_count"] == 1

    user = result["users"][0]

    assert user["user_id"] == 7
    assert user["name"] == "Rahul Sharma"


def test_search_users_returns_multiple_same_names():

    db = Mock()

    current_user = make_user(
        user_id=1,
        organization_id=1,
    )

    users = [
        make_user(
            user_id=7,
            organization_id=1,
            name="Rahul Sharma",
        ),
        make_user(
            user_id=8,
            organization_id=1,
            name="Rahul Sharma",
        ),
    ]

    db.execute.return_value = make_scalars_result(
        users
    )

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    result = search_users.func(
        name="Rahul Sharma",
        runtime=runtime,
    )

    assert result["found"] is True
    assert result["match_count"] == 2

    assert {
        user["user_id"]
        for user in result["users"]
    } == {7, 8}


def test_search_users_supports_combined_filters():

    db = Mock()

    current_user = make_user(
        user_id=1,
        organization_id=2,
    )

    matched_user = make_user(
        user_id=15,
        organization_id=2,
        name="Rahul Sharma",
        email="rahul@example.com",
        department_id=3,
        team_id=4,
    )

    db.execute.return_value = make_scalars_result(
        [matched_user]
    )

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    result = search_users.func(
        name="Rahul",
        department_id=3,
        team_id=4,
        runtime=runtime,
    )

    assert result["match_count"] == 1
    assert result["users"][0]["user_id"] == 15


def test_search_users_rejects_invalid_limit():

    runtime = make_runtime()

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        search_users.func(
            limit=0,
            runtime=runtime,
        )


def test_search_users_enforces_organization_and_super_admin_filter():

    db = Mock()

    current_user = make_user(
        organization_id=2,
    )

    db.execute.return_value = make_scalars_result(
        []
    )

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    search_users.func(
        user_id=7,
        runtime=runtime,
    )

    stmt = db.execute.call_args.args[0]

    compiled = str(
        stmt.compile()
    )

    assert "organization_id" in compiled
    assert "user_id" in compiled
    assert "role" in compiled


# ======================================================================
# Department
# ======================================================================


def test_get_department_returns_same_organization_department():

    db = Mock()

    current_user = make_user(
        organization_id=2,
    )

    department = make_department(
        department_id=3,
        organization_id=2,
        name="Engineering",
    )

    db.execute.return_value = make_scalar_result(
        department
    )

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    result = get_department.func(
        department_id=3,
        runtime=runtime,
    )

    assert result is not None
    assert result["department_id"] == 3
    assert result["name"] == "Engineering"
    assert result["organization_id"] == 2


def test_get_department_returns_none_for_missing_department():

    db = Mock()

    db.execute.return_value = make_scalar_result(
        None
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=2,
        ),
    )

    result = get_department.func(
        department_id=999,
        runtime=runtime,
    )

    assert result is None


# ======================================================================
# Search departments
# ======================================================================


def test_search_departments_returns_matches():

    db = Mock()

    departments = [
        make_department(
            department_id=1,
            organization_id=2,
            name="Engineering",
        ),
        make_department(
            department_id=2,
            organization_id=2,
            name="Engineering Operations",
        ),
    ]

    db.execute.return_value = make_scalars_result(
        departments
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=2,
        ),
    )

    result = search_departments.func(
        name="Engineering",
        runtime=runtime,
    )

    assert result["found"] is True
    assert result["match_count"] == 2

    assert {
        department["department_id"]
        for department in result["departments"]
    } == {1, 2}


def test_search_departments_rejects_invalid_limit():

    runtime = make_runtime()

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        search_departments.func(
            limit=0,
            runtime=runtime,
        )


# ======================================================================
# Department users
# ======================================================================


def test_list_department_users_returns_users():

    db = Mock()

    current_user = make_user(
        organization_id=1,
    )

    department = make_department(
        department_id=3,
        organization_id=1,
        name="Engineering",
    )

    users = [
        make_user(
            user_id=10,
            organization_id=1,
            department_id=3,
        ),
        make_user(
            user_id=11,
            organization_id=1,
            department_id=3,
        ),
    ]

    # --------------------------------------------------------------
    # DB calls:
    #
    # 1. Get department
    # 2. Get users in department
    # 3. Resolve department relationship for user 10
    # 4. Resolve department relationship for user 11
    # --------------------------------------------------------------

    department_result = make_scalar_result(
        department
    )

    users_result = make_scalars_result(
        users
    )

    db.execute.side_effect = [
        department_result,
        users_result,
        make_scalar_result(department),
        make_scalar_result(department),
    ]

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    result = list_department_users.func(
        department_id=3,
        runtime=runtime,
    )

    assert result["found"] is True
    assert result["match_count"] == 2
    assert result["department"]["department_id"] == 3


def test_list_department_users_hides_missing_department():

    db = Mock()

    db.execute.return_value = make_scalar_result(
        None
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=1,
        ),
    )

    result = list_department_users.func(
        department_id=999,
        runtime=runtime,
    )

    assert result["found"] is False
    assert result["users"] == []


def test_list_department_users_rejects_invalid_limit():

    runtime = make_runtime()

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        list_department_users.func(
            department_id=3,
            limit=0,
            runtime=runtime,
        )


# ======================================================================
# Team
# ======================================================================


def test_get_team_returns_same_organization_team():

    db = Mock()

    team = make_team(
        team_id=4,
        organization_id=2,
        name="Platform",
    )

    db.execute.return_value = make_scalar_result(
        team
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=2,
        ),
    )

    result = get_team.func(
        team_id=4,
        runtime=runtime,
    )

    assert result is not None
    assert result["team_id"] == 4
    assert result["name"] == "Platform"
    assert result["organization_id"] == 2


def test_get_team_returns_none_for_missing_team():

    db = Mock()

    db.execute.return_value = make_scalar_result(
        None
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=2,
        ),
    )

    result = get_team.func(
        team_id=999,
        runtime=runtime,
    )

    assert result is None


# ======================================================================
# Search teams
# ======================================================================


def test_search_teams_returns_matches():

    db = Mock()

    teams = [
        make_team(
            team_id=4,
            organization_id=2,
            name="Platform",
        ),
        make_team(
            team_id=5,
            organization_id=2,
            name="Platform Operations",
        ),
    ]

    db.execute.return_value = make_scalars_result(
        teams
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=2,
        ),
    )

    result = search_teams.func(
        name="Platform",
        runtime=runtime,
    )

    assert result["found"] is True
    assert result["match_count"] == 2

    assert {
        team["team_id"]
        for team in result["teams"]
    } == {4, 5}


def test_search_teams_rejects_invalid_limit():

    runtime = make_runtime()

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        search_teams.func(
            limit=0,
            runtime=runtime,
        )


# ======================================================================
# Team users
# ======================================================================


def test_list_team_users_returns_users():

    db = Mock()

    current_user = make_user(
        organization_id=1,
    )

    team = make_team(
        team_id=4,
        organization_id=1,
        name="Platform",
    )

    users = [
        make_user(
            user_id=10,
            organization_id=1,
            team_id=4,
        ),
    ]

    # --------------------------------------------------------------
    # DB calls:
    #
    # 1. Get team
    # 2. Get users in team
    # 3. Resolve team relationship for user 10
    # --------------------------------------------------------------

    team_result = make_scalar_result(
        team
    )

    users_result = make_scalars_result(
        users
    )

    db.execute.side_effect = [
        team_result,
        users_result,
        make_scalar_result(team),
    ]

    runtime = make_runtime(
        db=db,
        current_user=current_user,
    )

    result = list_team_users.func(
        team_id=4,
        runtime=runtime,
    )

    assert result["found"] is True
    assert result["match_count"] == 1
    assert result["team"]["team_id"] == 4


def test_list_team_users_hides_missing_team():

    db = Mock()

    db.execute.return_value = make_scalar_result(
        None
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=1,
        ),
    )

    result = list_team_users.func(
        team_id=999,
        runtime=runtime,
    )

    assert result["found"] is False
    assert result["users"] == []


def test_list_team_users_rejects_invalid_limit():

    runtime = make_runtime()

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        list_team_users.func(
            team_id=4,
            limit=0,
            runtime=runtime,
        )


# ======================================================================
# Organization
# ======================================================================


def test_get_organization_returns_current_users_organization():

    db = Mock()

    organization = make_organization(
        organization_id=2,
        name="Intellex",
        industry="Technology",
    )

    db.execute.return_value = make_scalar_result(
        organization
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=2,
        ),
    )

    result = get_organization.func(
        runtime=runtime,
    )

    assert result is not None
    assert result["organization_id"] == 2
    assert result["name"] == "Intellex"
    assert result["industry"] == "Technology"


def test_get_organization_returns_none_when_missing():

    db = Mock()

    db.execute.return_value = make_scalar_result(
        None
    )

    runtime = make_runtime(
        db=db,
        current_user=make_user(
            organization_id=2,
        ),
    )

    result = get_organization.func(
        runtime=runtime,
    )

    assert result is None


# ======================================================================
# Relationship serialization
# ======================================================================


def test_user_relationships_are_serialized():

    db = Mock()

    user = make_user(
        user_id=10,
        organization_id=2,
        department_id=3,
        team_id=4,
    )

    department = make_department(
        department_id=3,
        organization_id=2,
        name="Engineering",
    )

    team = make_team(
        team_id=4,
        organization_id=2,
        name="Platform",
    )

    db.execute.side_effect = [
        make_scalar_result(department),
        make_scalar_result(team),
    ]

    runtime = make_runtime(
        db=db,
        current_user=user,
    )

    result = get_current_user.func(
        runtime=runtime,
    )

    assert result["department"] == {
        "department_id": 3,
        "name": "Engineering",
    }

    assert result["team"] == {
        "team_id": 4,
        "name": "Platform",
    }