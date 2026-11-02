
"""allow nullable transaction description

Revision ID: 200c45ad063e
Revises: 0cf66e0d8b44
Create Date: 2026-10-29 13:19:06.404923
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "200c45ad063e"
down_revision: Union[str, Sequence[str], None] = "0cf66e0d8b44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow transaction descriptions to be NULL."""
    op.alter_column(
        "transactions",
        "description",
        existing_type=sa.String(length=500),
        nullable=True,
    )


def downgrade() -> None:
    """Restore the description column to NOT NULL."""
    op.execute(
        """
        UPDATE transactions
        SET description = ''
        WHERE description IS NULL
        """
    )

    op.alter_column(
        "transactions",
        "description",
        existing_type=sa.String(length=500),
        nullable=False,
    )
