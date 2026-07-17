from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.departments import CreateDepartmentRequest,DepartmentResponse
from app.database.database import get_db
from app.models.users import User
from app.dependencies.roles import require_org_admin
from app.services.department_service import create_department

router=APIRouter(
    prefix="/departments",
    tags=["Departments"]
)

@router.post("",response_model=DepartmentResponse)
def create_department_api(department_data:CreateDepartmentRequest,
                      db:Session=Depends(get_db),
                      current_user:User=Depends(require_org_admin)
                      ):
    
    department=create_department(
        db=db,
        department_data=department_data,
        organization_id=current_user.organization_id
    )

    return department

