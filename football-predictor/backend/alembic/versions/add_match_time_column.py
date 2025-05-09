"""add match_time column

Revision ID: add_match_time_column
Revises: 
Create Date: 2025-05-09 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_match_time_column'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add match_time column to fixtures table
    op.add_column('fixtures', sa.Column('match_time', sa.String(), nullable=True))


def downgrade():
    # Remove match_time column from fixtures table
    op.drop_column('fixtures', 'match_time') 