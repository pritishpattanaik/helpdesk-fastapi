from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload

from app.api.models import (
    TicketCreate, TicketUpdate, TicketResponse, TicketSearch,
    BulkUpdateRequest, BulkUpdateResponse, StatusEnum, PriorityEnum, TicketTypeEnum,
    AttachmentResponse, TicketSchema
)
from app.models import Ticket, Attachment, Tag, CustomFieldValue, ticket_tags
from app.db import database, ticket

# Enhanced ticket operations

async def get_tickets_paginated(
    page: int = 1,
    per_page: int = 25,
    status: Optional[List[StatusEnum]] = None,
    priority: Optional[List[PriorityEnum]] = None,
    ticket_type: Optional[List[TicketTypeEnum]] = None,
    customer: Optional[str] = None,
    agent: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[TicketResponse], int]:
    """Get paginated tickets with filtering and sorting"""
    
    # Build WHERE conditions
    conditions = []
    
    if status:
        status_values = [s.value for s in status]
        conditions.append(ticket.c.status.in_(status_values))
    
    if priority:
        priority_values = [p.value for p in priority]
        conditions.append(ticket.c.priority.in_(priority_values))
    
    if ticket_type:
        type_values = [t.value for t in ticket_type]
        conditions.append(ticket.c.ticket_type.in_(type_values))
    
    if customer:
        conditions.append(ticket.c.customer.ilike(f"%{customer}%"))
    
    if agent:
        conditions.append(ticket.c.agent.ilike(f"%{agent}%"))
    
    # Build WHERE clause
    where_clause = and_(*conditions) if conditions else None
    
    # Count total records
    count_query = ticket.select().where(where_clause) if where_clause else ticket.select()
    total_count = len(await database.fetch_all(count_query))
    
    # Build main query with pagination and sorting
    order_column = getattr(ticket.c, sort_by, ticket.c.created_at)
    order_func = desc if sort_order == "desc" else asc
    
    offset = (page - 1) * per_page
    
    query = (
        ticket.select()
        .where(where_clause)
        .order_by(order_func(order_column))
        .offset(offset)
        .limit(per_page)
    )
    
    tickets = await database.fetch_all(query)
    
    # Convert to response objects (simplified - in real implementation, you'd include relations)
    ticket_responses = []
    for t in tickets:
        ticket_responses.append(TicketResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            priority=PriorityEnum(t.priority),
            status=StatusEnum(t.status),
            ticket_type=TicketTypeEnum(t.ticket_type),
            customer=t.customer,
            agent=t.agent,
            agent_notes=t.agent_notes or "",
            resolution_notes=t.resolution_notes or "",
            due_date=t.due_date,
            created_at=t.created_at,
            updated_at=t.updated_at,
            resolved_at=t.resolved_at,
            closed_at=t.closed_at,
            tags=[],  # TODO: Load tags
            custom_field_values=[],  # TODO: Load custom fields
            attachments=[]  # TODO: Load attachments
        ))
    
    return ticket_responses, total_count

async def get_ticket_with_relations(ticket_id: int) -> Optional[TicketResponse]:
    """Get a single ticket with all its relationships loaded"""
    # Get ticket
    query = ticket.select().where(ticket.c.id == ticket_id)
    ticket_row = await database.fetch_one(query)
    
    if not ticket_row:
        return None
    
    # Get attachments
    attachments_query = """
        SELECT id, filename, original_filename, content_type, file_size, 
               uploaded_by, is_image, is_public, created_at
        FROM attachments 
        WHERE ticket_id = :ticket_id
        ORDER BY created_at
    """
    attachments = await database.fetch_all(attachments_query, {"ticket_id": ticket_id})
    
    # Convert attachments
    attachment_responses = [
        AttachmentResponse(
            id=att.id,
            filename=att.filename,
            original_filename=att.original_filename,
            content_type=att.content_type,
            file_size=att.file_size,
            uploaded_by=att.uploaded_by,
            is_image=att.is_image,
            is_public=att.is_public,
            created_at=att.created_at
        ) for att in attachments
    ]
    
    # TODO: Load tags and custom fields similarly
    
    return TicketResponse(
        id=ticket_row.id,
        title=ticket_row.title,
        description=ticket_row.description,
        priority=PriorityEnum(ticket_row.priority),
        status=StatusEnum(ticket_row.status),
        ticket_type=TicketTypeEnum(ticket_row.ticket_type),
        customer=ticket_row.customer,
        agent=ticket_row.agent,
        agent_notes=ticket_row.agent_notes or "",
        resolution_notes=ticket_row.resolution_notes or "",
        due_date=ticket_row.due_date,
        created_at=ticket_row.created_at,
        updated_at=ticket_row.updated_at,
        resolved_at=ticket_row.resolved_at,
        closed_at=ticket_row.closed_at,
        tags=[],  # TODO: Load tags
        custom_field_values=[],  # TODO: Load custom fields
        attachments=attachment_responses
    )

