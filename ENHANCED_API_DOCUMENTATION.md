# 🚀 Enhanced PlacDesk API Documentation

## Overview

PlacDesk has been enhanced with Zendesk-style endpoints, file upload capabilities, and enterprise features while maintaining full backward compatibility.

## 📊 API Structure

### Base URL: `http://localhost:7001`

### Available Endpoint Groups:

1. **🎫 Enhanced Tickets** (`/tickets`) - New feature-rich endpoints
2. **🔖 Tags** (`/tags`) - Tag management
3. **🏗️ Custom Fields** (`/custom-fields`) - Custom field management  
4. **📊 Statistics** (`/ticketcount`) - Ticket statistics
5. **🏥 Health Check** (`/plac`) - API health
6. **🔄 Legacy Tickets** (`/ticket`) - Original endpoints (preserved)

---

## 🎫 Enhanced Tickets API (`/tickets`)

### List Tickets with Advanced Filtering
```http
GET /tickets?page=1&per_page=25&status=open,pending&priority=high&sort_by=created_at&sort_order=desc
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (1-100, default: 25)
- `status` (array): Filter by status(es)
- `priority` (array): Filter by priority(ies)  
- `ticket_type` (array): Filter by type(s)
- `customer` (string): Filter by customer
- `agent` (string): Filter by agent
- `sort_by` (string): Sort field (default: created_at)
- `sort_order` (string): asc/desc (default: desc)

**Response:**
```json
{
  "tickets": [...],
  "count": 150,
  "next_page": "/tickets?page=2",
  "previous_page": null
}
```

### Get Single Ticket with Relations
```http
GET /tickets/{ticket_id}
```

**Response:** Full ticket with attachments, tags, custom fields

### Create Ticket with File Attachments
```http
POST /tickets
Content-Type: multipart/form-data
```

**Form Data:**
- `title` (required): Ticket title
- `description` (required): Ticket description  
- `priority`: low|normal|high|urgent (default: normal)
- `status`: new|open|pending|on_hold|resolved|closed (default: new)
- `ticket_type`: incident|request|problem|change (default: incident)
- `customer` (required): Customer identifier
- `agent`: Assigned agent
- `agent_notes`: Internal notes
- `due_date`: SLA due date (ISO format)
- `tag_ids`: Comma-separated tag IDs
- `files`: File uploads (multiple allowed)
- `uploaded_by`: File uploader identifier

**File Constraints:**
- Max size: 10MB per file
- Allowed types: .jpg, .jpeg, .png, .gif, .pdf, .doc, .docx, .txt, .zip

### Update Ticket with New Attachments
```http
PUT /tickets/{ticket_id}
Content-Type: multipart/form-data
```

**Form Data:** Same as create (all fields optional for updates)

### Delete Ticket
```http
DELETE /tickets/{ticket_id}
```
*Note: Deletes ticket and all associated files*

---

## 📎 Attachment Management

### Get Ticket Attachments
```http
GET /tickets/{ticket_id}/attachments
```

### Download Attachment
```http
GET /tickets/{ticket_id}/attachments/{attachment_id}/download
```

### Delete Attachment
```http
DELETE /tickets/{ticket_id}/attachments/{attachment_id}
```

---

## 🔍 Advanced Search

### Search Tickets
```http
POST /tickets/search?page=1&per_page=25
Content-Type: application/json

{
  "query": "search text",
  "status": ["open", "pending"],
  "priority": ["high", "urgent"],
  "ticket_type": ["incident"],
  "customer": "customer@example.com",
  "agent": "agent1",
  "created_after": "2024-01-01T00:00:00Z",
  "created_before": "2024-12-31T23:59:59Z",
  "tag_ids": [1, 2, 3]
}
```

---

## 🔄 Bulk Operations

### Bulk Update Tickets
```http
PUT /tickets/bulk
Content-Type: application/json

