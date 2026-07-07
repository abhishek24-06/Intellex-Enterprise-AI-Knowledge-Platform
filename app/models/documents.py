from sqlalchemy import Integer,String,DateTime,ForeignKey,Boolean,Enum
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime,UTC
from app.models.base import Base
from app.enums.enums import DocumentStatus,DocumentType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.chat_history import ChatHistory
    from app.models.users import User
    from app.models.document_acl import DocumentACL

class Document(Base):
    __tablename__="documents"

    document_id:Mapped[int]=mapped_column(primary_key=True,index=True)

    organization_id:Mapped[int]=mapped_column(ForeignKey("organizations.organization_id"),nullable=False)

    uploaded_by:Mapped[int]=mapped_column(ForeignKey("users.user_id"),nullable=False)

    document_type:Mapped[DocumentType]=mapped_column(Enum(DocumentType),nullable=False)

    title:Mapped[str]=mapped_column(String(255),nullable=False)

    description:Mapped[str]=mapped_column(String(255),nullable=True)

    original_filename:Mapped[str]=mapped_column(String(255),nullable=False)

    stored_filename:Mapped[str]=mapped_column(String(255),nullable=False)

    status:Mapped[DocumentStatus]=mapped_column(Enum(DocumentStatus),nullable=False)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    file_path: Mapped[str] = mapped_column(String(500),nullable=False)

    file_size: Mapped[int] = mapped_column(nullable=False)

    mime_type: Mapped[str] = mapped_column(String(100),nullable=False)

    processing_error: Mapped[str | None]=mapped_column(String(500),nullable=True)

    is_deleted: Mapped[bool]=mapped_column(default=False)

    #RELATIONSHIP

    organization:Mapped["Organization"]=relationship(back_populates="documents")

    chat_historys:Mapped[list["ChatHistory"]]=relationship(back_populates="document")

    uploader: Mapped["User"] = relationship(back_populates="documents")

    acl_entries: Mapped[list["DocumentACL"]]=relationship(back_populates="document",cascade="all,delete-orphan")








