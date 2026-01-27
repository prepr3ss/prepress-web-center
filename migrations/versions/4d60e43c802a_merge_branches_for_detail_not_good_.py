"""Merge branches for detail_not_good_field and multiple_attachments

Revision ID: 4d60e43c802a
Revises: add_detail_not_good_field, add_multiple_attachments_to_ctp_problem_logs
Create Date: 2025-12-06 09:00:28.201709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d60e43c802a'
down_revision = ('add_detail_not_good_field', 'add_multiple_attachments_to_ctp_problem_logs')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
