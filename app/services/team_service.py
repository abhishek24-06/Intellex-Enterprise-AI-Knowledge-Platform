from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import Team

def get_team_by_name(db:Session,department_id: int,name:str)->Team|None:

    stmt = (select(Team).where(Team.department_id == department_id,Team.name == name))

    return db.execute(stmt).scalar_one_or_none()

def create_team(db:Session,
                      *,
                      organization_id: int,
                      department_id: int,
                      name:str,
                      description:str)-> Team:
    
    existing_team = get_team_by_name(db=db,department_id=department_id,name=name)

    if existing_team:
        return existing_team
    
    team=Team(
        organization_id=organization_id,
        department_id=department_id,
        name=name,
        description=description
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    return team