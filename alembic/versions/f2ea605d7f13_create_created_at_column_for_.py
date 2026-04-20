"""Create created_at Column for beneficiary table

Revision ID: f2ea605d7f13
Revises: 6a69cc48c9e9
Create Date: 2026-04-06 20:25:44.121075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import models

# revision identifiers, used by Alembic.
revision: str = 'f2ea605d7f13'
down_revision: Union[str, Sequence[str], None] = '6a69cc48c9e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('beneficiary', sa.Column('created_at', sa.DateTime(), nullable=True))
    

def downgrade() -> None:
    op.drop_column('beneficiary', 'created_at')    
