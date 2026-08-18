from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_session import ChatSession
from app.models.users import User

def create_chat_session(*,db:Session,current_user:User,title:str|None=None)->ChatSession:

    session = ChatSession(user_id=current_user.user_id,title=title)

    db.add(session)
    db.commit()
    db.refresh(session)

    return session

def get_user_chat_sessions(*,db: Session,current_user: User) -> list[ChatSession]:

    stmt = (select(ChatSession).where(ChatSession.user_id==current_user.user_id)
            .order_by (ChatSession.is_pinned.desc(),
                       ChatSession.last_active.desc()))

    return list(db.execute(stmt).scalars().all())

def get_chat_session(*,db: Session,session_id: int,current_user: User) -> ChatSession | None:

    stmt = select(ChatSession).where(ChatSession.session_id == session_id,ChatSession.user_id == current_user.user_id)

    return list(db.execute(stmt).scalar_one_or_none())

def delete_chat_session(*,db: Session,session_id: int,current_user: User) -> bool:

    session = get_chat_session(db=db,session_id=session_id,current_user=current_user,)

    if session is None:
        return False

    db.delete(session)
    db.commit()

    return True
