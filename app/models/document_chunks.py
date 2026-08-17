from app.models.base import Base
from sqlalchemy import Integer,String,ForeignKey,DateTime,UniqueConstraint,JSON,Text
from sqlalchemy.orm import mapped_column,Mapped,relationship
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from pgvector.sqlalchemy import Vector

if TYPE_CHECKING:
    from app.models.documents import Document

class DocumentChunk(Base):
    __tablename__="document_chunks"

    __table_args__=(
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_index"
        ),
    )

    chunk_id:Mapped[int]=mapped_column(primary_key=True,index=True)

    document_id:Mapped[int]=mapped_column(ForeignKey("documents.document_id",ondelete="CASCADE"),nullable=False)

    chunk_index:Mapped[int]=mapped_column(nullable=False)

    chunk_text:Mapped[str]=mapped_column(Text,nullable=False)

    token_count:Mapped[int]=mapped_column(Integer,nullable=False)

    embedding:Mapped[list[float] | None]=mapped_column(Vector(1024),nullable=True)

    metadata_json:Mapped[dict]=mapped_column(JSON,nullable=False)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC),onupdate=lambda:datetime.now(UTC))

    #RELATIONSHIPS
    document:Mapped["Document"]=relationship(back_populates="chunks")

