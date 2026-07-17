from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.departments import CreateDepartmentRequest

def get_department_by_name(db:Session,organization_id:int,name:str)->Department|None:

    stmt = (select(Department).where(Department.organization_id==organization_id,Department.name == name))

    return db.execute(stmt).scalar_one_or_none()

def create_department(db:Session,
                      department_data:CreateDepartmentRequest,
                      organization_id: int)-> Department:
    
    existing_department = get_department_by_name(db=db,organization_id=organization_id,name=department_data.name)

    if existing_department:
        raise ValueError("Department already exists.")
    
    department=Department(
        organization_id=organization_id,
        name=department_data.name,
        description=department_data.description
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    return department