"""Add cutlist and surface tables

Revision ID: add_cutlist_tables
Revises: add_task_tables
Create Date: 2025-01-04 18:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_cutlist_tables'
down_revision = 'add_task_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create cutlists table
    op.create_table('cutlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index(op.f('ix_cutlists_user_id'), 'cutlists', ['user_id'], unique=False)

    # Create surfaces table
    op.create_table('surfaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cutlist_id', sa.Integer(), nullable=False),
        sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cutlist_id'], ['cutlists.id'], )
    )
    op.create_index(op.f('ix_surfaces_cutlist_id'), 'surfaces', ['cutlist_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_surfaces_cutlist_id'), table_name='surfaces')
    op.drop_table('surfaces')
    op.drop_index(op.f('ix_cutlists_user_id'), table_name='cutlists')
    op.drop_table('cutlists')
