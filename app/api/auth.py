from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse

from app.services.auth_service import login_user
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_org_admin
from app.models.users import User
from app.schemas.auth import CurrentUserResponse

router=APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login",response_model=TokenResponse)
def login(login_data:LoginRequest,db:Session=Depends(get_db)):
    
    return login_user(db,login_data)

@router.get("/me",response_model=CurrentUserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user

