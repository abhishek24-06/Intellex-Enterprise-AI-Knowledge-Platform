from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.auth import LoginRequest,TokenResponse
from app.core.security import verify_password,create_access_token

def login_user(db:Session,login_data:LoginRequest):
    stmt=(select(User).where(User.email == login_data.email))    

    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise ValueError("Invalid email or password.")
    
    if not verify_password(login_data.password,user.hashed_password):
        raise ValueError("Invalid email or password.")
    
    access_token = create_access_token({
        "sub":str(user.user_id)
    })

    return TokenResponse(
        access_token=access_token
    )

    
    



