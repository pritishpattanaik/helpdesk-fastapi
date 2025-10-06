# Database Migration Guide (Docker Compose)

This guide explains how to migrate your PlacDesk database from the basic schema to the enhanced enterprise schema using Docker Compose.

## What's New in the Enhanced Schema

### 1. **Ticket Priorities**
- `LOW` - Low priority tickets
- `NORMAL` - Normal priority (default)
- `HIGH` - High priority tickets  
- `URGENT` - Urgent tickets requiring immediate attention

### 2. **Enhanced Ticket Statuses**
- `NEW` - Newly created tickets (default)
- `OPEN` - Tickets being actively worked on
- `PENDING` - Waiting for customer response
- `ON_HOLD` - Temporarily paused tickets
- `RESOLVED` - Issues resolved, awaiting verification
- `CLOSED` - Completed and verified tickets

### 3. **Ticket Types**
- `INCIDENT` - Something is broken (default)
- `REQUEST` - Service requests
- `PROBLEM` - Root cause analysis
- `CHANGE` - Change requests

### 4. **Custom Fields**
- Flexible custom field system
- Support for: text, number, date, boolean, select fields
- Required/optional field validation
- Per-ticket custom values

### 5. **Tags/Labels**
- Many-to-many relationship between tickets and tags
- Color-coded tags for visual organization
- Searchable and filterable

### 6. **Enhanced Timestamps**
- `created_at` - Ticket creation time
- `updated_at` - Last modification time
- `resolved_at` - Resolution timestamp
- `closed_at` - Closure timestamp
- `due_date` - SLA due date

## Migration Steps for Docker Compose

### Prerequisites

1. **Backup your database** (IMPORTANT!)
   ```bash
   # Create backup using Docker
   docker compose exec db pg_dump -U placdesk placdesk > backup_before_migration.sql
   ```

2. **Ensure you have the latest code**
   ```bash
   git pull  # if using git
   ```

3. **Stop the web service** (keep database running)
   ```bash
   docker compose stop web
   ```

### Method 1: Automatic Migration (Recommended)

Run the dedicated migration service:

```bash
# Run migration using Docker Compose profile
docker compose --profile migration up migrate

# Or run as one-time service
docker compose run --rm migrate
```

This will:
- Wait for database to be ready
- Check current schema state
- Apply migrations safely
- Preserve existing data

### Method 2: Manual Migration (Advanced)

If you prefer manual control:

1. **Run interactive shell in container**
   ```bash
   docker compose run --rm web bash
   ```

2. **Inside the container, run Alembic commands**
   ```bash
   # Check current state
   alembic current
   
   # For existing databases, stamp baseline first
   alembic stamp 001
   
   # Apply enhancement migration
   alembic upgrade 002
   
   # Verify migration
   alembic current
   alembic history
   ```

3. **Exit container**
   ```bash
   exit
   ```

### Method 3: Direct Database Connection

Connect directly to the database container:

```bash
# Access PostgreSQL directly
docker compose exec db psql -U placdesk -d placdesk

# Check tables
\dt

# View ticket structure
\d tickets

# Exit
\q
```

### After Migration

1. **Start the web service**
   ```bash
   docker compose up -d web
   ```

2. **Verify everything works**
   ```bash
   curl http://localhost:7001/plac
   curl http://localhost:7001/ticketcount
   ```

### Rollback (if needed)

```bash
# Run rollback in container
docker compose run --rm web alembic downgrade 001
```

**⚠️ Warning:** Rollback will lose data from new features (tags, custom fields, etc.)

## Database Schema Changes

### Modified Tables

#### `tickets` table changes:
- Added `priority` enum column (default: NORMAL)
- Modified `status` to use enum instead of string
- Added `ticket_type` enum column (default: INCIDENT)
- Changed `description` from VARCHAR(250) to TEXT
- Added `resolution_notes` TEXT column
- Added `updated_at`, `resolved_at`, `closed_at` timestamps
- Added `due_date` for SLA tracking
- Renamed `created_date` to `created_at`
- Added indexes for better performance

### New Tables