{
  "ticket_ids": [1, 2, 3, 4, 5],
  "updates": {
    "status": "resolved",
    "agent": "agent1",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "updated_tickets": [1, 2, 3, 4],
  "failed_tickets": [{"ticket_id": 5, "error": "Ticket not found"}],
  "success_count": 4,
  "error_count": 1
}
```

### Bulk Delete Tickets
```http
DELETE /tickets/bulk
Content-Type: application/json

[1, 2, 3, 4, 5]
```

---

## 🎯 Status Management

### Transition Ticket Status
```http
PUT /tickets/{ticket_id}/status
Content-Type: multipart/form-data
```

**Form Data:**
- `new_status` (required): Target status
- `comment`: Optional transition comment

**Valid Transitions:**
- `new` → `open`, `closed`
- `open` → `pending`, `on_hold`, `resolved`, `closed`
- `pending` → `open`, `resolved`, `closed`
- `on_hold` → `open`, `resolved`, `closed`
- `resolved` → `open`, `closed`
- `closed` → `open`

### Assign Ticket
```http
PUT /tickets/{ticket_id}/assign
Content-Type: multipart/form-data
```

**Form Data:**
- `agent` (required): Agent identifier
- `comment`: Optional assignment comment

### Unassign Ticket
```http
PUT /tickets/{ticket_id}/unassign
Content-Type: multipart/form-data
```

**Form Data:**
- `comment`: Optional unassignment comment

---

## 🔖 Tags API (`/tags`)

### List Tags
```http
GET /tags?page=1&per_page=50
```

### Get Tag
```http
GET /tags/{tag_id}
```

### Create Tag
```http
POST /tags
Content-Type: application/json

{
  "name": "urgent-bug",
  "color": "#ff0000",
  "description": "Critical bugs requiring immediate attention"
}
```

### Update Tag
```http
PUT /tags/{tag_id}
Content-Type: application/json

{
  "name": "updated-name",
  "color": "#00ff00",
  "description": "Updated description"
}
```

### Delete Tag
```http
DELETE /tags/{tag_id}
```

### Get Tag's Tickets
```http
GET /tags/{tag_id}/tickets
```

---

## 🏗️ Custom Fields API (`/custom-fields`)

### List Custom Fields
```http
GET /custom-fields
```

### Get Custom Field
```http
GET /custom-fields/{field_id}
```

### Create Custom Field
```http
POST /custom-fields
Content-Type: application/json

{
  "name": "Department",
  "field_type": "select",
  "is_required": true,
  "options": "[\"IT\", \"HR\", \"Finance\", \"Marketing\"]"
}
```

**Field Types:**
- `text`: Text input
- `number`: Numeric input
- `date`: Date picker
- `boolean`: Checkbox
- `select`: Dropdown (requires options JSON)

### Update Custom Field
```http
PUT /custom-fields/{field_id}
Content-Type: application/json
```

### Delete Custom Field
```http
DELETE /custom-fields/{field_id}
```
*Note: Cannot delete fields in use by tickets*

---

## 📊 Statistics API

### Get Ticket Statistics
```http
GET /ticketcount
```

**Response:**
```json
{
  "total": 150,
  "new": 25,
  "open": 45,
  "pending": 20,
  "resolved": 35,
  "closed": 25
}
```

---

## 🔄 Legacy Compatibility

All original endpoints are preserved under `/ticket`:

- `GET /ticket/` - List all tickets
- `GET /ticket/{id}/` - Get single ticket  
- `POST /ticket/` - Create ticket (simple)
- `PUT /ticket/{id}/` - Update ticket (simple)
- `DELETE /ticket/{id}/` - Delete ticket

---

## 📝 Data Models

### Ticket Response (Enhanced)
```json
{
  "id": 1,
  "title": "Login Issue",
  "description": "Cannot log into the system",
  "priority": "high",
  "status": "open", 
  "ticket_type": "incident",
  "customer": "user@example.com",
  "agent": "agent1",
  "agent_notes": "Investigating...",
  "resolution_notes": null,
  "due_date": "2024-10-05T17:00:00Z",
  "created_at": "2024-10-01T10:00:00Z",
  "updated_at": "2024-10-01T15:30:00Z",
  "resolved_at": null,
  "closed_at": null,
  "tags": [
    {
      "id": 1,
      "name": "login-issue",
      "color": "#ff9900",
      "description": "Login related problems",
      "created_at": "2024-09-01T00:00:00Z"
    }
  ],
  "attachments": [
    {
      "id": 1,
      "filename": "screenshot.png",
      "original_filename": "error_screenshot.png",
      "content_type": "image/png",
      "file_size": 125840,
      "uploaded_by": "user@example.com",
      "is_image": true,
      "is_public": true,
      "created_at": "2024-10-01T10:05:00Z"
    }
  ],
  "custom_field_values": []
}
```

### Enums

**Priority:** `low`, `normal`, `high`, `urgent`

**Status:** `new`, `open`, `pending`, `on_hold`, `resolved`, `closed`

**Ticket Type:** `incident`, `request`, `problem`, `change`

---

## 🔧 Usage Examples

### Create Ticket with Attachment
```bash
curl -X POST "http://localhost:7001/tickets" \
  -F "title=Login Issue" \
  -F "description=Cannot access the system" \
  -F "priority=high" \
  -F "customer=user@example.com" \
  -F "files=@screenshot.png" \
  -F "uploaded_by=user@example.com"
```

### Search for High Priority Open Tickets
```bash
curl -X POST "http://localhost:7001/tickets/search" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": ["high", "urgent"],
    "status": ["open", "pending"]
  }'
```

### Bulk Update to Resolve Multiple Tickets
```bash
curl -X PUT "http://localhost:7001/tickets/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_ids": [1, 2, 3],
    "updates": {
      "status": "resolved",
      "resolution_notes": "Issue resolved via system update"
    }
  }'
```

---

## 🚀 Getting Started

1. **Start the enhanced API:**
   ```bash
   docker compose up -d
   ```

2. **Run migrations for new features:**
   ```bash
   docker compose run --rm migrate
   ```

3. **Access API documentation:**
   - Swagger UI: `http://localhost:7001/docs`
   - ReDoc: `http://localhost:7001/redoc`

4. **Test with sample requests:**
   ```bash
   # Create a tag
   curl -X POST "http://localhost:7001/tags" \
     -H "Content-Type: application/json" \
     -d '{"name": "bug", "color": "#ff0000"}'
   
   # Create ticket with the tag
   curl -X POST "http://localhost:7001/tickets" \
     -F "title=Sample Bug" \
     -F "description=This is a test bug" \
     -F "priority=high" \
     -F "customer=test@example.com" \
     -F "tag_ids=1"
   ```

---

## 🎯 Key Improvements

- ✅ **File Upload Support** - Attach files to tickets
- ✅ **Enhanced Search** - Advanced filtering and text search
- ✅ **Bulk Operations** - Update/delete multiple tickets
- ✅ **Status Workflows** - Controlled status transitions
- ✅ **Tags & Custom Fields** - Flexible categorization
- ✅ **Zendesk-style API** - Industry-standard patterns
- ✅ **Backward Compatibility** - Original endpoints preserved
- ✅ **Comprehensive Documentation** - Auto-generated OpenAPI docs

Your helpdesk API is now enterprise-ready! 🚀