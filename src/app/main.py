from fastapi import FastAPI

from app.api import ping, ticket, ticketcount
from app.db import engine, metadata, database
from fastapi.middleware.cors import CORSMiddleware

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
