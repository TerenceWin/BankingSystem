"""Create created_at for user column

Revision ID: 6a69cc48c9e9
Revises: 
Create Date: 2026-04-06 20:06:02.834349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a69cc48c9e9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'created_at')
    pass