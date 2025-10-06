from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Form, Path
from datetime import datetime

router = APIRouter()

# Simple in-memory tag storage
tags_store = {}
next_tag_id = 1

def get_next_tag_id():
    global next_tag_id
    current_id = next_tag_id
    next_tag_id += 1
    return current_id

@router.get("/")
async def list_tags():
    """List all tags"""
    return {
        "tags": list(tags_store.values()),
        "count": len(tags_store)
    }

@router.get("/{tag_id}")
async def get_tag(tag_id: int = Path(..., gt=0)):
    """Get a specific tag"""
    tag = tags_store.get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.post("/", status_code=201)
async def create_tag(
    name: str = Form(..., min_length=1, max_length=50),
    color: str = Form("#808080", description="Hex color code"),
    description: str = Form("", max_length=255)
):
    """Create a new tag"""
    
    # Check if tag name already exists
    for tag in tags_store.values():
        if tag["name"].lower() == name.lower():
            raise HTTPException(status_code=400, detail="Tag name already exists")
    
    # Validate color format
    if not color.startswith("#") or len(color) != 7:
        raise HTTPException(status_code=400, detail="Color must be in hex format (#RRGGBB)")
    
    # Create tag
    tag_id = get_next_tag_id()
    tag_data = {
        "id": tag_id,
        "name": name,
        "color": color,
        "description": description,
        "created_at": datetime.now().isoformat()
    }
    
    tags_store[tag_id] = tag_data
    return tag_data

@router.put("/{tag_id}")
async def update_tag(
    tag_id: int = Path(..., gt=0),
    name: str = Form(..., min_length=1, max_length=50),
    color: str = Form("#808080"),
    description: str = Form("", max_length=255)
):
    """Update an existing tag"""
    
    if tag_id not in tags_store:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if new name conflicts with another tag
    for tid, tag in tags_store.items():
        if tid != tag_id and tag["name"].lower() == name.lower():
            raise HTTPException(status_code=400, detail="Tag name already exists")
    
    # Validate color format
    if not color.startswith("#") or len(color) != 7:
        raise HTTPException(status_code=400, detail="Color must be in hex format (#RRGGBB)")
    
    # Update tag
    tags_store[tag_id].update({
        "name": name,
        "color": color,
        "description": description,
        "updated_at": datetime.now().isoformat()
    })
    
    return tags_store[tag_id]

@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: int = Path(..., gt=0)):
    """Delete a tag"""
    if tag_id not in tags_store:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    del tags_store[tag_id]