from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import Team
from app.schemas.teams import CreateTeamRequest,TeamResponse
from app.services.department_service import get_department_by_id 

def get_team_by_name(db:Session,department_id: int,name:str)->Team|None:

    stmt = (select(Team).where(Team.department_id == department_id,Team.name == name))

    return db.execute(stmt).scalar_one_or_none()

def get_team_by_id(db:Session,team_id:int)->Team|None:

    stmt = (select(Team).where(Team.team_id == team_id))

    return db.execute(stmt).scalar_one_or_none()

def create_team(db:Session,
                      team_data:CreateTeamRequest,
                      organization_id: int)-> Team:
    
    department=get_department_by_id(db=db, department_id=team_data.department_id)

    if department is None:
        raise ValueError("Department not found")
    
    if department.organization_id != organization_id:
        raise ValueError("Cannot create a team in another organization.")
    
    existing_team=get_team_by_name(db=db,department_id=team_data.department_id,name=team_data.name)

    if existing_team:
        raise ValueError("Team already exists")
    
    team=Team(
        organization_id=organization_id,
        department_id=team_data.department_id,
        name=team_data.name,
        description=team_data.description
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    return team