from sqlalchemy import Integer, String,DateTime,ForeignKey,Boolean,Enum
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime,UTC
from app.enums.enums import UserRole
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.department import Department
    from app.models.team import Team
    from app.models.chat_session import ChatSession
    from app.models.documents import Document

class User(Base):
    __tablename__="users"

    user_id: Mapped[int]= mapped_column(Integer,primary_key=True,index=True)
    
    organization_id: Mapped[int]= mapped_column(ForeignKey("organizations.organization_id"),nullable=False) 

    department_id:Mapped[int]=mapped_column(ForeignKey("departments.department_id"),nullable=True)

    team_id:Mapped[int]=mapped_column(ForeignKey("teams.team_id"),nullable=True)    
    
    name: Mapped[str]= mapped_column(String(100),nullable=False)
    
    role: Mapped[UserRole]= mapped_column(Enum(UserRole),nullable=False)
    
    email: Mapped[str]= mapped_column(String(254),nullable=False,unique=True,index=True)
    
    hashed_password: Mapped[str]= mapped_column(String(255),nullable=False)
    
    created_at: Mapped[datetime]= mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))##Lambda adds timestamps only when new row is added not when app starts
    
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)

    #REALTIONSHIP

    department: Mapped["Department"] = relationship(back_populates="users")

    organization: Mapped["Organization"] = relationship(back_populates="users")

    team: Mapped["Team"]=relationship(back_populates="users")

    chat_sessions:Mapped[list["ChatSession"]]=relationship(back_populates="user",cascade="all, delete-orphan")

    documents: Mapped[list["Document"]] = relationship(back_populates="uploader")

    
