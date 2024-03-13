from fastapi import FastAPI

from app.api import ping, ticket, ticketcount
from app.db import engine, metadata, database

metadata.create_all(engine)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await  database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# /plac ping router to test the APP API 
app.include_router(ping.router)

#  /ticket router for CRUD operations 
app.include_router(ticket.router, prefix="/ticket", tags=["ticket"])

# / ticketcount router for all stats
app.include_router(ticketcount.router)
