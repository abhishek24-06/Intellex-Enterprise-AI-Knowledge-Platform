from fastapi import Depends, HTTPException,status

from app.dependencies.auth import get_current_user
from app.enums.enums import UserRole
from app.models.users import User


def require_org_admin(current_user:User= Depends(get_current_user)):
    if current_user.role!=UserRole.ORG_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only organization administrators can perform this action.")
    
    return current_user

def require_super_admin(current_user:User= Depends(get_current_user)):
    if current_user.role!=UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Intellex Dev can perform this action.")
    
    return current_user