async def create_ticket_with_attachments(
    ticket_data: TicketCreate, 
    attachment_data: List[Dict[str, Any]]
) -> TicketResponse:
    """Create a new ticket with attachments"""
    
    # Insert ticket
    insert_query = ticket.insert().values(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority.value,
        status=ticket_data.status.value,
        ticket_type=ticket_data.ticket_type.value,
        customer=ticket_data.customer,
        agent=ticket_data.agent,
        agent_notes=ticket_data.agent_notes,
        resolution_notes=ticket_data.resolution_notes,
        due_date=ticket_data.due_date,
        created_at=func.now(),
        updated_at=func.now()
    )
    
    ticket_id = await database.execute(insert_query)
    
    # Insert attachments if any
    if attachment_data:
        for att_data in attachment_data:
            attachment_query = """
                INSERT INTO attachments 
                (ticket_id, filename, original_filename, content_type, file_size, 
                 file_path, uploaded_by, is_image, is_public, created_at)
                VALUES (:ticket_id, :filename, :original_filename, :content_type, 
                        :file_size, :file_path, :uploaded_by, :is_image, :is_public, :created_at)
            """
            await database.execute(attachment_query, {
                "ticket_id": ticket_id,
                "filename": att_data["filename"],
                "original_filename": att_data["original_filename"],
                "content_type": att_data["content_type"],
                "file_size": att_data["file_size"],
                "file_path": att_data["file_path"],
                "uploaded_by": att_data.get("uploaded_by"),
                "is_image": att_data["is_image"],
                "is_public": att_data.get("is_public", True),
                "created_at": func.now()
            })
    
    # TODO: Handle tags if provided in ticket_data.tag_ids
    
    return await get_ticket_with_relations(ticket_id)

async def update_ticket_with_attachments(
    ticket_id: int,
    ticket_data: TicketUpdate,
    attachment_data: List[Dict[str, Any]]
) -> TicketResponse:
    """Update an existing ticket and add new attachments"""
    
    # Build update values (only include non-None fields)
    update_values = {"updated_at": func.now()}
    
    if ticket_data.title is not None:
        update_values["title"] = ticket_data.title
    if ticket_data.description is not None:
        update_values["description"] = ticket_data.description
    if ticket_data.priority is not None:
        update_values["priority"] = ticket_data.priority.value
    if ticket_data.status is not None:
        update_values["status"] = ticket_data.status.value
        # Set resolved_at or closed_at based on status
        if ticket_data.status == StatusEnum.RESOLVED:
            update_values["resolved_at"] = func.now()
        elif ticket_data.status == StatusEnum.CLOSED:
            update_values["closed_at"] = func.now()
    if ticket_data.ticket_type is not None:
        update_values["ticket_type"] = ticket_data.ticket_type.value
    if ticket_data.customer is not None:
        update_values["customer"] = ticket_data.customer
    if ticket_data.agent is not None:
        update_values["agent"] = ticket_data.agent
    if ticket_data.agent_notes is not None:
        update_values["agent_notes"] = ticket_data.agent_notes
    if ticket_data.resolution_notes is not None:
        update_values["resolution_notes"] = ticket_data.resolution_notes
    if ticket_data.due_date is not None:
        update_values["due_date"] = ticket_data.due_date
    
    # Update ticket
    update_query = ticket.update().where(ticket.c.id == ticket_id).values(**update_values)
    await database.execute(update_query)
    
    # Add new attachments if any
    if attachment_data:
        for att_data in attachment_data:
            attachment_query = """
                INSERT INTO attachments 
                (ticket_id, filename, original_filename, content_type, file_size, 
                 file_path, uploaded_by, is_image, is_public, created_at)
                VALUES (:ticket_id, :filename, :original_filename, :content_type, 
                        :file_size, :file_path, :uploaded_by, :is_image, :is_public, :created_at)
            """
            await database.execute(attachment_query, {
                "ticket_id": ticket_id,
                "filename": att_data["filename"],
                "original_filename": att_data["original_filename"],
                "content_type": att_data["content_type"],
                "file_size": att_data["file_size"],
                "file_path": att_data["file_path"],
                "uploaded_by": att_data.get("uploaded_by"),
                "is_image": att_data["is_image"],
                "is_public": att_data.get("is_public", True),
                "created_at": func.now()
            })
    
    # TODO: Handle tag updates if provided
    
    return await get_ticket_with_relations(ticket_id)

