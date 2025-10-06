from typing import List
from fastapi import APIRouter, HTTPException, Path, Query
from app.api.models import TagCreate, TagResponse
from app.db import database
from sqlalchemy import func

router = APIRouter()

@router.get("/", response_model=List[TagResponse])
async def list_tags(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    """List all tags with pagination"""
    offset = (page - 1) * per_page
    
    query = """
        SELECT id, name, color, description, created_at
        FROM tags
        ORDER BY name
        LIMIT :limit OFFSET :offset
    """
    
    tags = await database.fetch_all(query, {"limit": per_page, "offset": offset})
    
    return [TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        description=tag.description,
        created_at=tag.created_at
    ) for tag in tags]

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: int = Path(..., gt=0)):
    """Get a specific tag"""
    query = "SELECT id, name, color, description, created_at FROM tags WHERE id = :tag_id"
    tag = await database.fetch_one(query, {"tag_id": tag_id})
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        description=tag.description,
        created_at=tag.created_at
    )

@router.post("/", response_model=TagResponse, status_code=201)
async def create_tag(tag_data: TagCreate):
    """Create a new tag"""
    # Check if tag name already exists
    existing_query = "SELECT id FROM tags WHERE name = :name"
    existing = await database.fetch_one(existing_query, {"name": tag_data.name})
    
    if existing:
        raise HTTPException(status_code=400, detail="Tag name already exists")
    
    # Insert new tag
    insert_query = """
        INSERT INTO tags (name, color, description, created_at)
        VALUES (:name, :color, :description, :created_at)
        RETURNING id
    """
    
    tag_id = await database.execute(insert_query, {
        "name": tag_data.name,
        "color": tag_data.color,
        "description": tag_data.description,
        "created_at": func.now()
    })
    
    return await get_tag(tag_id)

@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: int = Path(..., gt=0), tag_data: TagCreate = None):
    """Update an existing tag"""
    # Check if tag exists
    existing = await get_tag(tag_id)
    
    # Check if new name conflicts with another tag
    if tag_data.name != existing.name:
        name_check_query = "SELECT id FROM tags WHERE name = :name AND id != :tag_id"
        name_conflict = await database.fetch_one(name_check_query, {
            "name": tag_data.name,
            "tag_id": tag_id
        })
        
        if name_conflict:
            raise HTTPException(status_code=400, detail="Tag name already exists")
    
    # Update tag
    update_query = """
        UPDATE tags 
        SET name = :name, color = :color, description = :description
        WHERE id = :tag_id
    """
    
    await database.execute(update_query, {
        "tag_id": tag_id,
        "name": tag_data.name,
        "color": tag_data.color,
        "description": tag_data.description
    })
    
    return await get_tag(tag_id)

@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: int = Path(..., gt=0)):
    """Delete a tag"""
    # Check if tag exists
    await get_tag(tag_id)
    
    # Delete tag (cascade will remove ticket associations)
    delete_query = "DELETE FROM tags WHERE id = :tag_id"
    await database.execute(delete_query, {"tag_id": tag_id})

@router.get("/{tag_id}/tickets")
async def get_tag_tickets(tag_id: int = Path(..., gt=0)):
    """Get all tickets associated with a tag"""
    # Check if tag exists
    await get_tag(tag_id)
    
    query = """
        SELECT t.id, t.title, t.status, t.priority, t.created_at
        FROM tickets t
        JOIN ticket_tags tt ON t.id = tt.ticket_id
        WHERE tt.tag_id = :tag_id
        ORDER BY t.created_at DESC
    """
    
    tickets = await database.fetch_all(query, {"tag_id": tag_id})
    return tickets