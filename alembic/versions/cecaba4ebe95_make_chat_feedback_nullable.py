"""make chat feedback nullable

Revision ID: cecaba4ebe95
Revises: 81410be240c4
Create Date: 2026-08-18 20:06:44.241487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cecaba4ebe95'
down_revision: Union[str, Sequence[str], None] = '81410be240c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.alter_column(
        "chat_history",
        "feedback",
        existing_type=sa.Enum(
            "Good",
            "Satisfactory",
            "Bad",
            name="feedbacktype",
        ),
        nullable=True,
    )


def downgrade() -> None:

    op.alter_column(
        "chat_history",
        "feedback",
        existing_type=sa.Enum(
            "Good",
            "Satisfactory",
            "Bad",
            name="feedbacktype",
        ),
        nullable=False,
    )