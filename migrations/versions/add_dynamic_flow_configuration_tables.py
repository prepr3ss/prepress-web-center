"""Add dynamic flow configuration tables

Revision ID: add_dynamic_flow_configuration_tables
Revises: 
Create Date: 2025-12-17 13:39:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_dynamic_flow_configuration_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create rnd_flow_configurations table
    op.create_table('rnd_flow_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sample_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rnd_flow_configurations_id'), 'rnd_flow_configurations', ['id'], unique=False)
    op.create_index(op.f('ix_rnd_flow_configurations_name'), 'rnd_flow_configurations', ['name'], unique=False)
    op.create_index(op.f('ix_rnd_flow_configurations_sample_type'), 'rnd_flow_configurations', ['sample_type'], unique=False)

    # Create rnd_flow_steps table
    op.create_table('rnd_flow_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flow_configuration_id', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(length=255), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['flow_configuration_id'], ['rnd_flow_configurations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rnd_flow_steps_flow_configuration_id'), 'rnd_flow_steps', ['flow_configuration_id'], unique=False)
    op.create_index(op.f('ix_rnd_flow_steps_id'), 'rnd_flow_steps', ['id'], unique=False)

    # Add flow_configuration_id column to rnd_jobs table
    op.add_column('rnd_jobs', sa.Column('flow_configuration_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_rnd_jobs_flow_configuration_id', 'rnd_jobs', 'rnd_flow_configurations', ['flow_configuration_id'], ['id'])
    op.create_index(op.f('ix_rnd_jobs_flow_configuration_id'), 'rnd_jobs', ['flow_configuration_id'], unique=False)


def downgrade():
    # Remove flow_configuration_id from rnd_jobs
    op.drop_index(op.f('ix_rnd_jobs_flow_configuration_id'), table_name='rnd_jobs')
    op.drop_constraint('fk_rnd_jobs_flow_configuration_id', table_name='rnd_jobs', type_='foreignkey')
    op.drop_column('rnd_jobs', 'flow_configuration_id')

    # Drop rnd_flow_steps table
    op.drop_index(op.f('ix_rnd_flow_steps_id'), table_name='rnd_flow_steps')
    op.drop_index(op.f('ix_rnd_flow_steps_flow_configuration_id'), table_name='rnd_flow_steps')
    op.drop_table('rnd_flow_steps')

    # Drop rnd_flow_configurations table
    op.drop_index(op.f('ix_rnd_flow_configurations_sample_type'), table_name='rnd_flow_configurations')
    op.drop_index(op.f('ix_rnd_flow_configurations_name'), table_name='rnd_flow_configurations')
    op.drop_index(op.f('ix_rnd_flow_configurations_id'), table_name='rnd_flow_configurations')
    op.drop_table('rnd_flow_configurations')