"""
Revision ID: add_fivewoneh_table
Revises: 
Create Date: 2026-01-13
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import enum

# revision identifiers, used by Alembic.
revision = 'add_fivewoneh_table'
down_revision = None
branch_labels = None
depends_on = None

class FiveWOneHStatus(enum.Enum):
    draft = 'draft'
    open = 'open'
    closed = 'closed'

def upgrade():
    op.create_table(
        'five_w_one_h',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('who', sa.Text, nullable=False),
        sa.Column('what', sa.Text, nullable=False),
        sa.Column('when', sa.DateTime, nullable=False),
        sa.Column('where', sa.Text, nullable=False),
        sa.Column('why', sa.Text, nullable=False),
        sa.Column('how', sa.Text, nullable=False),
        sa.Column('owner_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('status', sa.Enum('draft', 'open', 'closed', name='fivewonehstatus'), nullable=False, server_default='draft'),
        sa.Column('attachment_path', sa.String(512)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

def downgrade():
    op.drop_table('five_w_one_h')
    op.execute('DROP TYPE IF EXISTS fivewonehstatus')
