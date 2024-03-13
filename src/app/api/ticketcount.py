from typing import List

from fastapi.params import Path
from app.api import crud
from app.api.models import TicketDB, TicketSchema
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/ticketcount")
async def ticketcount():
    return await crud.t_count()
   


