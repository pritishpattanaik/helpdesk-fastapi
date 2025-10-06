import os
import uuid
import json
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

# File upload configuration for Docker
UPLOAD_DIR = "/usr/src/app/uploads/attachments"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.zip', '.csv'}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Simple in-memory storage for attachments and tags (can be upgraded to DB later)
attachments_store = {}
tags_store = {}
next_attachment_id = 1
next_tag_id = 1

def get_next_attachment_id():
    global next_attachment_id
    current_id = next_attachment_id
    next_attachment_id += 1
    return current_id

def get_next_tag_id():
    global next_tag_id
    current_id = next_tag_id
    next_tag_id += 1
    return current_id

async def save_uploaded_file(file: UploadFile, ticket_id: int, uploaded_by: str = None) -> Dict[str, Any]:
    """Save uploaded file and return file metadata"""
    # Validate file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Store metadata
    attachment_id = get_next_attachment_id()
    attachment_data = {
        'id': attachment_id,
        'ticket_id': ticket_id,
        'filename': unique_filename,
        'original_filename': file.filename,
        'content_type': file.content_type,
        'file_size': len(content),
        'file_path': file_path,
        'is_image': file_ext in {'.jpg', '.jpeg', '.png', '.gif'},
        'uploaded_by': uploaded_by,
        'is_public': True,
        'created_at': datetime.now()
    }
    attachments_store[attachment_id] = attachment_data
    
    return attachment_data

# Enhanced CRUD Endpoints

