import os

from sqlalchemy import (Column, DateTime, Integer, MetaData, String, Table,
                        create_engine)
from sqlalchemy.sql import func

from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy
engine = create_engine(DATABASE_URL)
metadata = MetaData()
ticket = Table(
    "tickets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(150)),
    Column("description", String(250)),
    Column("status", String(100)),
    Column("customer", String(200)),
    Column("agent", String(200)),
    Column("created_date", DateTime, default=func.now(), nullable=False),
    Column("agent_notes", String(1000)),
)

# databases query builder
database = Database(DATABASE_URL)