#### `tags` table:
```sql
- id (Primary Key)
- name (Unique, max 50 chars)
- color (Hex color code, default #808080)
- description (Optional, max 255 chars)
- created_at (Timestamp)
```

#### `custom_fields` table:
```sql
- id (Primary Key)
- name (Field name, max 100 chars)
- field_type (text|number|date|boolean|select)
- is_required (Boolean, default false)
- options (JSON string for select field options)
- created_at (Timestamp)
```

#### `custom_field_values` table:
```sql
- id (Primary Key)
- ticket_id (Foreign Key to tickets)
- field_id (Foreign Key to custom_fields)
- value (TEXT, stores the field value)
- Unique constraint on (ticket_id, field_id)
```

#### `ticket_tags` table (association):
```sql
- ticket_id (Foreign Key to tickets)
- tag_id (Foreign Key to tags)
- Unique constraint on (ticket_id, tag_id)
```

## API Model Changes

### New Pydantic Models

- `TicketCreate` - For creating tickets with new features
- `TicketUpdate` - For partial updates
- `TicketResponse` - Full ticket response with relationships
- `TagCreate`, `TagResponse` - Tag management
- `CustomFieldCreate`, `CustomFieldResponse` - Custom field management
- Enum classes: `PriorityEnum`, `StatusEnum`, `TicketTypeEnum`

### Legacy Compatibility

Old `TicketSchema` and `TicketDB` models are preserved for backward compatibility.

## Data Migration Details

### Status Migration Mapping:
- `"new"` → `NEW`
- `"open"` → `OPEN`  
- `"pending"` → `PENDING`
- `"resolved"` → `RESOLVED`
- `"closed"` → `CLOSED`
- Unknown values → `NEW`

### Default Values:
- All existing tickets get `priority = NORMAL`
- All existing tickets get `ticket_type = INCIDENT`
- `updated_at` is set to `created_at` for existing records

## Testing the Migration

After migration, test these endpoints:

1. **Verify existing tickets**:
   ```bash
   curl http://localhost:7001/ticket/
   ```

2. **Create ticket with legacy format** (still supported):
   ```bash
   curl -X POST http://localhost:7001/ticket/ \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Legacy Format Test",
       "description": "Testing backward compatibility",
       "status": "new",
       "customer": "test@example.com",
       "agent": "agent1",
       "agent_notes": "Created via legacy API"
     }'
   ```

3. **Check ticket statistics**:
   ```bash
   curl http://localhost:7001/ticketcount
   ```

4. **Test inside Docker container**:
   ```bash
   # Run tests from inside container
   docker compose exec web curl http://localhost:8010/plac
   docker compose exec web curl http://localhost:8010/ticket/
   ```

## Troubleshooting

### Common Issues:

1. **"relation already exists" error**
   - Database may already have been migrated
   - Check current migration: `docker compose run --rm web alembic current`

2. **Connection refused**
   - Ensure PostgreSQL is running: `docker compose up -d db`
   - Wait for database to be ready (check logs: `docker compose logs db`)
   - Verify network connectivity between containers

3. **Permission denied**
   - Ensure database user has CREATE privileges
   - Check Docker container database permissions
   - Verify volumes are properly mounted

4. **Migration fails midway**
   - Check container logs: `docker compose logs migrate`
   - Restore from backup: `docker compose exec db psql -U placdesk -d placdesk < backup_before_migration.sql`
   - Check migration logs for specific errors

5. **Container build issues**
   - Rebuild containers: `docker compose build --no-cache`
   - Check Dockerfile and requirements.txt

6. **Network issues**
   - Ensure plac-net network exists: `docker network create plac-net`
   - Check network connectivity: `docker compose exec web ping db`

### Getting Help

If migration fails:
1. Restore from backup
2. Check the logs for specific error messages
3. Ensure all prerequisites are met
4. Consider running migrations step by step manually

## Next Steps

After successful migration:
1. Update your API code to use new models
2. Implement tag and custom field management endpoints
3. Add validation for enum values
4. Consider implementing SLA tracking with due_date
5. Update frontend to support new features