async def delete_ticket(ticket_id: int) -> bool:
    """Delete a ticket and all related data"""
    # Delete ticket (cascading deletes will handle attachments, etc.)
    delete_query = ticket.delete().where(ticket.c.id == ticket_id)
    result = await database.execute(delete_query)
    return result > 0

async def get_attachment(ticket_id: int, attachment_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific attachment"""
    query = """
        SELECT a.id, a.ticket_id, a.filename, a.original_filename, a.content_type,
               a.file_size, a.file_path, a.uploaded_by, a.is_image, a.is_public, a.created_at
        FROM attachments a
        WHERE a.ticket_id = :ticket_id AND a.id = :attachment_id
    """
    return await database.fetch_one(query, {"ticket_id": ticket_id, "attachment_id": attachment_id})

async def delete_attachment(attachment_id: int) -> bool:
    """Delete a specific attachment"""
    query = "DELETE FROM attachments WHERE id = :attachment_id"
    result = await database.execute(query, {"attachment_id": attachment_id})
    return result > 0

async def search_tickets(
    search_params: TicketSearch,
    page: int = 1,
    per_page: int = 25
) -> Tuple[List[TicketResponse], int]:
    """Advanced search functionality"""
    conditions = []
    
    # Text search in title and description
    if search_params.query:
        text_search = f"%{search_params.query}%"
        conditions.append(
            or_(
                ticket.c.title.ilike(text_search),
                ticket.c.description.ilike(text_search),
                ticket.c.agent_notes.ilike(text_search)
            )
        )
    
    # Filter by status
    if search_params.status:
        status_values = [s.value for s in search_params.status]
        conditions.append(ticket.c.status.in_(status_values))
    
    # Filter by priority
    if search_params.priority:
        priority_values = [p.value for p in search_params.priority]
        conditions.append(ticket.c.priority.in_(priority_values))
    
    # Filter by ticket type
    if search_params.ticket_type:
        type_values = [t.value for t in search_params.ticket_type]
        conditions.append(ticket.c.ticket_type.in_(type_values))
    
    # Filter by customer
    if search_params.customer:
        conditions.append(ticket.c.customer.ilike(f"%{search_params.customer}%"))
    
    # Filter by agent
    if search_params.agent:
        conditions.append(ticket.c.agent.ilike(f"%{search_params.agent}%"))
    
    # Date range filters
    if search_params.created_after:
        conditions.append(ticket.c.created_at >= search_params.created_after)
    
    if search_params.created_before:
        conditions.append(ticket.c.created_at <= search_params.created_before)
    
    if search_params.updated_after:
        conditions.append(ticket.c.updated_at >= search_params.updated_after)
    
    if search_params.updated_before:
        conditions.append(ticket.c.updated_at <= search_params.updated_before)
    
    # Build WHERE clause
    where_clause = and_(*conditions) if conditions else None
    
    # Use the existing paginated function with the search conditions
    return await get_tickets_paginated_with_conditions(where_clause, page, per_page)

async def get_tickets_paginated_with_conditions(where_clause, page: int, per_page: int):
    """Helper function for paginated results with custom WHERE clause"""
    # Count total
    count_query = ticket.select().where(where_clause) if where_clause else ticket.select()
    total_count = len(await database.fetch_all(count_query))
    
    # Get paginated results
    offset = (page - 1) * per_page
    query = (
        ticket.select()
        .where(where_clause)
        .order_by(desc(ticket.c.created_at))
        .offset(offset)
        .limit(per_page)
    )
    
    tickets = await database.fetch_all(query)
    
    # Convert to response objects
    ticket_responses = []
    for t in tickets:
        ticket_responses.append(TicketResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            priority=PriorityEnum(t.priority),
            status=StatusEnum(t.status),
            ticket_type=TicketTypeEnum(t.ticket_type),
            customer=t.customer,
            agent=t.agent,
            agent_notes=t.agent_notes or "",
            resolution_notes=t.resolution_notes or "",
            due_date=t.due_date,
            created_at=t.created_at,
            updated_at=t.updated_at,
            resolved_at=t.resolved_at,
            closed_at=t.closed_at,
            tags=[],
            custom_field_values=[],
            attachments=[]
        ))
    
    return ticket_responses, total_count

async def bulk_update_tickets(bulk_request: BulkUpdateRequest) -> BulkUpdateResponse:
    """Update multiple tickets at once"""
    updated_tickets = []
    failed_tickets = []
    
    for ticket_id in bulk_request.ticket_ids:
        try:
            # Check if ticket exists
            existing = await database.fetch_one(
                ticket.select().where(ticket.c.id == ticket_id)
            )
            if not existing:
                failed_tickets.append({
                    "ticket_id": ticket_id,
                    "error": "Ticket not found"
                })
                continue
            
            # Apply updates
            await update_ticket_with_attachments(ticket_id, bulk_request.updates, [])
            updated_tickets.append(ticket_id)
            
        except Exception as e:
            failed_tickets.append({
                "ticket_id": ticket_id,
                "error": str(e)
            })
    
    return BulkUpdateResponse(
        updated_tickets=updated_tickets,
        failed_tickets=failed_tickets,
        success_count=len(updated_tickets),
        error_count=len(failed_tickets)
    )

async def bulk_delete_tickets(ticket_ids: List[int]) -> Dict[str, Any]:
    """Delete multiple tickets at once"""
    deleted_count = 0
    failed_tickets = []
    
    for ticket_id in ticket_ids:
        try:
            success = await delete_ticket(ticket_id)
            if success:
                deleted_count += 1
            else:
                failed_tickets.append({
                    "ticket_id": ticket_id,
                    "error": "Ticket not found"
                })
        except Exception as e:
            failed_tickets.append({
                "ticket_id": ticket_id,
                "error": str(e)
            })
    
    return {
        "deleted_count": deleted_count,
        "failed_tickets": failed_tickets,
        "total_requested": len(ticket_ids)
    }

async def transition_ticket_status(
    ticket_id: int, 
    new_status: StatusEnum, 
    comment: Optional[str] = None
) -> TicketResponse:
    """Transition ticket to new status"""
    update_values = {
        "status": new_status.value,
        "updated_at": func.now()
    }
    
    # Set timestamp based on status
    if new_status == StatusEnum.RESOLVED:
        update_values["resolved_at"] = func.now()
    elif new_status == StatusEnum.CLOSED:
        update_values["closed_at"] = func.now()
    
    # If reopening, clear resolved/closed timestamps
    if new_status == StatusEnum.OPEN:
        update_values["resolved_at"] = None
        update_values["closed_at"] = None
    
    # Update ticket
    update_query = ticket.update().where(ticket.c.id == ticket_id).values(**update_values)
    await database.execute(update_query)
    
    # TODO: Add comment/note if provided
    
    return await get_ticket_with_relations(ticket_id)

async def assign_ticket(
    ticket_id: int, 
    agent: Optional[str], 
    comment: Optional[str] = None
) -> TicketResponse:
    """Assign or unassign ticket to/from agent"""
    update_query = ticket.update().where(ticket.c.id == ticket_id).values(
        agent=agent,
        updated_at=func.now()
    )
    await database.execute(update_query)
    
    # TODO: Add assignment comment if provided
    
    return await get_ticket_with_relations(ticket_id)

# Legacy CRUD functions (keep for backward compatibility)
from app.api.crud import get, get_all, post, put, delete, t_count