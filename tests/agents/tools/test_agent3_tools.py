from __future__ import annotations

import pytest

from app.database.database import SessionLocal
from app.models.users import User

from app.agents.tools.user_data_tools import (
    get_current_user,
    search_users,
    get_department,
    search_departments,
    list_department_users,
    get_team,
    search_teams,
    list_team_users,
    get_organization,
)


# ============================================================
# Configuration
# ============================================================

TEST_USER_ID = 9


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def current_user(db):
    user = (
        db.query(User)
        .filter(
            User.user_id == TEST_USER_ID
        )
        .first()
    )

    if user is None:
        pytest.fail(
            f"Test user {TEST_USER_ID} was not found."
        )

    return user


# ============================================================
# Helper
# ============================================================

def call_tool(tool, **kwargs):
    """
    LangChain @tool functions are StructuredTool objects.

    .invoke() is the normal way to execute them.
    """
    return tool.invoke(kwargs)


# ============================================================
# 1. Current User
# ============================================================

def test_get_current_user(
    db,
    current_user,
):
    result = call_tool(
        get_current_user,
        db=db,
        current_user=current_user,
    )

    print("\nCURRENT USER:")
    print(result)

    assert result is not None
    assert result["user_id"] == TEST_USER_ID
    assert result["organization_id"] == current_user.organization_id

    assert "name" in result
    assert "email" in result
    assert "role" in result
    assert "department" in result
    assert "team" in result


# ============================================================
# 2. Search users by name
# ============================================================

def test_search_users_by_name(
    db,
    current_user,
):
    result = call_tool(
        search_users,
        db=db,
        current_user=current_user,
        name="Akash",
    )

    print("\nSEARCH USERS BY NAME:")
    print(result)

    assert result is not None
    assert "found" in result
    assert "match_count" in result
    assert "users" in result

    for user in result["users"]:
        assert user["organization_id"] == (
            current_user.organization_id
        )


# ============================================================
# 3. Search users by ID
# ============================================================

def test_search_user_by_id(
    db,
    current_user,
):
    result = call_tool(
        search_users,
        db=db,
        current_user=current_user,
        user_id=TEST_USER_ID,
    )

    print("\nSEARCH USER BY ID:")
    print(result)

    assert result["found"] is True
    assert result["match_count"] == 1
    assert result["users"][0]["user_id"] == TEST_USER_ID


# ============================================================
# 4. Search departments by name
# ============================================================

def test_search_departments_by_name(
    db,
    current_user,
):
    result = call_tool(
        search_departments,
        db=db,
        current_user=current_user,
        name="IT",
    )

    print("\nSEARCH DEPARTMENTS:")
    print(result)

    assert result is not None
    assert "found" in result
    assert "departments" in result

    for department in result["departments"]:
        assert department["organization_id"] == (
            current_user.organization_id
        )


# ============================================================
# 5. Get department by ID
# ============================================================

def test_get_department(
    db,
    current_user,
):
    search_result = call_tool(
        search_departments,
        db=db,
        current_user=current_user,
        name="IT",
    )

    assert search_result["found"] is True
    assert search_result["departments"]

    department_id = (
        search_result["departments"][0]["department_id"]
    )

    result = call_tool(
        get_department,
        db=db,
        current_user=current_user,
        department_id=department_id,
    )

    print("\nGET DEPARTMENT:")
    print(result)

    assert result is not None
    assert result["department_id"] == department_id
    assert result["organization_id"] == (
        current_user.organization_id
    )


# ============================================================
# 6. List users in department
# ============================================================

def test_list_department_users(
    db,
    current_user,
):
    search_result = call_tool(
        search_departments,
        db=db,
        current_user=current_user,
        name="IT",
    )

    assert search_result["found"] is True

    department_id = (
        search_result["departments"][0]["department_id"]
    )

    result = call_tool(
        list_department_users,
        db=db,
        current_user=current_user,
        department_id=department_id,
    )

    print("\nDEPARTMENT USERS:")
    print(result)

    assert result["found"] is True
    assert result["department"]["department_id"] == (
        department_id
    )

    for user in result["users"]:
        assert user["organization_id"] == (
            current_user.organization_id
        )
        assert user["department"]["department_id"] == (
            department_id
        )


# ============================================================
# 7. Search teams by name
# ============================================================

def test_search_teams_by_name(
    db,
    current_user,
):
    result = call_tool(
        search_teams,
        db=db,
        current_user=current_user,
        name="HR",
    )

    print("\nSEARCH TEAMS:")
    print(result)

    assert result is not None
    assert "found" in result
    assert "teams" in result

    for team in result["teams"]:
        assert team["organization_id"] == (
            current_user.organization_id
        )


# ============================================================
# 8. Get team by ID
# ============================================================

def test_get_team(
    db,
    current_user,
):
    search_result = call_tool(
        search_teams,
        db=db,
        current_user=current_user,
        name="HR",
    )

    assert search_result["found"] is True
    assert search_result["teams"]

    team_id = (
        search_result["teams"][0]["team_id"]
    )

    result = call_tool(
        get_team,
        db=db,
        current_user=current_user,
        team_id=team_id,
    )

    print("\nGET TEAM:")
    print(result)

    assert result is not None
    assert result["team_id"] == team_id
    assert result["organization_id"] == (
        current_user.organization_id
    )


# ============================================================
# 9. List users in team
# ============================================================

def test_list_team_users(
    db,
    current_user,
):
    search_result = call_tool(
        search_teams,
        db=db,
        current_user=current_user,
        name="HR",
    )

    assert search_result["found"] is True

    team_id = (
        search_result["teams"][0]["team_id"]
    )

    result = call_tool(
        list_team_users,
        db=db,
        current_user=current_user,
        team_id=team_id,
    )

    print("\nTEAM USERS:")
    print(result)

    assert result["found"] is True
    assert result["team"]["team_id"] == team_id

    for user in result["users"]:
        assert user["organization_id"] == (
            current_user.organization_id
        )
        assert user["team"]["team_id"] == team_id


# ============================================================
# 10. Get organization
# ============================================================

def test_get_organization(
    db,
    current_user,
):
    result = call_tool(
        get_organization,
        db=db,
        current_user=current_user,
    )

    print("\nORGANIZATION:")
    print(result)

    assert result is not None
    assert result["organization_id"] == (
        current_user.organization_id
    )

    assert "name" in result
    assert "industry" 