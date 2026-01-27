"""Add multiple attachments to CTP problem logs

Revision ID: add_multiple_attachments_to_ctp_problem_logs
Revises: create_ctp_log_tables
Create Date: 2025-11-25 18:28:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_multiple_attachments_to_ctp_problem_logs'
down_revision = 'create_ctp_log_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create table for multiple photos
    op.create_table('ctp_problem_photos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_log_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['problem_log_id'], ['ctp_problem_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ctp_problem_photos_problem_log_id'), 'ctp_problem_photos', ['problem_log_id'], unique=False)
    
    # Create table for documents
    op.create_table('ctp_problem_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_log_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['problem_log_id'], ['ctp_problem_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ctp_problem_documents_problem_log_id'), 'ctp_problem_documents', ['problem_log_id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_ctp_problem_documents_problem_log_id'), table_name='ctp_problem_documents')
    op.drop_table('ctp_problem_documents')
    op.drop_index(op.f('ix_ctp_problem_photos_problem_log_id'), table_name='ctp_problem_photos')
    op.drop_table('ctp_problem_photos')