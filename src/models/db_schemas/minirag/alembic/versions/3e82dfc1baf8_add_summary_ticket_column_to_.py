"""add summary_ticket column to conversations

Revision ID: 3e82dfc1baf8
Revises: 4186cd075862
Create Date: 2026-08-24 00:09:30.437686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '3e82dfc1baf8'
down_revision: Union[str, None] = '4186cd075862'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('summary_ticket', sa.String(), nullable=True))
    op.alter_column('conversations', 'title',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('conversations', 'title',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('conversations', 'summary_ticket')