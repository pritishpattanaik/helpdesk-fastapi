from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Pydantic Enums matching SQLAlchemy enums
class PriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class StatusEnum(str, Enum):
    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketTypeEnum(str, Enum):
    INCIDENT = "incident"
    REQUEST = "request"
    PROBLEM = "problem"
    CHANGE = "change"

# Tag schemas
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#808080", pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=255)

class TagResponse(TagCreate):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Custom Field schemas
class CustomFieldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    field_type: str = Field(..., pattern=r"^(text|number|date|boolean|select)$")
    is_required: bool = False
    options: Optional[str] = None  # JSON string for select field options

class CustomFieldResponse(CustomFieldCreate):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CustomFieldValueCreate(BaseModel):
    field_id: int
    value: Optional[str] = None

class CustomFieldValueResponse(CustomFieldValueCreate):
    id: int
    field: CustomFieldResponse
    
    model_config = ConfigDict(from_attributes=True)

# Attachment schemas
class AttachmentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    uploaded_by: Optional[str] = None
    is_image: bool = False
    is_public: bool = True
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AttachmentCreate(BaseModel):
    uploaded_by: Optional[str] = None
    is_public: bool = True

# Base ticket schemas
class TicketBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=3)
    priority: PriorityEnum = PriorityEnum.NORMAL
    status: StatusEnum = StatusEnum.NEW
    ticket_type: TicketTypeEnum = TicketTypeEnum.INCIDENT
    customer: str = Field(..., min_length=3, max_length=200)
    agent: Optional[str] = Field(None, max_length=200)
    agent_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    due_date: Optional[datetime] = None

class TicketCreate(TicketBase):
    tag_ids: Optional[List[int]] = []
    custom_field_values: Optional[List[CustomFieldValueCreate]] = []

class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, min_length=3)
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    ticket_type: Optional[TicketTypeEnum] = None
    customer: Optional[str] = Field(None, min_length=3, max_length=200)
    agent: Optional[str] = Field(None, max_length=200)
    agent_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    due_date: Optional[datetime] = None
    tag_ids: Optional[List[int]] = None
    custom_field_values: Optional[List[CustomFieldValueCreate]] = None

class TicketResponse(TicketBase):
    id: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tags: List[TagResponse] = []
    custom_field_values: List[CustomFieldValueResponse] = []
    attachments: List[AttachmentResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# Legacy schemas for backward compatibility
class TicketSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=3, max_length=500)
    status: str = Field(..., min_length=3, max_length=50)
    customer: str = Field(..., min_length=3, max_length=100)
    agent: str = Field(..., min_length=3, max_length=100)
    agent_notes: str = Field(..., min_length=1, max_length=1000)

class TicketDB(TicketSchema):
    id: int

# Statistics schemas
class TicketStats(BaseModel):
    total: int
    by_status: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    by_type: Dict[str, int] = {}

# Zendesk-style schemas
class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    count: int
    next_page: Optional[str] = None
    previous_page: Optional[str] = None

class TicketSearch(BaseModel):
    query: Optional[str] = None
    status: Optional[List[StatusEnum]] = None
    priority: Optional[List[PriorityEnum]] = None
    ticket_type: Optional[List[TicketTypeEnum]] = None
    customer: Optional[str] = None
    agent: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    tag_ids: Optional[List[int]] = None

class BulkUpdateRequest(BaseModel):
    ticket_ids: List[int] = Field(..., min_items=1, max_items=100)
    updates: TicketUpdate

class BulkUpdateResponse(BaseModel):
    updated_tickets: List[int]
    failed_tickets: List[Dict[str, Any]] = []
    success_count: int
    error_count: int

class TicketTransition(BaseModel):
    from_status: StatusEnum
    to_status: StatusEnum
    comment: Optional[str] = None
    
class TicketComment(BaseModel):
    content: str = Field(..., min_length=1)
    is_public: bool = True
    author: Optional[str] = None

class TicketCommentResponse(TicketComment):
    id: int
    ticket_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
