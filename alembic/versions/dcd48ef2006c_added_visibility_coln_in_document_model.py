"""Added visibility coln in document model"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "dcd48ef2006c"
down_revision: Union[str, Sequence[str], None] = "ecce575d4b37"
branch_labels = None
depends_on = None


document_visibility = sa.Enum(
    "ORGANIZATION",
    "RESTRICTED",
    name="documentvisibility",
)


def upgrade() -> None:

    # Create PostgreSQL enum type
    document_visibility.create(op.get_bind(), checkfirst=True)

    # Add the new column
    op.add_column(
        "documents",
        sa.Column(
            "visibility",
            document_visibility,
            nullable=False,
            server_default="ORGANIZATION",
        ),
    )

    # Remove the temporary default
    op.alter_column(
        "documents",
        "visibility",
        server_default=None,
    )


def downgrade() -> None:

    op.drop_column("documents", "visibility")

    document_visibility.drop(op.get_bind(), checkfirst=True)