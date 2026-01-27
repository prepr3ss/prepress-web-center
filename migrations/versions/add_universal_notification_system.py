"""Add Universal Notification System tables

Revision ID: universal_notifications_001
Revises: 
Create Date: 2025-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'universal_notifications_001'
down_revision = None  # Change ini ke revision terakhir jika ada
branch_labels = None
depends_on = None


def upgrade():
    # Create universal_notifications table
    op.create_table(
        'universal_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_resource_type', sa.String(50), nullable=False),
        sa.Column('related_resource_id', sa.Integer(), nullable=False),
        sa.Column('triggered_by_user_id', sa.Integer(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_universal_notifications_notification_type'), 'universal_notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_universal_notifications_created_at'), 'universal_notifications', ['created_at'], unique=False)
    
    # Create notification_recipients table
    op.create_table(
        'notification_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['notification_id'], ['universal_notifications.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_recipients_user_id'), 'notification_recipients', ['user_id'], unique=False)
    op.create_index(op.f('ix_notification_recipients_is_read'), 'notification_recipients', ['is_read'], unique=False)
    op.create_index(op.f('ix_notification_recipients_notification_id'), 'notification_recipients', ['notification_id'], unique=False)


def downgrade():
    # Drop indices
    op.drop_index(op.f('ix_notification_recipients_notification_id'), table_name='notification_recipients')
    op.drop_index(op.f('ix_notification_recipients_is_read'), table_name='notification_recipients')
    op.drop_index(op.f('ix_notification_recipients_user_id'), table_name='notification_recipients')
    
    # Drop tables
    op.drop_table('notification_recipients')
    
    op.drop_index(op.f('ix_universal_notifications_created_at'), table_name='universal_notifications')
    op.drop_index(op.f('ix_universal_notifications_notification_type'), table_name='universal_notifications')
    op.drop_table('universal_notifications')
