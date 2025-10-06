from fastapi import FastAPI

from app.api import ping, ticket, ticketcount
from app.api import enhanced_tickets_full as enhanced_tickets
from app.api import tags_simple as tags
from app.db import engine, metadata, database
from fastapi.middleware.cors import CORSMiddleware

metadata.create_all(engine)

app = FastAPI(
    title="PlacDesk - Helpdesk API", 
    description="A helpdesk API system with ticket management",
    version="1.1.0"
)


@app.on_event("startup")
async def startup():
    await  database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Health check endpoint
app.include_router(ping.router, tags=["health"])

# Original ticket endpoints
app.include_router(ticket.router, prefix="/ticket", tags=["tickets"])

# Enhanced ticket endpoints (full-featured)
app.include_router(enhanced_tickets.router, prefix="/tickets", tags=["tickets-enhanced"])

# Tag management endpoints
app.include_router(tags.router, prefix="/tags", tags=["tags"])

# Statistics endpoint
app.include_router(ticketcount.router, tags=["statistics"])

#Allow IPs
origins = [
    "http://localhost",
    "http://localhost:8080",
]

#Allow middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
