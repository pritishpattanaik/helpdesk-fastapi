import os
import uuid
import aiofiles
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Path
from fastapi.responses import FileResponse

# Import existing CRUD and models
from app.api import crud
from app.api.models import TicketSchema, TicketDB
from app.db import ticket, database
from sqlalchemy import func, and_, or_, desc, asc

router = APIRouter()

# File upload configuration
UPLOAD_DIR = "uploads/attachments"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.zip'}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    """Save uploaded file and return file metadata"""
    # Validate file
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Determine if file is an image
    is_image = file_ext in {'.jpg', '.jpeg', '.png', '.gif'}
    
    return {
        'filename': unique_filename,
        'original_filename': file.filename,
        'content_type': file.content_type,
        'file_size': len(content),
        'file_path': file_path,
        'is_image': is_image
    }

# Enhanced CRUD Endpoints (Zendesk-style)

@router.get("/", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    status: Optional[List[StatusEnum]] = Query(None, description="Filter by status"),
    priority: Optional[List[PriorityEnum]] = Query(None, description="Filter by priority"),
    ticket_type: Optional[List[TicketTypeEnum]] = Query(None, description="Filter by ticket type"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List tickets with pagination and filtering (Zendesk-style)"""
    tickets, total_count = await crud.get_tickets_paginated(
        page=page, per_page=per_page, status=status, priority=priority,
        ticket_type=ticket_type, customer=customer, agent=agent,
        sort_by=sort_by, sort_order=sort_order
    )
    
    return TicketListResponse(
        tickets=tickets,
        count=total_count,
        next_page=f"/ticket?page={page + 1}" if len(tickets) == per_page else None,
        previous_page=f"/ticket?page={page - 1}" if page > 1 else None
    )

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int = Path(..., gt=0)):
    """Get a single ticket with all relationships"""
    ticket = await crud.get_ticket_with_relations(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.post("/", response_model=TicketResponse, status_code=201)
async def create_ticket_with_attachments(
    title: str = Form(..., min_length=3, max_length=150),
    description: str = Form(..., min_length=3),
    priority: PriorityEnum = Form(PriorityEnum.NORMAL),
    status: StatusEnum = Form(StatusEnum.NEW),
    ticket_type: TicketTypeEnum = Form(TicketTypeEnum.INCIDENT),
    customer: str = Form(..., min_length=3, max_length=200),
    agent: Optional[str] = Form(None, max_length=200),
    agent_notes: Optional[str] = Form(None),
    due_date: Optional[datetime] = Form(None),
    tag_ids: Optional[str] = Form(None, description="Comma-separated tag IDs"),
    files: List[UploadFile] = File(default=[]),
    uploaded_by: Optional[str] = Form(None)
):
    """Create a new ticket with optional file attachments"""
    
    # Parse tag_ids if provided
    parsed_tag_ids = []
    if tag_ids:
        try:
            parsed_tag_ids = [int(x.strip()) for x in tag_ids.split(',') if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tag_ids format")
    
    # Create ticket data
    ticket_data = TicketCreate(
        title=title,
        description=description,
        priority=priority,
        status=status,
        ticket_type=ticket_type,
        customer=customer,
        agent=agent,
        agent_notes=agent_notes,
        due_date=due_date,
        tag_ids=parsed_tag_ids
    )
    
    # Process file uploads
    attachment_data = []
    for file in files:
        if file.filename:  # Skip empty file uploads
            file_info = await save_uploaded_file(file)
            file_info['uploaded_by'] = uploaded_by
            attachment_data.append(file_info)
    
    # Create ticket with attachments
    ticket = await crud.create_ticket_with_attachments(ticket_data, attachment_data)
    return ticket

@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket_with_attachments(
    ticket_id: int = Path(..., gt=0),
    title: Optional[str] = Form(None, min_length=3, max_length=150),
    description: Optional[str] = Form(None, min_length=3),
    priority: Optional[PriorityEnum] = Form(None),
    status: Optional[StatusEnum] = Form(None),
    ticket_type: Optional[TicketTypeEnum] = Form(None),
    customer: Optional[str] = Form(None, min_length=3, max_length=200),
    agent: Optional[str] = Form(None, max_length=200),
    agent_notes: Optional[str] = Form(None),
    resolution_notes: Optional[str] = Form(None),
    due_date: Optional[datetime] = Form(None),
    tag_ids: Optional[str] = Form(None, description="Comma-separated tag IDs"),
    files: List[UploadFile] = File(default=[]),
    uploaded_by: Optional[str] = Form(None)
):
    """Update an existing ticket with optional new file attachments"""
    
    # Check if ticket exists
    existing_ticket = await crud.get_ticket_with_relations(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Parse tag_ids if provided
    parsed_tag_ids = None
    if tag_ids is not None:
        try:
            parsed_tag_ids = [int(x.strip()) for x in tag_ids.split(',') if x.strip()] if tag_ids else []
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tag_ids format")
    
    # Create update data (only include non-None values)
    update_data = {}
    if title is not None:
        update_data['title'] = title
    if description is not None:
        update_data['description'] = description
    if priority is not None:
        update_data['priority'] = priority
    if status is not None:
        update_data['status'] = status
    if ticket_type is not None:
        update_data['ticket_type'] = ticket_type
    if customer is not None:
        update_data['customer'] = customer
    if agent is not None:
        update_data['agent'] = agent
    if agent_notes is not None:
        update_data['agent_notes'] = agent_notes
    if resolution_notes is not None:
        update_data['resolution_notes'] = resolution_notes
    if due_date is not None:
        update_data['due_date'] = due_date
    if parsed_tag_ids is not None:
        update_data['tag_ids'] = parsed_tag_ids
    
    ticket_update = TicketUpdate(**update_data)
    
    # Process new file uploads
    attachment_data = []
    for file in files:
        if file.filename:  # Skip empty file uploads
            file_info = await save_uploaded_file(file)
            file_info['uploaded_by'] = uploaded_by
            attachment_data.append(file_info)
    
    # Update ticket with new attachments
    ticket = await crud.update_ticket_with_attachments(ticket_id, ticket_update, attachment_data)
    return ticket

@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: int = Path(..., gt=0)):
    """Delete a ticket and all its attachments"""
    ticket = await crud.get_ticket_with_relations(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Delete associated files
    for attachment in ticket.attachments:
        try:
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
        except Exception:
            pass  # Continue even if file deletion fails
    
    await crud.delete_ticket(ticket_id)

# Attachment Management

@router.get("/{ticket_id}/attachments", response_model=List[AttachmentResponse])
async def get_ticket_attachments(ticket_id: int = Path(..., gt=0)):
    """Get all attachments for a ticket"""
    ticket = await crud.get_ticket_with_relations(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.attachments

@router.get("/{ticket_id}/attachments/{attachment_id}/download")
async def download_attachment(
    ticket_id: int = Path(..., gt=0),
    attachment_id: int = Path(..., gt=0)
):
    """Download a specific attachment"""
    attachment = await crud.get_attachment(ticket_id, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_filename,
        media_type=attachment.content_type
    )

@router.delete("/{ticket_id}/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    ticket_id: int = Path(..., gt=0),
    attachment_id: int = Path(..., gt=0)
):
    """Delete a specific attachment"""
    attachment = await crud.get_attachment(ticket_id, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Delete file from disk
    try:
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
    except Exception:
        pass  # Continue even if file deletion fails
    
    await crud.delete_attachment(attachment_id)

# Advanced Search

@router.post("/search", response_model=TicketListResponse)
async def search_tickets(
    search_params: TicketSearch,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100)
):
    """Advanced ticket search with multiple filters"""
    tickets, total_count = await crud.search_tickets(search_params, page, per_page)
    
    return TicketListResponse(
        tickets=tickets,
        count=total_count,
        next_page=f"/ticket/search?page={page + 1}" if len(tickets) == per_page else None,
        previous_page=f"/ticket/search?page={page - 1}" if page > 1 else None
    )

# Bulk Operations

@router.put("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_tickets(bulk_request: BulkUpdateRequest):
    """Update multiple tickets at once"""
    return await crud.bulk_update_tickets(bulk_request)

@router.delete("/bulk", response_model=Dict[str, Any])
async def bulk_delete_tickets(ticket_ids: List[int]):
    """Delete multiple tickets at once"""
    if len(ticket_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 tickets at once")
    
    return await crud.bulk_delete_tickets(ticket_ids)

# Status Transitions

@router.put("/{ticket_id}/status", response_model=TicketResponse)
async def transition_ticket_status(
    ticket_id: int = Path(..., gt=0),
    new_status: StatusEnum = Form(...),
    comment: Optional[str] = Form(None, description="Optional transition comment")
):
    """Transition ticket to a new status with optional comment"""
    ticket = await crud.get_ticket_with_relations(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Validate status transition (implement business rules as needed)
    valid_transitions = {
        StatusEnum.NEW: [StatusEnum.OPEN, StatusEnum.CLOSED],
        StatusEnum.OPEN: [StatusEnum.PENDING, StatusEnum.ON_HOLD, StatusEnum.RESOLVED, StatusEnum.CLOSED],
        StatusEnum.PENDING: [StatusEnum.OPEN, StatusEnum.RESOLVED, StatusEnum.CLOSED],
        StatusEnum.ON_HOLD: [StatusEnum.OPEN, StatusEnum.RESOLVED, StatusEnum.CLOSED],
        StatusEnum.RESOLVED: [StatusEnum.OPEN, StatusEnum.CLOSED],
        StatusEnum.CLOSED: [StatusEnum.OPEN]  # Allow reopening
    }
    
    if new_status not in valid_transitions.get(ticket.status, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status transition from {ticket.status} to {new_status}"
        )
    
    return await crud.transition_ticket_status(ticket_id, new_status, comment)

# Assign/Unassign

@router.put("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: int = Path(..., gt=0),
    agent: str = Form(..., min_length=1, max_length=200),
    comment: Optional[str] = Form(None)
):
    """Assign ticket to an agent"""
    ticket = await crud.get_ticket_with_relations(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return await crud.assign_ticket(ticket_id, agent, comment)

@router.put("/{ticket_id}/unassign", response_model=TicketResponse)
async def unassign_ticket(
    ticket_id: int = Path(..., gt=0),
    comment: Optional[str] = Form(None)
):
    """Unassign ticket from current agent"""
    ticket = await crud.get_ticket_with_relations(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return await crud.assign_ticket(ticket_id, None, comment)

# Legacy endpoints for backward compatibility

@router.get("/{id}/", response_model=TicketDB, include_in_schema=False)
async def read_ticket_legacy(id: int = Path(..., gt=0)):
    """Legacy endpoint for backward compatibility"""
    ticket = await crud.get(id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket

@router.post("/", response_model=TicketDB, status_code=201, include_in_schema=False)
async def create_ticket_legacy(payload: TicketSchema):
    """Legacy endpoint for backward compatibility"""
    ticket_id = await crud.post(payload)
    
    response_object = {
        "id": ticket_id,
        "title": payload.title,
        "description": payload.description,
        "status": payload.status,
        "customer": payload.customer,
        "agent": payload.agent,
        "agent_notes": payload.agent_notes,
    }
    return response_object

@router.put("/{id}/", response_model=TicketDB, include_in_schema=False)
async def update_ticket_legacy(payload: TicketSchema, id: int = Path(..., gt=0)):
    """Legacy endpoint for backward compatibility"""
    ticket = await crud.get(id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket ID not found")
    
    ticket_id = await crud.put(id, payload)
    
    response_object = {
        "id": ticket_id,
        "title": payload.title,
        "description": payload.description,
        "customer": payload.customer,
        "agent": payload.agent,
        "status": payload.status,
        "agent_notes": payload.agent_notes,
    }
    return response_object