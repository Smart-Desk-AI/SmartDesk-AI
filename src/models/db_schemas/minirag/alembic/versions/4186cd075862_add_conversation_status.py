from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4186cd075862'
down_revision = 'faddeeaa792e'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Explicitly create the ENUM type
    status_enum = postgresql.ENUM('ACTIVE', 'CLOSED', name='conversationstatusenum')
    status_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. Add the column
    op.add_column('conversations', sa.Column(
        'status', 
        sa.Enum('ACTIVE', 'CLOSED', name='conversationstatusenum'), 
        nullable=False,
        server_default='ACTIVE'
    ))

def downgrade() -> None:
    op.drop_column('conversations', 'status')
    
    status_enum = postgresql.ENUM('ACTIVE', 'CLOSED', name='conversationstatusenum')
    status_enum.drop(op.get_bind(), checkfirst=True)