"""add composite indexes for vector search query optimization

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add composite indexes for vector search optimization."""
    
    # Composite index on documents for the common filter pattern:
    # organization_id + is_deleted + visibility + embedding_status
    # This helps the initial document filtering before joining with chunks
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_documents_org_visibility_embedding "
        "ON documents (organization_id, is_deleted, visibility, embedding_status) "
        "WHERE is_deleted = false AND embedding_status = 'COMPLETED'"
    )
    
    # Partial index on document_chunks for embedded chunks only
    # This avoids scanning chunks without embeddings
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedded "
        "ON document_chunks (document_id) "
        "WHERE embedding IS NOT NULL"
    )
    
    # Composite index on document_acls for efficient ACL lookups
    # Principal type + principal_id + document_id for the EXISTS subqueries
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_acls_principal_doc "
        "ON document_acls (principal_type, principal_id, document_id) "
        "WHERE principal_type IN ('USER', 'TEAM', 'DEPARTMENT', 'ORG_ADMIN')"
    )


def downgrade() -> None:
    """Downgrade schema - Remove composite indexes."""
    op.execute("DROP INDEX IF EXISTS ix_documents_org_visibility_embedding")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedded")
    op.execute("DROP INDEX IF EXISTS ix_document_acls_principal_doc")