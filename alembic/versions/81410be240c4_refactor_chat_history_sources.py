"""refactor chat history sources

Revision ID: 81410be240c4
Revises: 66d6a6c3aa01
Create Date: 2026-08-18 12:27:52.393337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81410be240c4'
down_revision: Union[str, Sequence[str], None] = '66d6a6c3aa01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # --------------------------------------------------------------
    # chat_history
    # --------------------------------------------------------------

    op.drop_constraint(
        "chat_history_document_id_fkey",
        "chat_history",
        type_="foreignkey",
    )

    op.drop_column(
        "chat_history",
        "document_id",
    )

    op.alter_column(
        "chat_history",
        "question",
        existing_type=sa.VARCHAR(length=1000),
        type_=sa.Text(),
        existing_nullable=False,
    )

    op.alter_column(
        "chat_history",
        "answer",
        existing_type=sa.VARCHAR(length=1000),
        type_=sa.Text(),
        existing_nullable=False,
    )

    # --------------------------------------------------------------
    # chat_source
    # --------------------------------------------------------------

    op.create_table(
        "chat_source",

        sa.Column(
            "source_id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "chat_id",
            sa.Integer(),
            sa.ForeignKey(
                "chat_history.chat_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey(
                "documents.document_id",
            ),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "chat_id",
            "document_id",
            name="uq_chat_source",
        ),
    )


def downgrade() -> None:

    # --------------------------------------------------------------
    # Remove chat_source
    # --------------------------------------------------------------

    op.drop_table(
        "chat_source"
    )

    # --------------------------------------------------------------
    # Restore question/answer types
    # --------------------------------------------------------------

    op.alter_column(
        "chat_history",
        "question",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=1000),
        existing_nullable=False,
    )

    op.alter_column(
        "chat_history",
        "answer",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=1000),
        existing_nullable=False,
    )

    # --------------------------------------------------------------
    # Restore document_id
    # --------------------------------------------------------------

    op.add_column(
        "chat_history",
        sa.Column(
            "document_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "chat_history_document_id_fkey",
        "chat_history",
        "documents",
        ["document_id"],
        ["document_id"],
    )