from sqlalchemy import Integer,String,DateTime,ForeignKey,Boolean,Enum
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime,UTC
from app.models.base import Base
from app.enums.enums import FeedbackType
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.documents import Document
    from app.models.chat_session import ChatSession

class ChatHistory(Base):
    __tablename__="chat_history"

    chat_id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)

    # user_id:Mapped[int]=mapped_column(ForeignKey("users.user_id"),nullable=False)

    document_id:Mapped[int]=mapped_column(ForeignKey("documents.document_id"),nullable=False)

    session_id:Mapped[int]=mapped_column(ForeignKey("chat_session.session_id"),nullable=False)

    question:Mapped[str]=mapped_column(String(1000),nullable=False)

    answer:Mapped[str]=mapped_column(String(1000),nullable=False)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    feedback:Mapped[FeedbackType]=mapped_column(Enum(FeedbackType))

    #RELATIONSHIP

    document:Mapped["Document"]=relationship(back_populates="chat_historys")

    session:Mapped["ChatSession"]=relationship(back_populates="messages")



