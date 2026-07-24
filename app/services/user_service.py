from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import User
from app.enums.enums import UserRole
from app.core.security import hash_password
from app.schemas.users import UpdateUserRequest,ChangeUserRoleRequest
from app.services.department_service import get_department_by_id
from app.services.team_service import get_team_by_id

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
        if department_id is None or team_id is None:
            raise ValueError("Employees must belong to a department and team.")
        
    # elif role==UserRole.SUPER_ADMIN:
    #     organization_id=None
    #     department_id=None
    #     team_id=None

    elif role==UserRole.ORG_ADMIN:
        if organization_id is None:
            raise ValueError("Organization admin must belong to an organization.")

    
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

def get_users_by_organization(db:Session,
                              organization_id:int)->list[User]:
    
    stmt=select(User).where (User.organization_id == organization_id,
                             User.is_active == True)
    
    users=db.execute(stmt).scalars().all()

    return users

def update_user(db:Session,
                user_id:int,
                user_data:UpdateUserRequest,
                organization_id:int)->User:
    
    user=get_user_by_id(db=db,id=user_id)

    if user is None:
        raise ValueError("User not found")
        
    if user.organization_id != organization_id:
        raise ValueError("You cannot update users from another organization.")
    
    if user_data.email is not None:
        existing_user=get_user_by_email(db=db,email=user_data.email)

        if existing_user and existing_user.user_id != user.user_id:
            raise ValueError("Email already registered.")
    
    new_department_id = user.department_id
    new_team_id = user.team_id

    if user_data.department_id is not None:
        new_department_id = user_data.department_id

    if user_data.team_id is not None:
        new_team_id = user_data.team_id      

    if(user_data.department_id is not None
       and user_data.team_id is None):
       raise ValueError("Changing department requires selecting a team.")
    
    department = None
    team = None

    #DEPARTMENT
    if new_department_id is not None:
        department=get_department_by_id(db=db,department_id=new_department_id) 
    
        if department is None: 
            raise ValueError("Department does not exist") 
    
        if department.organization_id != organization_id:
            raise ValueError("Department does not belong to your organization")
    
    else:
        department = None

    #TEAM
    if new_team_id is not None:
        team = get_team_by_id(db=db,team_id=new_team_id,)

        if team is None:
            raise ValueError("Team does not exist")

        if team.organization_id != organization_id:
            raise ValueError("Team does not belong to your organization.") 

        if department is not None:
            if team.department_id != department.department_id:
                raise ValueError("Selected team does not belong to the selected department.")
            
    #UPDATING
    if user_data.name is not None:
        user.name = user_data.name

    if user_data.email is not None:
        user.email = user_data.email

    user.department_id = new_department_id
    user.team_id = new_team_id

    db.commit()
    db.refresh(user)

    return user

def change_user_role(db:Session,
                    user_id:int,
                    role_data:ChangeUserRoleRequest,
                    organization_id:int)-> User:
    
    role=role_data.role
    user = get_user_by_id(db=db, id=user_id)

    if user is None:
        raise ValueError("User not found")
    
    if user.organization_id != organization_id:
        raise ValueError("You cannot update users from another organization.")
    
    if role==UserRole.SUPER_ADMIN:
        raise ValueError("SUPER ADMIN cannot be assigned.")

    if role == user.role:
        return user
    
    if role == UserRole.EMPLOYEE:
        if user.department_id is None or user.team_id is None:
            raise ValueError("Employees must belong to a department and team.")
            
        department = get_department_by_id(db=db,department_id=user.department_id,)
        team = get_team_by_id(db=db,team_id=user.team_id,)
    
        if team.department_id != department.department_id:
            raise ValueError("Selected team does not belong to the selected department.")
    
    elif role == UserRole.ORG_ADMIN:
        user.department_id = None
        user.team_id = None

    user.role = role

    db.commit()
    db.refresh(user)

    return user
