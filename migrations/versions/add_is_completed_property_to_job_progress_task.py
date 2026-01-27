"""Add is_completed property to JobProgressTask for backward compatibility

Revision ID: add_is_completed_property_to_job_progress_task
Revises: 43cc4ce79ce4
Create Date: 2025-12-09 14:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_completed_property_to_job_progress_task'
down_revision = '43cc4ce79ce4'
branch_labels = None
depends_on = None


def upgrade():
    # No actual database changes needed as is_completed is a property
    # This migration is just for documentation purposes
    pass


def downgrade():
    # No changes to revert
    pass