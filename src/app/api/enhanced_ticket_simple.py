import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Path
from fastapi.responses import FileResponse

# Try to import aiofiles, use regular file operations if not available
try:
    import aiofiles
    ASYNC_FILES = True
except ImportError:
    ASYNC_FILES = False
    print("aiofiles not available, using synchronous file operations")

# Import existing CRUD and models
from app.api import crud
from app.api.models import TicketSchema, TicketDB
from app.db import ticket, database
from sqlalchemy import func, and_, or_, desc, asc

router = APIRouter()

# File upload configuration for Docker
UPLOAD_DIR = "/usr/src/app/uploads/attachments"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.zip'}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Simple attachment storage (in-memory for now, can be moved to DB later)
attachments_store = {}

async def save_uploaded_file(file: UploadFile, ticket_id: int) -> Dict[str, Any]:
    """Save uploaded file and return file metadata"""
    # Validate file
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    content = await file.read()
    if ASYNC_FILES:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    else:
        # Fallback to synchronous file operations
        with open(file_path, 'wb') as f:
            f.write(content)
    
    # Store metadata (simple in-memory storage for now)
    attachment_id = len(attachments_store) + 1
    attachment_data = {
        'id': attachment_id,
        'ticket_id': ticket_id,
        'filename': unique_filename,
        'original_filename': file.filename,
        'content_type': file.content_type,
        'file_size': len(content),
        'file_path': file_path,
        'is_image': file_ext in {'.jpg', '.jpeg', '.png', '.gif'},
        'created_at': datetime.now()
    }
    attachments_store[attachment_id] = attachment_data
    
    return attachment_data

# Enhanced CRUD Endpoints (working with existing DB structure)

