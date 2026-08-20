from __future__ import annotations

from typing import Annotated

from langchain_core.tools import tool
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.users import User
from app.enums.enums import UserRole
from app.models.department import Department
from app.models.team import Team
from app.models.organization import Organization

def _serialize_user(user:User,*,department: Department |None = None,team: Team |None = None)->dict:

    return{
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": (
            user.role.value
            if hasattr(user.role, "value")
            else str(user.role)
        ),
        "organization_id": user.organization_id,
        "department": (
            {
                "department_id": department.department_id,
                "name": department.name
            }
            if department is not None
            else None
        ),
        "team": (
            {
                "team_id": team.team_id,
                "name": team.name
            }
            if team is not None
            else None
        ),
    }

def _base_user_conditions(*,current_user:User)->list:

    #Super_Admin and User from other ORG are excluded with this func


    return[
        User.organization_id == current_user.organization_id,

        User.role != UserRole.SUPER_ADMIN
    ] 

def _get_user_with_relationships(*,db:Session,user:User)->dict:

    department = None
    team = None

    if user.department_id is not None:
        department = db.execute(
            select(Department).where(
                Department.department_id== user.department_id,
                Department.organization_id== user.organization_id,
            )
        ).scalar_one_or_none()

    if user.team_id is not None:
        team = db.execute(
            select(Team).where(
                Team.team_id == user.team_id,
                Team.organization_id== user.organization_id,
            )
        ).scalar_one_or_none()

    return _serialize_user(
        user,
        department=department,
        team=team,
    )

@tool
def get_current_user(db:Annotated[Session,"Authenticated Database session"],
                     current_user:Annotated[User,"Authenticated user"])->dict:

    """
    Get information about the currently authenticated user,
    including their department and team.
    """

    return _get_user_with_relationships(
        db=db,
        user=current_user,
    )

@tool
def search_users(db:Annotated[Session,"Authenticated Database session"],
                     current_user:Annotated[User,"Authenticated user"],
                     user_id: int | None = None,
                     email: str | None = None,
                     name: str | None = None,
                     department_id: int | None = None,
                     team_id: int | None = None,
                     limit: int = 10 )->dict | None:

    """
    Search users in the authenticated user's organization
    by user ID, email, name, department, or team.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    conditions = _base_user_conditions(current_user=current_user)

    if user_id is not None:
        conditions.append(
            User.user_id == user_id 
        )

    if email is not None:
        conditions.append(
            User.email == email
        )

    if name is not None:
        normalized_name = name.strip()

        if normalized_name:
            conditions.append(
                User.name.ilike(
                    f"%{normalized_name}%"
                )
            )

    if department_id is not None:
        conditions.append(
            User.department_id == department_id
        )

    if team_id is not None:
        conditions.append(
            User.team_id == team_id
        )

    stmt = select(User).where(*conditions).order_by(User.name.asc()).limit(limit)

    users = db.execute(stmt).scalars().all()

    results = [
        _get_user_with_relationships(
            db=db,
            user=user,
        )
        for user in users
    ]

    return {
        "found": bool(results),
        "match_count": len(results),
        "users": results,
    }

@tool
def get_department(db:Annotated[Session,"Authenticated database session"],
                   current_user: Annotated[User,"Authenticated database session"],
                   department_id:int)->dict | None:

    """
    Get a department by ID within the authenticated user's organization.
    """

    department = db.execute(
        select(Department).where(
            Department.department_id == department_id,
            Department.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if department is None:
        return None

    return {
        "department_id": department.department_id,
        "name": department.name,
        "description": department.description,
        "organization_id": department.organization_id,
    }

@tool
def search_departments(db:Annotated[Session,"Authenticated database session"],
                   current_user: Annotated[User,"Authenticated database session"],
                   name:str | None = None,
                   limit: int = 10)->dict | None:

    """
    Search departments by name within the authenticated user's organization.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    limit = min(limit, 20)

    conditions = [
        Department.organization_id == current_user.organization_id]

    if name:
        normalized_name = name.strip()

        if normalized_name:
            conditions.append(
                Department.name.ilike(
                    f"%{normalized_name}%"
                )
            )

    stmt = (select(Department).where(*conditions).order_by(Department.name.asc()).limit(limit))

    departments = (db.execute(stmt).scalars().all())

    return {
        "found": bool(departments),
        "match_count": len(departments),
        "departments": [
            {
                "department_id": department.department_id,
                "name": department.name,
                "organization_id": department.organization_id,
            }
            for department in departments
        ],
    }


