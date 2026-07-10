from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import User
from app.enums.enums import UserRole
from app.core.security import hash_password

def get_user_by_email(db:Session,email:str)->User | None:
    stmt = (select(User).where(User.email == email))

    return db.execute(stmt).scalar_one_or_none()

def get_user_by_id(db:Session,id:int)->User | None:
    stmt=(select(User).where(User.user_id==id))

    return db.execute(stmt).scalar_one_or_none()

def create_user(db:Session,
                *,
                name:str,
                email:str,
                password:str,
                role:UserRole,
                organization_id:int,
                department_id:int,
                team_id:int |None=None)->User:
    
    if role==UserRole.EMPLOYEE:
        if department_id is None:
            raise ValueError("Employees must belong to a department.")
    
    existing_user=get_user_by_email(db=db,email=email)

    if existing_user:
        raise ValueError("Email already registered")
    
    hashed_password=hash_password(password=password)

    new_user=User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role=role,
        organization_id=organization_id,
        department_id=department_id,
        team_id=team_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user