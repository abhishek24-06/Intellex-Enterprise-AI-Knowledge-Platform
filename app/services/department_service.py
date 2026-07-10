from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department

def get_department_by_name(db:Session,organization_id:int,name:str)->Department|None:

    stmt = (select(Department).where(Department.organization_id==organization_id,Department.name == name))

    return db.execute(stmt).scalar_one_or_none()

def create_department(db:Session,
                      *,
                      organization_id: int,
                      name:str,
                      description:str)-> Department:
    
    existing_department = get_department_by_name(db=db,organization_id=organization_id,name=name)

    if existing_department:
        return existing_department
    
    department=Department(
        organization_id=organization_id,
        name=name,
        description=description
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    return department