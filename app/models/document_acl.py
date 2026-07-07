from datetime import UTC, datetime
from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column,relationship
from app.models.base import Base
from app.enums.enums import PrincipalType, PermissionType
from sqlalchemy import UniqueConstraint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.documents import Document


class DocumentACL(Base):
    __tablename__ = "document_acls"

    __table_args__ = (
    UniqueConstraint(
        "document_id",
        "principal_type",
        "principal_id",
        "permission",
        name="uq_document_acl"
    ),
)
    acl_id: Mapped[int] = mapped_column(primary_key=True,index=True)

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.document_id"),nullable=False)

    principal_type: Mapped[PrincipalType] = mapped_column(Enum(PrincipalType),nullable=False)

    principal_id: Mapped[int] = mapped_column(nullable=False)

    permission: Mapped[PermissionType] = mapped_column(Enum(PermissionType),nullable=False,default=PermissionType.READ)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(UTC))

    #RELATIONSHIP

    document: Mapped["Document"]=relationship(back_populates="acl_entries")



