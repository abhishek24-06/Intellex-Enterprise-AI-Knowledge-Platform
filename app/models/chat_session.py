from sqlalchemy import Integer,String,DateTime,ForeignKey,Boolean,Enum
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime,UTC
from app.models.base import Base
from app.enums.enums import FeedbackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.chat_history import ChatHistory

class ChatSession(Base):
    __tablename__="chat_session"

    session_id:Mapped[int]=mapped_column(primary_key=True,index=True)

    user_id:Mapped[int]=mapped_column(ForeignKey("users.user_id"),nullable=False)

    title:Mapped[str]=mapped_column(String(255),nullable=True)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    last_active:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    is_pinned: Mapped[bool] = mapped_column(default=False)

    #RELATIONSHIP

    user:Mapped["User"]=relationship(back_populates="chat_sessions")

    messages: Mapped[list["ChatHistory"]] = relationship(back_populates="session",cascade="all, delete-orphan")


