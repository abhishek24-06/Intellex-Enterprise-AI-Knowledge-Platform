"""rename role principal type to org admin

Revision ID: 66d6a6c3aa01
Revises: f2cf0054f8fa
Create Date: 2026-08-18 00:25:57.465939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66d6a6c3aa01'
down_revision: Union[str, Sequence[str], None] = 'f2cf0054f8fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
        ALTER TYPE principaltype
        RENAME VALUE 'ROLE' TO 'ORG_ADMIN'
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TYPE principaltype
        RENAME VALUE 'ORG_ADMIN' TO 'ROLE'
        """
    )