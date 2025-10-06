"""Add attachments table for file uploads

Revision ID: 003
Revises: 002
Create Date: 2024-10-01 12:02:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create attachments table
    op.create_table('attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('uploaded_by', sa.String(length=200), nullable=True),
        sa.Column('is_image', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for better performance
    op.create_index(op.f('ix_attachments_ticket_id'), 'attachments', ['ticket_id'])
    op.create_index(op.f('ix_attachments_created_at'), 'attachments', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_attachments_created_at'), table_name='attachments')
    op.drop_index(op.f('ix_attachments_ticket_id'), table_name='attachments')
    
    # Drop table
    op.drop_table('attachments')