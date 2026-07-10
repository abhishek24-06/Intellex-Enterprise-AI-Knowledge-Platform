from pydantic import BaseModel,EmailStr

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