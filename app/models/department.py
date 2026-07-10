from sqlalchemy import Integer,String,DateTime,ForeignKey,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime,UTC
from app.models.base import Base
from sqlalchemy import UniqueConstraint

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.team import Team
    from app.models.users import User

class Department(Base):
    __tablename__="departments"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_department_org_name"
        ),
    )

    department_id:Mapped[int]=mapped_column(primary_key=True,index=True)

    organization_id:Mapped[int]=mapped_column(ForeignKey("organizations.organization_id"),nullable=False)

    name:Mapped[str]=mapped_column(String(255),nullable=False)

    description:Mapped[str]=mapped_column(String(255),nullable=False)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    #RELATIONSHIP

    organization:Mapped["Organization"]=relationship(back_populates="departments")

    users:Mapped[list["User"]]=relationship(back_populates="department")

    teams:Mapped[list["Team"]]=relationship(back_populates="department")

