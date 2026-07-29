from app.enums.enums import EmbeddingStatus
from app.models.base import Base
from sqlalchemy import Integer,String,ForeignKey,Boolean,DateTime,UniqueConstraint,Enum,JSON
from sqlalchemy.orm import mapped_column,Mapped,relationship
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.documents import Document

class DocumentChunk(Base):
    __tablename__="document_chunks"

    __table_args__=(
        UniqueConstraint(
            "documenr_id",
            "chunk_index",
            name="uq_document_chunk_index"
        ),
    )

    chunk_id:Mapped[int]=mapped_column(primary_key=True,index=True)

    document_id:Mapped[int]=mapped_column(ForeignKey("documents.document_id",ondelete="CASCADE"),nullable=False)

    chunk_index:Mapped[int]=mapped_column(nullable=True)

    chunk_text:Mapped[str]=mapped_column(String(500),nullable=False)

    token_count:Mapped[int]=mapped_column(Integer,nullable=False)

    vector_id:Mapped[str|None]=mapped_column(String(255),unique=True,nullable=False)

    metadata_json:Mapped[dict|None]=mapped_column(JSON,nullable=True)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC),onupdate=lambda:datetime.now(UTC))

    #RELATIONSHIPS
    documents:Mapped["Document"]=relationship(back_populates="chunks")

