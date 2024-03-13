from typing import List

from fastapi.params import Path
from app.api import crud
from app.api.models import TicketDB, TicketSchema
from fastapi import APIRouter, HTTPException

router = APIRouter()


# get single ticket with ticket ID /ticket/ID 
@router.get("/{id}/", response_model=TicketDB)
async def read_ticket(id: int = Path(..., gt=0)):
    ticket = await crud.get(id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket

# get all tickets using /ticket/
@router.get("/", response_model=List[TicketDB])
async def read_all_tickets():
    return await crud.get_all()


# POST /ticket/<ID>
@router.post("/", response_model=TicketDB, status_code=201)
async def create_ticket(payload: TicketSchema):
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


# PUT /ticket/<ID>
@router.put("/{id}/", response_model=TicketDB)
async def update_ticket(payload: TicketSchema, id: int = Path(..., gt=0),):
    ticket = await crud.get(id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket ID not found")
    
    ticket_id = await crud.put(id, payload)

    response_object = {
        "id": ticket_id,
        "title": payload.title,
        "description": payload.description,
        "customer": payload.customer,
        "agent":  payload.agent,
        "status": payload.status,
        "agent_notes": payload.agent_notes,
    }
    return response_object

# DELETE /ticket<ID>
# note - this will be removed in future 
@router.delete("/{id}/", response_model=TicketDB)
async def delete_ticket(id: int = Path(..., gt=0)):
    ticket = await crud.get(id)
    
    if not ticket:
        raise HTTPException(status_code=404, detail="ticet ID not found")

    await crud.delete(id)

    return ticket