@router.get("/", response_model=List[TicketDB])
async def list_tickets_enhanced(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    sort_by: str = Query("created_date", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List tickets with pagination and filtering"""
    
    # Build WHERE conditions
    conditions = []
    
    if status:
        conditions.append(ticket.c.status.ilike(f"%{status}%"))
    
    if customer:
        conditions.append(ticket.c.customer.ilike(f"%{customer}%"))
    
    if agent:
        conditions.append(ticket.c.agent.ilike(f"%{agent}%"))
    
    # Build WHERE clause
    where_clause = and_(*conditions) if conditions else None
    
    # Build main query with pagination and sorting
    order_column = getattr(ticket.c, sort_by, ticket.c.created_date)
    order_func = desc if sort_order == "desc" else asc
    
    offset = (page - 1) * per_page
    
    query = ticket.select()
    if where_clause is not None:
        query = query.where(where_clause)
    
    query = query.order_by(order_func(order_column)).offset(offset).limit(per_page)
    
    tickets = await database.fetch_all(query)
    return tickets

@router.get("/{ticket_id}", response_model=TicketDB)
async def get_ticket_enhanced(ticket_id: int = Path(..., gt=0)):
    """Get a single ticket"""
    ticket_data = await crud.get(ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_data

@router.post("/", response_model=TicketDB, status_code=201)
async def create_ticket_with_files(
    title: str = Form(..., min_length=3, max_length=150),
    description: str = Form(..., min_length=3),
    status: str = Form("new"),
    customer: str = Form(..., min_length=3, max_length=200),
    agent: str = Form("", max_length=200),
    agent_notes: str = Form(""),
    files: List[UploadFile] = File(default=[])
):
    """Create a new ticket with optional file attachments"""
    
    # Create ticket using existing schema
    ticket_data = TicketSchema(
        title=title,
        description=description,
        status=status,
        customer=customer,
        agent=agent or "",
        agent_notes=agent_notes or ""
    )
    
    # Create ticket using existing CRUD
    ticket_id = await crud.post(ticket_data)
    
    # Process file uploads
    for file in files:
        if file.filename:  # Skip empty file uploads
            await save_uploaded_file(file, ticket_id)
    
    # Return the created ticket
    response_object = {
        "id": ticket_id,
        "title": ticket_data.title,
        "description": ticket_data.description,
        "status": ticket_data.status,
        "customer": ticket_data.customer,
        "agent": ticket_data.agent,
        "agent_notes": ticket_data.agent_notes,
    }
    return response_object

@router.put("/{ticket_id}", response_model=TicketDB)
async def update_ticket_with_files(
    ticket_id: int = Path(..., gt=0),
    title: Optional[str] = Form(None, min_length=3, max_length=150),
    description: Optional[str] = Form(None, min_length=3),
    status: Optional[str] = Form(None),
    customer: Optional[str] = Form(None, min_length=3, max_length=200),
    agent: Optional[str] = Form(None, max_length=200),
    agent_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[])
):
    """Update an existing ticket with optional new file attachments"""
    
    # Check if ticket exists
    existing_ticket = await crud.get(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Create update data using existing values as defaults
    update_data = TicketSchema(
        title=title if title is not None else existing_ticket["title"],
        description=description if description is not None else existing_ticket["description"],
        status=status if status is not None else existing_ticket["status"],
        customer=customer if customer is not None else existing_ticket["customer"],
        agent=agent if agent is not None else existing_ticket["agent"],
        agent_notes=agent_notes if agent_notes is not None else existing_ticket["agent_notes"]
    )
    
    # Update ticket using existing CRUD
    await crud.put(ticket_id, update_data)
    
    # Process new file uploads
    for file in files:
        if file.filename:  # Skip empty file uploads
            await save_uploaded_file(file, ticket_id)
    
    # Return updated ticket
    response_object = {
        "id": ticket_id,
        "title": update_data.title,
        "description": update_data.description,
        "status": update_data.status,
        "customer": update_data.customer,
        "agent": update_data.agent,
        "agent_notes": update_data.agent_notes,
    }
    return response_object

# File attachment endpoints

@router.get("/{ticket_id}/attachments")
async def get_ticket_attachments(ticket_id: int = Path(..., gt=0)):
    """Get all attachments for a ticket"""
    # Check if ticket exists
    ticket_data = await crud.get(ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get attachments from in-memory store
    ticket_attachments = [
        att for att in attachments_store.values() 
        if att['ticket_id'] == ticket_id
    ]
    
    return ticket_attachments

@router.get("/{ticket_id}/attachments/{attachment_id}/download")
async def download_attachment(
    ticket_id: int = Path(..., gt=0),
    attachment_id: int = Path(..., gt=0)
):
    """Download a specific attachment"""
    # Check if ticket exists
    ticket_data = await crud.get(ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get attachment
    attachment = attachments_store.get(attachment_id)
    if not attachment or attachment['ticket_id'] != ticket_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    if not os.path.exists(attachment['file_path']):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=attachment['file_path'],
        filename=attachment['original_filename'],
        media_type=attachment['content_type']
    )

@router.delete("/{ticket_id}/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    ticket_id: int = Path(..., gt=0),
    attachment_id: int = Path(..., gt=0)
):
    """Delete a specific attachment"""
    # Check if ticket exists
    ticket_data = await crud.get(ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get attachment
    attachment = attachments_store.get(attachment_id)
    if not attachment or attachment['ticket_id'] != ticket_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Delete file from disk
    try:
        if os.path.exists(attachment['file_path']):
            os.remove(attachment['file_path'])
    except Exception:
        pass  # Continue even if file deletion fails
    
    # Remove from store
    del attachments_store[attachment_id]

# Search functionality (working with existing structure)

@router.get("/search/")
async def search_tickets(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100)
):
    """Search tickets with text query and filters"""
    
    conditions = []
    
    # Text search in title, description, and notes
    if q:
        text_search = f"%{q}%"
        conditions.append(
            or_(
                ticket.c.title.ilike(text_search),
                ticket.c.description.ilike(text_search),
                ticket.c.agent_notes.ilike(text_search)
            )
        )
    
    # Status filter
    if status:
        conditions.append(ticket.c.status.ilike(f"%{status}%"))
    
    # Customer filter
    if customer:
        conditions.append(ticket.c.customer.ilike(f"%{customer}%"))
    
    # Agent filter
    if agent:
        conditions.append(ticket.c.agent.ilike(f"%{agent}%"))
    
    # Build WHERE clause
    where_clause = and_(*conditions) if conditions else None
    
    # Count total
    count_query = ticket.select()
    if where_clause is not None:
        count_query = count_query.where(where_clause)
    total_count = len(await database.fetch_all(count_query))
    
    # Get paginated results
    offset = (page - 1) * per_page
    query = ticket.select()
    if where_clause is not None:
        query = query.where(where_clause)
    
    query = query.order_by(desc(ticket.c.created_date)).offset(offset).limit(per_page)
    
    tickets = await database.fetch_all(query)
    
    return {
        "tickets": tickets,
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page
    }

# Status transition with validation

@router.put("/{ticket_id}/status", response_model=TicketDB)
async def transition_ticket_status(
    ticket_id: int = Path(..., gt=0),
    new_status: str = Form(...),
    comment: Optional[str] = Form(None, description="Optional transition comment")
):
    """Transition ticket to a new status"""
    # Check if ticket exists
    existing_ticket = await crud.get(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Simple status validation
    valid_statuses = ["new", "open", "pending", "resolved", "closed"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Update status using existing CRUD
    update_data = TicketSchema(
        title=existing_ticket["title"],
        description=existing_ticket["description"],
        status=new_status,
        customer=existing_ticket["customer"],
        agent=existing_ticket["agent"],
        agent_notes=existing_ticket["agent_notes"] + (f"\n[Status changed to {new_status}]" + (f": {comment}" if comment else ""))
    )
    
    await crud.put(ticket_id, update_data)
    
    # Return updated ticket
    return await crud.get(ticket_id)

# Assignment endpoints

@router.put("/{ticket_id}/assign", response_model=TicketDB)
async def assign_ticket(
    ticket_id: int = Path(..., gt=0),
    agent: str = Form(..., min_length=1, max_length=200),
    comment: Optional[str] = Form(None)
):
    """Assign ticket to an agent"""
    # Check if ticket exists
    existing_ticket = await crud.get(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update agent using existing CRUD
    update_data = TicketSchema(
        title=existing_ticket["title"],
        description=existing_ticket["description"],
        status=existing_ticket["status"],
        customer=existing_ticket["customer"],
        agent=agent,
        agent_notes=existing_ticket["agent_notes"] + f"\n[Assigned to {agent}]" + (f": {comment}" if comment else "")
    )
    
    await crud.put(ticket_id, update_data)
    
    return await crud.get(ticket_id)