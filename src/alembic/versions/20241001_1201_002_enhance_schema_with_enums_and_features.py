"""Enhance schema with enums, custom fields, tags, and improved structure

Revision ID: 002
Revises: 001
Create Date: 2024-10-01 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    priority_enum = sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', name='priority')
    status_enum = sa.Enum('NEW', 'OPEN', 'PENDING', 'ON_HOLD', 'RESOLVED', 'CLOSED', name='status')
    ticket_type_enum = sa.Enum('INCIDENT', 'REQUEST', 'PROBLEM', 'CHANGE', name='tickettype')
    
    priority_enum.create(op.get_bind())
    status_enum.create(op.get_bind())
    ticket_type_enum.create(op.get_bind())
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'])
    
    # Create custom_fields table
    op.create_table('custom_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('field_type', sa.String(length=20), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('options', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ticket_tags association table
    op.create_table('ticket_tags',
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('ticket_id', 'tag_id', name='uq_ticket_tag')
    )
    
    # Create custom_field_values table
    op.create_table('custom_field_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['field_id'], ['custom_fields.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_id', 'field_id', name='uq_ticket_field')
    )
    
    # Modify existing tickets table
    # First, add new columns with defaults
    op.add_column('tickets', sa.Column('priority', priority_enum, nullable=True))
    op.add_column('tickets', sa.Column('ticket_type', ticket_type_enum, nullable=True))
    op.add_column('tickets', sa.Column('resolution_notes', sa.Text(), nullable=True))
    op.add_column('tickets', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('tickets', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    op.add_column('tickets', sa.Column('closed_at', sa.DateTime(), nullable=True))
    op.add_column('tickets', sa.Column('due_date', sa.DateTime(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE tickets SET priority = 'NORMAL' WHERE priority IS NULL")
    op.execute("UPDATE tickets SET ticket_type = 'INCIDENT' WHERE ticket_type IS NULL")
    op.execute("UPDATE tickets SET updated_at = created_date WHERE updated_at IS NULL")
    
    # Make priority and ticket_type non-nullable after setting defaults
    op.alter_column('tickets', 'priority', nullable=False)
    op.alter_column('tickets', 'ticket_type', nullable=False)
    op.alter_column('tickets', 'updated_at', nullable=False)
    
    # Modify existing columns
    op.alter_column('tickets', 'title', nullable=False)
    op.alter_column('tickets', 'description', type_=sa.Text(), nullable=False)
    op.alter_column('tickets', 'customer', nullable=False)
    op.alter_column('tickets', 'agent_notes', type_=sa.Text())
    
    # Change status column to use enum
    # First rename the old column
    op.alter_column('tickets', 'status', new_column_name='status_old')
    
    # Add new status column with enum
    op.add_column('tickets', sa.Column('status', status_enum, nullable=True))
    
    # Migrate data from old status to new status with enum values
    op.execute("""
        UPDATE tickets SET status = 
        CASE 
            WHEN LOWER(status_old) = 'new' THEN 'NEW'
            WHEN LOWER(status_old) = 'open' THEN 'OPEN'
            WHEN LOWER(status_old) = 'pending' THEN 'PENDING'
            WHEN LOWER(status_old) = 'resolved' THEN 'RESOLVED'
            WHEN LOWER(status_old) = 'closed' THEN 'CLOSED'
            ELSE 'NEW'
        END
    """)
    
    # Make status non-nullable and drop old column
    op.alter_column('tickets', 'status', nullable=False)
    op.drop_column('tickets', 'status_old')
    
    # Rename created_date to created_at for consistency
    op.alter_column('tickets', 'created_date', new_column_name='created_at')
    
    # Add indexes for better performance
    op.create_index(op.f('ix_tickets_priority'), 'tickets', ['priority'])
    op.create_index(op.f('ix_tickets_status'), 'tickets', ['status'])
    op.create_index(op.f('ix_tickets_ticket_type'), 'tickets', ['ticket_type'])
    op.create_index(op.f('ix_tickets_customer'), 'tickets', ['customer'])
    op.create_index(op.f('ix_tickets_agent'), 'tickets', ['agent'])
    op.create_index(op.f('ix_tickets_created_at'), 'tickets', ['created_at'])
    op.create_index(op.f('ix_tickets_due_date'), 'tickets', ['due_date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_tickets_due_date'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_created_at'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_agent'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_customer'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_ticket_type'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_status'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_priority'), table_name='tickets')
    
    # Revert tickets table changes
    op.alter_column('tickets', 'created_at', new_column_name='created_date')
    
    # Add old status column back
    op.add_column('tickets', sa.Column('status_old', sa.String(length=100), nullable=True))
    
    # Migrate enum status back to string
    op.execute("""
        UPDATE tickets SET status_old = 
        CASE 
            WHEN status = 'NEW' THEN 'new'
            WHEN status = 'OPEN' THEN 'open'
            WHEN status = 'PENDING' THEN 'pending'
            WHEN status = 'ON_HOLD' THEN 'on_hold'
            WHEN status = 'RESOLVED' THEN 'resolved'
            WHEN status = 'CLOSED' THEN 'closed'
            ELSE 'new'
        END
    """)
    
    # Drop enum status column and rename old back
    op.drop_column('tickets', 'status')
    op.alter_column('tickets', 'status_old', new_column_name='status')
    
    # Revert other column changes
    op.alter_column('tickets', 'agent_notes', type_=sa.String(length=1000))
    op.alter_column('tickets', 'customer', nullable=True)
    op.alter_column('tickets', 'description', type_=sa.String(length=250), nullable=True)
    op.alter_column('tickets', 'title', nullable=True)
    
    # Drop new columns
    op.drop_column('tickets', 'due_date')
    op.drop_column('tickets', 'closed_at')
    op.drop_column('tickets', 'resolved_at')
    op.drop_column('tickets', 'updated_at')
    op.drop_column('tickets', 'resolution_notes')
    op.drop_column('tickets', 'ticket_type')
    op.drop_column('tickets', 'priority')
    
    # Drop new tables
    op.drop_table('custom_field_values')
    op.drop_table('ticket_tags')
    op.drop_table('custom_fields')
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')
    
    # Drop enum types
    sa.Enum(name='tickettype').drop(op.get_bind())
    sa.Enum(name='status').drop(op.get_bind())
    sa.Enum(name='priority').drop(op.get_bind())