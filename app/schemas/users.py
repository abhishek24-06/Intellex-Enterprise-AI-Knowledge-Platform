from pydantic import BaseModel,EmailStr,ConfigDict
from app.enums.enums import UserRole

class CreateUserRequest(BaseModel):
    name:str
    email:EmailStr
    password:str
    role:UserRole
    department_id:int| None=None
    team_id:int| None=None

class CreateEmployeeRequest(BaseModel):
    name:str
    email:EmailStr
    password:str
    department_id:int| None=None
    team_id:int| None=None

class CreateOrgAdminRequest(BaseModel):
    name:str
    email:EmailStr
    password:str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    role: UserRole
    organization_id: int | None
    department_id: int | None
    team_id: int | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UpdateUserRequest(BaseModel):
    name:str| None=None
    email:EmailStr| None=None
    department_id:int| None=None
    team_id:int| None=None

class ChangeUserRoleRequest(BaseModel):
    role: UserRole

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    new_password: str