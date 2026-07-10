from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import login_user

router=APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login/",response_model=TokenResponse)
def login(login_data:LoginRequest,db:Session=Depends(get_db)):
    
    return login_user(db,login_data)


