from app.api.models import TicketSchema
from app.db import ticket, database
from sqlalchemy import func



# SELECT * from tickets where ID = ?
async def get(id: int):
    query = ticket.select().where(id == ticket.c.id)
    return await database.fetch_one(query=query)

# this needs to be updated with ORM 
# kindly avoid using direct SQL statement. 
# SELECT count(id) from tickets
async def t_count():
    query = "SELECT status, COUNT(id) AS total FROM tickets GROUP BY status"
    rows = await database.fetch_all(query=query)
    result = {row['status']: row['total'] for row in rows}
    result['total'] = sum(result.values())
    return result


# SELCT * from tickets # expenssive 
async def get_all():
    query = ticket.select()
    return await database.fetch_all(query=query)

# insert new entry into tickets table
async def post(payload: TicketSchema):
    query = ticket.insert().values(title=payload.title, description=payload.description,\
            status=payload.status, agent=payload.agent, customer=payload.customer, agent_notes=payload.agent_notes)
    return await database.execute(query=query)

# update existing tickets using id column 
async def put(id: int, payload: TicketSchema):
    query = (
        ticket
        .update()
        .where(id == ticket.c.id)
        .values(title=payload.title, description=payload.description, \
        customer=payload.customer, status=payload.status, agent=payload.agent)
        #.values(status=payload.status, agent=payload.agent)
        .returning(ticket.c.id)
    )
    return await database.execute(query=query)

# delete entry from tickets table using ID 
# this will be removed in future 
async def delete(id: int):
    query = ticket.delete().where(id == ticket.c.id)
    return await database.execute(query=query)
