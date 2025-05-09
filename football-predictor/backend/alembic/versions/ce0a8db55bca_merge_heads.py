"""merge heads

Revision ID: ce0a8db55bca
Revises: add_match_time_column, ef06a844ad61
Create Date: 2025-05-09 03:30:58.298312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce0a8db55bca'
down_revision: Union[str, None] = ('add_match_time_column', 'ef06a844ad61')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