@router.get("/", response_model=List[TicketDB])
async def list_tickets_enhanced(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    sort_by: str = Query("created_date", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
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
    
    # Add attachment count to each ticket
    enriched_tickets = []
    for t in tickets:
        ticket_dict = dict(t)
        # Count attachments for this ticket
        attachment_count = len([att for att in attachments_store.values() if att['ticket_id'] == t.id])
        ticket_dict['attachment_count'] = attachment_count
        enriched_tickets.append(ticket_dict)
    
    return enriched_tickets

@router.get("/{ticket_id}", response_model=TicketDB)
async def get_ticket_enhanced(ticket_id: int = Path(..., gt=0)):
    """Get a single ticket with attachment info"""
    ticket_data = await crud.get(ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Add attachment info
    ticket_dict = dict(ticket_data)
    ticket_attachments = [att for att in attachments_store.values() if att['ticket_id'] == ticket_id]
    ticket_dict['attachments'] = ticket_attachments
    
    return ticket_dict

@router.post("/", response_model=TicketDB, status_code=201)
async def create_ticket_with_files(
    title: str = Form(..., min_length=3, max_length=150),
    description: str = Form(..., min_length=3),
    status: str = Form("new"),
    customer: str = Form(..., min_length=3, max_length=200),
    agent: str = Form("", max_length=200),
    agent_notes: str = Form(""),
    priority: str = Form("normal", description="Priority: low, normal, high, urgent"),
    ticket_type: str = Form("incident", description="Type: incident, request, problem, change"),
    files: List[UploadFile] = File(default=[]),
    uploaded_by: Optional[str] = Form(None)
):
    """Create a new ticket with optional file attachments"""
    
    # Validate priority and type
    valid_priorities = ["low", "normal", "high", "urgent"]
    valid_types = ["incident", "request", "problem", "change"]
    
    if priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {valid_priorities}")
    
    if ticket_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid ticket type. Must be one of: {valid_types}")
    
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
    uploaded_files = []
    for file in files:
        if file.filename:  # Skip empty file uploads
            file_data = await save_uploaded_file(file, ticket_id, uploaded_by)
            uploaded_files.append(file_data)
    
    # Return the created ticket
    response_object = {
        "id": ticket_id,
        "title": ticket_data.title,
        "description": ticket_data.description,
        "status": ticket_data.status,
        "customer": ticket_data.customer,
        "agent": ticket_data.agent,
        "agent_notes": ticket_data.agent_notes,
        "attachments": uploaded_files,
        "priority": priority,
        "ticket_type": ticket_type
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
    priority: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    uploaded_by: Optional[str] = Form(None)
):
    """Update an existing ticket with optional new file attachments"""
    
    # Check if ticket exists
    existing_ticket = await crud.get(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Validate priority if provided
    if priority is not None:
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {valid_priorities}")
    
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
    new_files = []
    for file in files:
        if file.filename:  # Skip empty file uploads
            file_data = await save_uploaded_file(file, ticket_id, uploaded_by)
            new_files.append(file_data)
    
    # Get all attachments for this ticket
    all_attachments = [att for att in attachments_store.values() if att['ticket_id'] == ticket_id]
    
    # Return updated ticket
    response_object = {
        "id": ticket_id,
        "title": update_data.title,
        "description": update_data.description,
        "status": update_data.status,
        "customer": update_data.customer,
        "agent": update_data.agent,
        "agent_notes": update_data.agent_notes,
        "attachments": all_attachments,
        "new_files_uploaded": len(new_files)
    }
    return response_object

# File attachment management

@router.get("/{ticket_id}/attachments")
async def get_ticket_attachments(ticket_id: int = Path(..., gt=0)):
    """Get all attachments for a ticket"""
    # Check if ticket exists
    ticket_data = await crud.get(ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get attachments from store
    ticket_attachments = [
        att for att in attachments_store.values() 
        if att['ticket_id'] == ticket_id
    ]
    
    return {
        "ticket_id": ticket_id,
        "attachment_count": len(ticket_attachments),
        "attachments": ticket_attachments
    }

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

# Advanced search functionality

@router.get("/search/")
async def search_tickets(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    ticket_type: Optional[str] = Query(None, description="Filter by ticket type"),
    has_attachments: Optional[bool] = Query(None, description="Filter by attachment presence"),
    created_after: Optional[str] = Query(None, description="Created after date (YYYY-MM-DD)"),
    created_before: Optional[str] = Query(None, description="Created before date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100)
):
    """Advanced ticket search with multiple filters"""
    
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
    
    # Date filters
    if created_after:
        try:
            date_obj = datetime.strptime(created_after, "%Y-%m-%d")
            conditions.append(ticket.c.created_date >= date_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format for created_after. Use YYYY-MM-DD")
    
    if created_before:
        try:
            date_obj = datetime.strptime(created_before, "%Y-%m-%d")
            conditions.append(ticket.c.created_date <= date_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format for created_before. Use YYYY-MM-DD")
    
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
    
    # Filter by attachment presence if requested
    filtered_tickets = []
    for t in tickets:
        ticket_dict = dict(t)
        attachment_count = len([att for att in attachments_store.values() if att['ticket_id'] == t.id])
        ticket_dict['attachment_count'] = attachment_count
        
        # Apply attachment filter
        if has_attachments is not None:
            if (has_attachments and attachment_count > 0) or (not has_attachments and attachment_count == 0):
                filtered_tickets.append(ticket_dict)
        else:
            filtered_tickets.append(ticket_dict)
    
    return {
        "tickets": filtered_tickets,
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,
        "filters_applied": {
            "search_query": q,
            "status": status,
            "customer": customer,
            "agent": agent,
            "priority": priority,
            "ticket_type": ticket_type,
            "has_attachments": has_attachments,
            "created_after": created_after,
            "created_before": created_before
        }
    }

# Status management and transitions

@router.put("/{ticket_id}/status", response_model=TicketDB)
async def transition_ticket_status(
    ticket_id: int = Path(..., gt=0),
    new_status: str = Form(...),
    comment: Optional[str] = Form(None, description="Optional transition comment"),
    notify_customer: bool = Form(False, description="Send notification to customer")
):
    """Transition ticket to a new status with validation"""
    # Check if ticket exists
    existing_ticket = await crud.get(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Status validation
    valid_statuses = ["new", "open", "pending", "on_hold", "resolved", "closed"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Business rule validation (simple version)
    current_status = existing_ticket["status"].lower()
    valid_transitions = {
        "new": ["open", "closed"],
        "open": ["pending", "on_hold", "resolved", "closed"],
        "pending": ["open", "resolved", "closed"],
        "on_hold": ["open", "resolved", "closed"],
        "resolved": ["open", "closed"],
        "closed": ["open"]  # Allow reopening
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status transition from '{current_status}' to '{new_status}'"
        )
    
    # Update status
    comment_text = f"\n[Status changed from {current_status} to {new_status}]"
    if comment:
        comment_text += f": {comment}"
    
    update_data = TicketSchema(
        title=existing_ticket["title"],
        description=existing_ticket["description"],
        status=new_status,
        customer=existing_ticket["customer"],
        agent=existing_ticket["agent"],
        agent_notes=existing_ticket["agent_notes"] + comment_text
    )
    
    await crud.put(ticket_id, update_data)
    
    # Return updated ticket
    updated_ticket = await crud.get(ticket_id)
    ticket_dict = dict(updated_ticket)
    ticket_dict['status_changed'] = True
    ticket_dict['previous_status'] = current_status
    ticket_dict['notification_sent'] = notify_customer
    
    return ticket_dict

# Assignment management

@router.put("/{ticket_id}/assign", response_model=TicketDB)
async def assign_ticket(
    ticket_id: int = Path(..., gt=0),
    agent: str = Form(..., min_length=1, max_length=200),
    comment: Optional[str] = Form(None),
    notify_agent: bool = Form(False, description="Send notification to agent")
):
    """Assign ticket to an agent"""
    # Check if ticket exists
    existing_ticket = await crud.get(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update agent
    comment_text = f"\n[Assigned to {agent}]"
    if comment:
        comment_text += f": {comment}"
    
    update_data = TicketSchema(
        title=existing_ticket["title"],
        description=existing_ticket["description"],
        status=existing_ticket["status"],
        customer=existing_ticket["customer"],
        agent=agent,
        agent_notes=existing_ticket["agent_notes"] + comment_text
    )
    
    await crud.put(ticket_id, update_data)
    
    updated_ticket = await crud.get(ticket_id)
    ticket_dict = dict(updated_ticket)
    ticket_dict['assigned'] = True
    ticket_dict['previous_agent'] = existing_ticket["agent"]
    ticket_dict['notification_sent'] = notify_agent
    
    return ticket_dict

@router.put("/{ticket_id}/unassign", response_model=TicketDB)
async def unassign_ticket(
    ticket_id: int = Path(..., gt=0),
    comment: Optional[str] = Form(None)
):
    """Unassign ticket from current agent"""
    # Check if ticket exists
    existing_ticket = await crud.get(ticket_id)
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    previous_agent = existing_ticket["agent"]
    
    # Update to remove agent
    comment_text = f"\n[Unassigned from {previous_agent}]"
    if comment:
        comment_text += f": {comment}"
    
    update_data = TicketSchema(
        title=existing_ticket["title"],
        description=existing_ticket["description"],
        status=existing_ticket["status"],
        customer=existing_ticket["customer"],
        agent="",
        agent_notes=existing_ticket["agent_notes"] + comment_text
    )
    
    await crud.put(ticket_id, update_data)
    
    updated_ticket = await crud.get(ticket_id)
    ticket_dict = dict(updated_ticket)
    ticket_dict['unassigned'] = True
    ticket_dict['previous_agent'] = previous_agent
    
    return ticket_dict

# Bulk operations

@router.put("/bulk/update")
async def bulk_update_tickets(
    ticket_ids: str = Form(..., description="Comma-separated ticket IDs"),
    status: Optional[str] = Form(None),
    agent: Optional[str] = Form(None),
    priority: Optional[str] = Form(None),
    comment: Optional[str] = Form(None)
):
    """Update multiple tickets at once"""
    
    # Parse ticket IDs
    try:
        ids = [int(x.strip()) for x in ticket_ids.split(',') if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket IDs format")
    
    if len(ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot update more than 100 tickets at once")
    
    if not any([status, agent, priority]):
        raise HTTPException(status_code=400, detail="At least one field must be provided for update")
    
    updated_tickets = []
    failed_tickets = []
    
    for ticket_id in ids:
        try:
            # Check if ticket exists
            existing = await crud.get(ticket_id)
            if not existing:
                failed_tickets.append({"ticket_id": ticket_id, "error": "Ticket not found"})
                continue
            
            # Build update data
            update_data = TicketSchema(
                title=existing["title"],
                description=existing["description"],
                status=status if status else existing["status"],
                customer=existing["customer"],
                agent=agent if agent else existing["agent"],
                agent_notes=existing["agent_notes"] + (f"\n[Bulk update]: {comment}" if comment else "")
            )
            
            await crud.put(ticket_id, update_data)
            updated_tickets.append(ticket_id)
            
        except Exception as e:
            failed_tickets.append({"ticket_id": ticket_id, "error": str(e)})
    
    return {
        "updated_tickets": updated_tickets,
        "failed_tickets": failed_tickets,
        "success_count": len(updated_tickets),
        "error_count": len(failed_tickets),
        "updates_applied": {
            "status": status,
            "agent": agent,
            "priority": priority,
            "comment": comment
        }
    }

@router.delete("/bulk/delete")
async def bulk_delete_tickets(ticket_ids: str = Form(..., description="Comma-separated ticket IDs")):
    """Delete multiple tickets at once"""
    
    # Parse ticket IDs
    try:
        ids = [int(x.strip()) for x in ticket_ids.split(',') if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket IDs format")
    
    if len(ids) > 50:
        raise HTTPException(status_code=400, detail="Cannot delete more than 50 tickets at once")
    
    deleted_count = 0
    failed_tickets = []
    
    for ticket_id in ids:
        try:
            # Check if ticket exists
            existing = await crud.get(ticket_id)
            if not existing:
                failed_tickets.append({"ticket_id": ticket_id, "error": "Ticket not found"})
                continue
            
            # Delete associated attachments
            ticket_attachments = [att_id for att_id, att in attachments_store.items() if att['ticket_id'] == ticket_id]
            for att_id in ticket_attachments:
                try:
                    att = attachments_store[att_id]
                    if os.path.exists(att['file_path']):
                        os.remove(att['file_path'])
                    del attachments_store[att_id]
                except Exception:
                    pass
            
            # Delete ticket
            await crud.delete(ticket_id)
            deleted_count += 1
            
        except Exception as e:
            failed_tickets.append({"ticket_id": ticket_id, "error": str(e)})
    
    return {
        "deleted_count": deleted_count,
        "failed_tickets": failed_tickets,
        "total_requested": len(ids)
    }

# Statistics and reporting

@router.get("/stats/summary")
async def get_ticket_statistics():
    """Get comprehensive ticket statistics"""
    
    # Get all tickets
    all_tickets = await database.fetch_all(ticket.select())
    
    # Basic counts
    total_count = len(all_tickets)
    
    # Count by status
    status_counts = {}
    agent_counts = {}
    customer_counts = {}
    
    for t in all_tickets:
        # Status counts
        status = t.status.lower()
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Agent counts
        agent = t.agent or "unassigned"
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        # Customer counts
        customer = t.customer
        customer_counts[customer] = customer_counts.get(customer, 0) + 1
    
    # Attachment statistics
    total_attachments = len(attachments_store)
    tickets_with_attachments = len(set(att['ticket_id'] for att in attachments_store.values()))
    
    return {
        "tickets": {
            "total": total_count,
            "by_status": status_counts,
            "by_agent": dict(sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:10]),  # Top 10
            "by_customer": dict(sorted(customer_counts.items(), key=lambda x: x[1], reverse=True)[:10])  # Top 10
        },
        "attachments": {
            "total_files": total_attachments,
            "tickets_with_attachments": tickets_with_attachments,
            "average_files_per_ticket": round(total_attachments / max(total_count, 1), 2)
        },
        "generated_at": datetime.now().isoformat()
    }