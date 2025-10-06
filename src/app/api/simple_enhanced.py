from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path

# Import existing CRUD and models
from app.api import crud
from app.api.models import TicketSchema, TicketDB
from app.db import ticket, database
from sqlalchemy import and_, or_, desc, asc

router = APIRouter()

@router.get("/", response_model=List[TicketDB])
async def list_tickets_enhanced(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
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
    order_func = desc if sort_order == "desc" else asc
    
    offset = (page - 1) * per_page
    
    query = ticket.select()
    if where_clause is not None:
        query = query.where(where_clause)
    
    query = query.order_by(order_func(ticket.c.created_date)).offset(offset).limit(per_page)
    
    tickets = await database.fetch_all(query)
    return tickets

@router.get("/{ticket_id}", response_model=TicketDB)
async def get_ticket_enhanced(ticket_id: int = Path(..., gt=0)):
    """Get a single ticket"""
    ticket_data = await crud.get(ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_data

@router.get("/search/")
async def search_tickets(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
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