"""Add collaborative job notes table

Revision ID: add_collaborative_job_notes
Revises: 
Create Date: 2025-12-16 09:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_collaborative_job_notes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create rnd_job_notes table
    op.create_table('rnd_job_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('note_content', sa.Text(), nullable=False),
        sa.Column('note_type', sa.String(length=20), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['rnd_jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rnd_job_notes_job_id'), 'rnd_job_notes', ['job_id'], unique=False)
    op.create_index(op.f('ix_rnd_job_notes_user_id'), 'rnd_job_notes', ['user_id'], unique=False)


def downgrade():
    # Drop rnd_job_notes table
    op.drop_index(op.f('ix_rnd_job_notes_user_id'), table_name='rnd_job_notes')
    op.drop_index(op.f('ix_rnd_job_notes_job_id'), table_name='rnd_job_notes')
    op.drop_table('rnd_job_notes')