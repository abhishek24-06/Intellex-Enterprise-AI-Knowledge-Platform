from pydantic import BaseModel,EmailStr,ConfigDict
from app.enums.enums import UserRole

class RegisterRequest(BaseModel):
    name:str
    email:EmailStr
    password:str

class LoginRequest(BaseModel):
    email:EmailStr
    password:str

#After Login Return Token

class TokenResponse(BaseModel):
    access_token:str
    token_type:str="bearer"

class UserResponse(BaseModel):
    user_id:int
    name:str
    email:EmailStr

class CurrentUserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: UserRole
    organization_id: int | None
    department_id: int | None
    team_id: int | None

    model_config=ConfigDict(from_attributes=True)

