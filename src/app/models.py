import enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, 
    Enum, Table, UniqueConstraint, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Priority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Status(enum.Enum):
    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketType(enum.Enum):
    INCIDENT = "incident"
    REQUEST = "request"
    PROBLEM = "problem"
    CHANGE = "change"

# Association table for many-to-many relationship between tickets and tags
ticket_tags = Table(
    'ticket_tags',
    Base.metadata,
    Column('ticket_id', Integer, ForeignKey('tickets.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
    UniqueConstraint('ticket_id', 'tag_id', name='uq_ticket_tag')
)

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), default='#808080')  # Hex color code
    description = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationship
    tickets = relationship("Ticket", secondary=ticket_tags, back_populates="tags")

class CustomField(Base):
    __tablename__ = 'custom_fields'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    field_type = Column(String(20), nullable=False)  # text, number, date, boolean, select
    is_required = Column(Boolean, default=False)
    options = Column(Text)  # JSON string for select field options
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationship
    values = relationship("CustomFieldValue", back_populates="field", cascade="all, delete-orphan")

class CustomFieldValue(Base):
    __tablename__ = 'custom_field_values'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    field_id = Column(Integer, ForeignKey('custom_fields.id', ondelete='CASCADE'), nullable=False)
    value = Column(Text)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="custom_field_values")
    field = relationship("CustomField", back_populates="values")
    
    __table_args__ = (UniqueConstraint('ticket_id', 'field_id', name='uq_ticket_field'),)

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    
    # Enhanced fields with enums
    priority = Column(Enum(Priority), default=Priority.NORMAL, nullable=False, index=True)
    status = Column(Enum(Status), default=Status.NEW, nullable=False, index=True)
    ticket_type = Column(Enum(TicketType), default=TicketType.INCIDENT, nullable=False, index=True)
    
    # User references (keeping as strings for now, can be converted to FKs later)
    customer = Column(String(200), nullable=False, index=True)
    agent = Column(String(200), index=True)
    
    # Additional fields
    agent_notes = Column(Text)
    resolution_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Due date for SLA tracking
    due_date = Column(DateTime, index=True)
    
    # Relationships
    tags = relationship("Tag", secondary=ticket_tags, back_populates="tickets")
    custom_field_values = relationship("CustomFieldValue", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="ticket", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title}', status='{self.status.value}')>"

class Attachment(Base):
    __tablename__ = 'attachments'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    file_path = Column(String(500), nullable=False)  # Path to stored file
    
    # Metadata
    uploaded_by = Column(String(200))  # User who uploaded the file
    is_image = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)  # Whether attachment is visible to customers
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationship
    ticket = relationship("Ticket", back_populates="attachments")
    
    def __repr__(self):
        return f"<Attachment(id={self.id}, filename='{self.filename}', ticket_id={self.ticket_id})>"