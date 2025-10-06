from typing import List
from fastapi import APIRouter, HTTPException, Path, Query
from app.api.models import CustomFieldCreate, CustomFieldResponse
from app.db import database
from sqlalchemy import func
import json

router = APIRouter()

@router.get("/", response_model=List[CustomFieldResponse])
async def list_custom_fields():
    """List all custom fields"""
    query = """
        SELECT id, name, field_type, is_required, options, created_at
        FROM custom_fields
        ORDER BY name
    """
    
    fields = await database.fetch_all(query)
    
    return [CustomFieldResponse(
        id=field.id,
        name=field.name,
        field_type=field.field_type,
        is_required=field.is_required,
        options=field.options,
        created_at=field.created_at
    ) for field in fields]

@router.get("/{field_id}", response_model=CustomFieldResponse)
async def get_custom_field(field_id: int = Path(..., gt=0)):
    """Get a specific custom field"""
    query = """
        SELECT id, name, field_type, is_required, options, created_at
        FROM custom_fields 
        WHERE id = :field_id
    """
    field = await database.fetch_one(query, {"field_id": field_id})
    
    if not field:
        raise HTTPException(status_code=404, detail="Custom field not found")
    
    return CustomFieldResponse(
        id=field.id,
        name=field.name,
        field_type=field.field_type,
        is_required=field.is_required,
        options=field.options,
        created_at=field.created_at
    )

@router.post("/", response_model=CustomFieldResponse, status_code=201)
async def create_custom_field(field_data: CustomFieldCreate):
    """Create a new custom field"""
    # Validate field_type
    valid_types = ['text', 'number', 'date', 'boolean', 'select']
    if field_data.field_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid field_type. Must be one of: {valid_types}")
    
    # Validate options for select fields
    if field_data.field_type == 'select':
        if not field_data.options:
            raise HTTPException(status_code=400, detail="Select fields must have options")
        try:
            # Validate that options is valid JSON
            json.loads(field_data.options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Options must be valid JSON")
    
    # Check if field name already exists
    existing_query = "SELECT id FROM custom_fields WHERE name = :name"
    existing = await database.fetch_one(existing_query, {"name": field_data.name})
    
    if existing:
        raise HTTPException(status_code=400, detail="Custom field name already exists")
    
    # Insert new field
    insert_query = """
        INSERT INTO custom_fields (name, field_type, is_required, options, created_at)
        VALUES (:name, :field_type, :is_required, :options, :created_at)
        RETURNING id
    """
    
    field_id = await database.execute(insert_query, {
        "name": field_data.name,
        "field_type": field_data.field_type,
        "is_required": field_data.is_required,
        "options": field_data.options,
        "created_at": func.now()
    })
    
    return await get_custom_field(field_id)

@router.put("/{field_id}", response_model=CustomFieldResponse)
async def update_custom_field(field_id: int = Path(..., gt=0), field_data: CustomFieldCreate = None):
    """Update an existing custom field"""
    # Check if field exists
    existing = await get_custom_field(field_id)
    
    # Validate field_type
    valid_types = ['text', 'number', 'date', 'boolean', 'select']
    if field_data.field_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid field_type. Must be one of: {valid_types}")
    
    # Validate options for select fields
    if field_data.field_type == 'select':
        if not field_data.options:
            raise HTTPException(status_code=400, detail="Select fields must have options")
        try:
            json.loads(field_data.options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Options must be valid JSON")
    
    # Check if new name conflicts with another field
    if field_data.name != existing.name:
        name_check_query = "SELECT id FROM custom_fields WHERE name = :name AND id != :field_id"
        name_conflict = await database.fetch_one(name_check_query, {
            "name": field_data.name,
            "field_id": field_id
        })
        
        if name_conflict:
            raise HTTPException(status_code=400, detail="Custom field name already exists")
    
    # Update field
    update_query = """
        UPDATE custom_fields 
        SET name = :name, field_type = :field_type, is_required = :is_required, options = :options
        WHERE id = :field_id
    """
    
    await database.execute(update_query, {
        "field_id": field_id,
        "name": field_data.name,
        "field_type": field_data.field_type,
        "is_required": field_data.is_required,
        "options": field_data.options
    })
    
    return await get_custom_field(field_id)

@router.delete("/{field_id}", status_code=204)
async def delete_custom_field(field_id: int = Path(..., gt=0)):
    """Delete a custom field"""
    # Check if field exists
    await get_custom_field(field_id)
    
    # Check if field is being used by any tickets
    usage_query = "SELECT COUNT(*) as count FROM custom_field_values WHERE field_id = :field_id"
    usage = await database.fetch_one(usage_query, {"field_id": field_id})
    
    if usage.count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete custom field. It is used by {usage.count} tickets."
        )
    
    # Delete field
    delete_query = "DELETE FROM custom_fields WHERE id = :field_id"
    await database.execute(delete_query, {"field_id": field_id})