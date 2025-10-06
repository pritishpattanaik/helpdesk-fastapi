"""Baseline migration for existing tickets table

Revision ID: 001
Revises: 
Create Date: 2024-10-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the existing tickets table structure
    op.create_table('tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=True),
        sa.Column('description', sa.String(length=250), nullable=True),
        sa.Column('status', sa.String(length=100), nullable=True),
        sa.Column('customer', sa.String(length=200), nullable=True),
        sa.Column('agent', sa.String(length=200), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False),
        sa.Column('agent_notes', sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('tickets')