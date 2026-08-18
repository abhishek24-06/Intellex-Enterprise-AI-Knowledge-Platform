from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from torch import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.chat_history import ChatHistory
    from app.models.documents import Document

class ChatSource(Base):

    __tablename__ = "chat_source"

    __table_args__ =(UniqueConstraint( 
            "chat_id",
            "document_id",
            name="uq_chat_source"
        ),
    )

    source_id: Mapped[int] = mapped_column(primary_key=True,index=True)

    chat_id: Mapped[int] = mapped_column(ForeignKey("chat_history.chat_id", ondelete="CASCADE"),nullable=False)

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.document_id"),nullable=False)

    #RELATIONSHIP

    chat: Mapped["ChatHistory"] = relationship(back_populates="sources")

    document: Mapped["Document"] = relationship()