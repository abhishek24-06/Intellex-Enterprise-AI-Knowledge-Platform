from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization

def get_organization_by_name(db:Session,name:str)->Organization|None:

    stmt = (select(Organization).where(Organization.name == name))

    return db.execute(stmt).scalar_one_or_none()

def create_organization(db:Session,
                        *,
                        name:str,
                        industry:str)-> Organization:
    
    existing_organization = get_organization_by_name(
    db=db,
    name=name,
)
    if existing_organization:
        return existing_organization

    organization = Organization(
    name=name,
    industry=industry
)
    
    db.add(organization)
    db.flush()
    db.refresh(organization)

    return organization