from pydantic import BaseModel
from pydantic.fields import Field

# status = new|open|resolved|closed|pending
# agent = name of a user who attend your ticket/request 
# customer = name of customer who raised the ticket
# agent_notes = notes put by agent
class TicketSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=3, max_length=500)
    status: str = Field(..., min_length=3, max_length=50)
    customer: str = Field(..., min_length=3, max_length=100)
    agent: str = Field(..., min_length=3, max_length=100)
    agent_notes: str = Field(..., min_length=1, max_length=1000)

class TicketDB(TicketSchema):
    id: int
