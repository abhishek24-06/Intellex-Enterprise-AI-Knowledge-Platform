from sqlalchemy import Integer, String, DateTime,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime,UTC
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.team import Team
    from app.models.users import User
    from app.models.documents import Document

class Organization(Base):
    __tablename__="organizations"

    organization_id: Mapped[int]= mapped_column(Integer,primary_key=True,index=True)

    name  : Mapped[str]= mapped_column(String(255))

    industry: Mapped[str]=mapped_column(String(100),nullable=True)
    
    created_at: Mapped[datetime]= mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))##Lambda adds timestamps only when new row is added not when app starts

    is_active: Mapped[bool]=mapped_column(Boolean,default=True)

    #RELATIONSHIPS

    departments:Mapped[list["Department"]]=relationship(back_populates="organization",cascade="all, delete-orphan")

    teams:Mapped[list["Team"]]=relationship(back_populates="organization",cascade="all, delete-orphan")

    users:Mapped[list["User"]]=relationship(back_populates="organization")

    documents:Mapped[list["Document"]]=relationship(back_populates="organization")


