"""add hnsw index on document_chunks embedding for vector search

Revision ID: a1b2c3d4e5f6
Revises: 28b74fcd8361
Create Date: 2026-08-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '28b74fcd8361'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add HNSW index for vector similarity search."""
    # Create HNSW index on embedding column for cosine similarity search
    # This dramatically speeds up vector similarity queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    """Downgrade schema - Remove HNSW index."""
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")