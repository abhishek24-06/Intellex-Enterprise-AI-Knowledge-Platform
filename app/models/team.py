from sqlalchemy import Integer,String,DateTime,ForeignKey,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime,UTC
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.department import Department
    from app.models.organization import Organization

class Team(Base):
    __tablename__="teams"

    team_id:Mapped[int]=mapped_column(primary_key=True,index=True)

    department_id:Mapped[int]=mapped_column(ForeignKey("departments.department_id"),nullable=False)

    organization_id:Mapped[int]=mapped_column(ForeignKey("organizations.organization_id"),nullable=False)

    name:Mapped[str]=mapped_column(String(255),nullable=False)

    description:Mapped[str]=mapped_column(String(255),nullable=False)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    #RELATIONSHIPS
    department:Mapped["Department"]=relationship(back_populates="teams")

    organization:Mapped["Organization"]=relationship(back_populates="teams")

    users: Mapped[list["User"]]=relationship(back_populates="team")



