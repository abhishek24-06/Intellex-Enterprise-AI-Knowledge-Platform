from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.users import User
from app.enums.enums import UserRole
from app.dependencies.roles import require_org_admin 
from app.schemas.users import CreateEmployeeRequest,CreateOrgAdminRequest, CreateUserRequest,UpdateUserRequest,ChangeUserRoleRequest,UserResponse
from app.services.user_service import create_user,get_user_by_id,change_user_role,update_user,get_users_by_organization

router=APIRouter(prefix="/users",tags=["Users"])

@router.get("/",response_model=list[UserResponse])
def get_all_users(db:Session=Depends(get_db),
              current_user:User=Depends(require_org_admin)):

    return get_users_by_organization(
        db=db,organization_id=current_user.organization_id
    )

@router.get("/{user_id}",response_model=UserResponse)
def get_user_by_id_api(user_id:int,db:Session=Depends(get_db),current_user:User=Depends(require_org_admin)):

    user=get_user_by_id(db=db,id=user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

    if user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Access denied",)

    return user

@router.post("/employees",response_model=UserResponse)
def create_employee_api(user_data:CreateEmployeeRequest,
                    db:Session=Depends(get_db),
                    current_user:User=Depends(require_org_admin)):

    return create_user(db=db,
                name=user_data.name,
                email=user_data.email,
                password=user_data.password,
                role=UserRole.EMPLOYEE,
                organization_id=current_user.organization_id,
                department_id=user_data.department_id,
                team_id=user_data.team_id)

@router.post("/org-admins",response_model=UserResponse)
def create_org_amdin_api(user_data:CreateOrgAdminRequest,
                         db:Session=Depends(get_db),
                         current_user:User=Depends(require_org_admin)):

    return create_user(db=db,
                name=user_data.name,
                email=user_data.email,
                password=user_data.password,
                role=UserRole.ORG_ADMIN,
                organization_id=current_user.organization_id,
                department_id=None,
                team_id=None)
    
@router.patch("/{user_id}",response_model=UserResponse)
def update_exsting_user(user_id:int,
                        request:UpdateUserRequest,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(require_org_admin)):

    return update_user(db=db,
                      user_id=user_id,
                      user_data=request,
                      organization_id=current_user.organization_id)

@router.patch("/{user_id}/role",response_model=UserResponse)
def update_user_role(user_id:int,
                     request:ChangeUserRoleRequest,
                     db:Session=Depends(get_db),
                     current_user:User=Depends(require_org_admin)):

    return change_user_role(db=db,
                     user_id=user_id,
                     role_data=request,
                     organization_id=current_user.organization_id)
        