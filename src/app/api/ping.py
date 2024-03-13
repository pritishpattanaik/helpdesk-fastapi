from fastapi import APIRouter

router = APIRouter()


@router.get("/plac")
async def pong():
    # some async operation could happen here
    # example: `notes = await get_all_notes()`
    return {"plac": "Welcome to PlacDesk API backend: node1"}
    
