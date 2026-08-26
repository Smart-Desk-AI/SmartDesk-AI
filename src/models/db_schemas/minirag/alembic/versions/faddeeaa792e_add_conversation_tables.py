"""add conversation tables

Revision ID: faddeeaa792e
Revises: 2e076c46f2e7
Create Date: 2026-08-23 03:24:24.526122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'faddeeaa792e'
down_revision: Union[str, None] = '2e076c46f2e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.create_table('conversations',
        sa.Column('conversation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_uuid', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conversation_project_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_project_id'], ['projects.project_id'], ),
        sa.PrimaryKeyConstraint('conversation_id'),
        sa.UniqueConstraint('conversation_uuid')
    )


def downgrade() -> None:
    
    op.drop_table('conversations')