@tool
def list_department_users(db:Annotated[Session,"Authenticated database session"],
                        current_user: Annotated[User,"Authenticated database session"],
                        department_id:int,
                        limit:int = 50)->dict | None:

    """
    List users belonging to a specific department.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    limit = min(limit, 100)

    department = db.execute(
        select(Department).where(
            Department.department_id == department_id,
            Department.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if department is None:
        return {
            "found": False,
            "department": None,
            "users": [],
        }

    stmt = (
        select(User)
        .where(
            User.organization_id == current_user.organization_id,

            User.department_id == department_id,

            User.role != UserRole.SUPER_ADMIN,
        )
        .order_by(User.name.asc())
        .limit(limit)
    )

    users = db.execute(stmt).scalars().all()

    return {
        "found": True,
        "department": {
            "department_id": department.department_id,
            "name": department.name,
        },
        "match_count": len(users),
        "users": [
            _get_user_with_relationships(
                db=db,
                user=user,
            )
            for user in users
        ],
    }

@tool
def get_team(db:Annotated[Session,"Authenticated database session"],
                        current_user: Annotated[User,"Authenticated database session"],
                        team_id:int)->dict | None:

    """
    Get a team by ID within the authenticated user's organization.
    """

    team = db.execute(
        select(Team).where(
            Team.team_id == team_id,
            Team.organization_id
            == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if team is None:
        return None

    return {
        "team_id": team.team_id,
        "name": team.name,
        "description": team.description,
        "department_id": team.department_id,
        "organization_id": team.organization_id,
    }

@tool
def search_teams(
    db: Annotated[Session,"Authenticated database session",],
    current_user: Annotated[User,"Authenticated user",],
    name: str | None = None,
    limit: int = 10) -> dict:

    """
    Search teams by name within the authenticated user's organization.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    limit = min(limit, 20)

    conditions = [
        Team.organization_id== current_user.organization_id]

    if name:
        normalized_name = name.strip()

        if normalized_name:
            conditions.append(
                Team.name.ilike(
                    f"%{normalized_name}%"
                )
            )

    stmt = (select(Team).where(*conditions).order_by(Team.name.asc()).limit(limit))

    teams = (db.execute(stmt).scalars().all())

    return {
        "found": bool(teams),
        "match_count": len(teams),
        "teams": [
            {
                "team_id": team.team_id,
                "name": team.name,
                "organization_id": team.organization_id,
            }
            for team in teams
        ],
    }

@tool
def list_team_users(db:Annotated[Session,"Authenticated database session"],
                        current_user: Annotated[User,"Authenticated database session"],
                        team_id:int,
                        limit:int = 50)->dict | None:

    """
    List users belonging to a specific team.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    limit = min(limit, 100)

    team = db.execute(
        select(Team).where(
            Team.team_id == team_id,
            Team.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if team is None:
        return {
            "found": False,
            "team": None,
            "users": [],
        }

    stmt = (
        select(User)
        .where(
            User.organization_id == current_user.organization_id,

            User.team_id == team_id,

            User.role != UserRole.SUPER_ADMIN,
        )
        .order_by(User.name.asc())
        .limit(limit)
    )

    users = db.execute(stmt).scalars().all()

    return {
        "found": True,
        "team": {
            "team_id": team.team_id,
            "name": team.name,
        },
        "match_count": len(users),
        "users": [
            _get_user_with_relationships(
                db=db,
                user=user,
            )
            for user in users
        ],
    }

@tool
def get_organization(
    db: Annotated[
        Session,
        "Authenticated database session",
    ],
    current_user: Annotated[
        User,
        "Authenticated user",
    ],
) -> dict | None:
    """
    Get the organization of the authenticated user.
    """

    organization = db.execute(
        select(Organization).where(
            Organization.organization_id
            == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if organization is None:
        return None

    return {
        "organization_id": organization.organization_id,
        "name": organization.name,
        "industry": organization.industry,
    }
