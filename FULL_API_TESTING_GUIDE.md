# 🚀 Complete Enhanced PlacDesk API Testing Guide

## 🎯 Full Feature Set Overview

Your PlacDesk API now includes:
- ✅ **File Upload Support** - Attach files to tickets
- ✅ **Advanced Search** - Multi-criteria filtering
- ✅ **Bulk Operations** - Update/delete multiple tickets
- ✅ **Status Management** - Controlled workflows
- ✅ **Assignment System** - Agent management
- ✅ **Tag System** - Categorization and labeling
- ✅ **Statistics & Reporting** - Comprehensive analytics
- ✅ **Backward Compatibility** - Original endpoints preserved

---

## 🐳 Deploy & Test

### 1. Deploy the Enhanced API
```bash
# Stop and rebuild
docker compose down
docker compose up -d --build

# Verify it's running
docker compose ps
curl http://localhost:7001/plac

# Check API documentation
open http://localhost:7001/docs
```

---

## 🎫 Enhanced Ticket Management

### List Tickets with Advanced Filtering
```bash
# Basic listing with pagination
curl "http://localhost:7001/tickets/?page=1&per_page=5"

# Filter by status and customer
curl "http://localhost:7001/tickets/?status=open&customer=test@example.com"

# Sort by different fields
curl "http://localhost:7001/tickets/?sort_by=created_date&sort_order=asc"
```

### Create Tickets with File Attachments
```bash
# Create a test file
echo "This is a test document for ticket attachment" > test_document.txt

# Create ticket with file attachment
curl -X POST http://localhost:7001/tickets/ \
  -F "title=Server Performance Issue" \
  -F "description=Database queries are running slowly" \
  -F "status=new" \
  -F "customer=admin@company.com" \
  -F "agent=john.doe" \
  -F "priority=high" \
  -F "ticket_type=incident" \
  -F "files=@test_document.txt" \
  -F "uploaded_by=admin@company.com"

# Create ticket with multiple files
curl -X POST http://localhost:7001/tickets/ \
  -F "title=UI Bug Report" \
  -F "description=Button layout is broken on mobile" \
  -F "customer=user@example.com" \
  -F "priority=normal" \
  -F "ticket_type=problem" \
  -F "files=@test_document.txt" \
  -F "files=@screenshot.png" \
  -F "uploaded_by=user@example.com"
```

### Update Tickets and Add Files
```bash
# Update ticket and add new attachments (replace {id} with actual ticket ID)
curl -X PUT http://localhost:7001/tickets/1 \
  -F "status=open" \
  -F "agent=jane.smith" \
  -F "agent_notes=Started investigation" \
  -F "priority=urgent" \
  -F "files=@additional_info.txt"
```

---

## 📎 File Attachment Management

### View Ticket Attachments
```bash
# Get all attachments for a ticket
curl http://localhost:7001/tickets/1/attachments
```

### Download Attachments
```bash
# Download specific attachment (replace IDs with actual values)
curl -O http://localhost:7001/tickets/1/attachments/1/download
```

### Delete Attachments
```bash
# Delete specific attachment
curl -X DELETE http://localhost:7001/tickets/1/attachments/1
```

---

## 🔍 Advanced Search & Filtering

### Text Search
```bash
# Search in title, description, and notes
curl "http://localhost:7001/tickets/search/?q=database&page=1&per_page=10"

# Search with multiple filters
curl "http://localhost:7001/tickets/search/?q=performance&status=open&priority=high"

# Search by customer and agent
curl "http://localhost:7001/tickets/search/?customer=admin&agent=john"

# Search with date filters
curl "http://localhost:7001/tickets/search/?created_after=2024-01-01&created_before=2024-12-31"

# Filter by attachment presence
curl "http://localhost:7001/tickets/search/?has_attachments=true"
```

---

## 🎯 Status Management & Workflows

### Change Ticket Status
```bash
# Transition ticket status with comment
curl -X PUT http://localhost:7001/tickets/1/status \
  -F "new_status=open" \
  -F "comment=Started working on this issue" \
  -F "notify_customer=true"

# Resolve ticket
curl -X PUT http://localhost:7001/tickets/1/status \
  -F "new_status=resolved" \
  -F "comment=Fixed database performance issues"

# Close ticket
curl -X PUT http://localhost:7001/tickets/1/status \
  -F "new_status=closed" \
  -F "comment=Customer confirmed resolution"
```

### Assignment Management
```bash
# Assign ticket to agent
curl -X PUT http://localhost:7001/tickets/1/assign \
  -F "agent=john.doe@company.com" \
  -F "comment=Assigning to database specialist" \
  -F "notify_agent=true"

# Unassign ticket
curl -X PUT http://localhost:7001/tickets/1/unassign \
  -F "comment=Reassigning to different team"
```

---

## 🏷️ Tag Management System

### Create Tags
```bash
# Create priority tag
curl -X POST http://localhost:7001/tags/ \
  -F "name=critical-bug" \
  -F "color=#ff0000" \
  -F "description=Critical bugs requiring immediate attention"

# Create category tag
curl -X POST http://localhost:7001/tags/ \
  -F "name=database" \
  -F "color=#0066cc" \
  -F "description=Database related issues"

# Create customer tag
curl -X POST http://localhost:7001/tags/ \
  -F "name=vip-customer" \
  -F "color=#ffd700" \
  -F "description=VIP customer tickets"
```

### Manage Tags
```bash
# List all tags
curl http://localhost:7001/tags/

# Get specific tag
curl http://localhost:7001/tags/1

# Update tag
curl -X PUT http://localhost:7001/tags/1 \
  -F "name=critical-issue" \
  -F "color=#cc0000" \
  -F "description=Updated description"

# Delete tag
curl -X DELETE http://localhost:7001/tags/1
```

---

## 🔄 Bulk Operations

### Bulk Update Tickets
```bash
# Update multiple tickets at once
curl -X PUT http://localhost:7001/tickets/bulk/update \
  -F "ticket_ids=1,2,3,4" \
  -F "status=resolved" \
  -F "agent=support.team@company.com" \
  -F "comment=Bulk resolved after system update"

# Bulk priority change
curl -X PUT http://localhost:7001/tickets/bulk/update \
  -F "ticket_ids=5,6,7" \
  -F "priority=urgent" \
  -F "comment=Escalated due to customer impact"
```

### Bulk Delete Tickets
```bash
# Delete multiple tickets (use with caution!)
curl -X DELETE http://localhost:7001/tickets/bulk/delete \
  -F "ticket_ids=10,11,12"
```

---

## 📊 Statistics & Reporting

### Get Comprehensive Statistics
```bash
# Get detailed ticket statistics
curl http://localhost:7001/tickets/stats/summary
```

**Example Response:**
```json
{
  "tickets": {
    "total": 150,
    "by_status": {
      "new": 25,
      "open": 45,
      "pending": 20,
      "resolved": 35,
      "closed": 25
    },
    "by_agent": {
      "john.doe": 30,
      "jane.smith": 25,
      "unassigned": 15
    },
    "by_customer": {
      "admin@company.com": 10,
      "user@example.com": 8
    }
  },
  "attachments": {
    "total_files": 45,
    "tickets_with_attachments": 20,
    "average_files_per_ticket": 2.25
  }
}
```

### Original Statistics (Preserved)
```bash
# Original ticket count endpoint
curl http://localhost:7001/ticketcount
```

---

## 🔄 Backward Compatibility Testing

### Original Endpoints (Still Working)
```bash
# Original health check
curl http://localhost:7001/plac

# Original ticket operations
curl http://localhost:7001/ticket/
curl http://localhost:7001/ticket/1/

# Create ticket (original format)
curl -X POST http://localhost:7001/ticket/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Original Format Ticket",
    "description": "Testing backward compatibility",
    "status": "new",
    "customer": "legacy@example.com",
    "agent": "support",
    "agent_notes": "Created via original API"
  }'

# Update ticket (original format)
curl -X PUT http://localhost:7001/ticket/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Original Ticket",
    "description": "Updated via original API",
    "status": "open",
    "customer": "legacy@example.com",
    "agent": "support.updated",
    "agent_notes": "Updated via original API"
  }'
```

---

## 🧪 Complete Workflow Test

### End-to-End Scenario
```bash
# 1. Create tags
curl -X POST http://localhost:7001/tags/ \
  -F "name=urgent" -F "color=#ff0000" -F "description=Urgent issues"

curl -X POST http://localhost:7001/tags/ \
  -F "name=database" -F "color=#0066cc" -F "description=Database issues"

# 2. Create ticket with attachments
echo "Error log details..." > error.log
echo "System diagnostics..." > diagnostics.txt

curl -X POST http://localhost:7001/tickets/ \
  -F "title=Critical Database Performance Issue" \
  -F "description=Database queries are timing out affecting all users" \
  -F "status=new" \
  -F "customer=admin@company.com" \
  -F "priority=urgent" \
  -F "ticket_type=incident" \
  -F "files=@error.log" \
  -F "files=@diagnostics.txt" \
  -F "uploaded_by=admin@company.com"

# 3. Assign ticket
curl -X PUT http://localhost:7001/tickets/1/assign \
  -F "agent=dba@company.com" \
  -F "comment=Assigning to database team" \
  -F "notify_agent=true"

# 4. Update status
curl -X PUT http://localhost:7001/tickets/1/status \
  -F "new_status=open" \
  -F "comment=Started investigation"

# 5. Add more information
echo "Additional findings..." > update.txt
curl -X PUT http://localhost:7001/tickets/1 \
  -F "agent_notes=Found the root cause in query optimization" \
  -F "files=@update.txt"

# 6. Resolve ticket
curl -X PUT http://localhost:7001/tickets/1/status \
  -F "new_status=resolved" \
  -F "comment=Optimized database indexes, performance restored"

# 7. Get final ticket state
curl http://localhost:7001/tickets/1

# 8. Get statistics
curl http://localhost:7001/tickets/stats/summary
```

---

## 🔧 Error Testing

### Test Validation
```bash
# Test file size limits (should fail for files > 10MB)
# Test invalid file types
# Test invalid status transitions
# Test invalid ticket IDs
# Test malformed requests

# Example: Invalid status transition
curl -X PUT http://localhost:7001/tickets/1/status \
  -F "new_status=invalid_status"

# Example: Invalid ticket ID
curl http://localhost:7001/tickets/99999
```

---

## 📋 API Endpoint Summary

### **Enhanced Tickets** (`/tickets`)
- `GET /tickets/` - List with advanced filtering
- `GET /tickets/{id}` - Get single ticket with attachments
- `POST /tickets/` - Create with file uploads
- `PUT /tickets/{id}` - Update with new files
- `GET /tickets/{id}/attachments` - List attachments
- `GET /tickets/{id}/attachments/{att_id}/download` - Download file
- `DELETE /tickets/{id}/attachments/{att_id}` - Delete attachment
- `GET /tickets/search/` - Advanced search
- `PUT /tickets/{id}/status` - Status transitions
- `PUT /tickets/{id}/assign` - Assign agent
- `PUT /tickets/{id}/unassign` - Unassign agent
- `PUT /tickets/bulk/update` - Bulk operations
- `DELETE /tickets/bulk/delete` - Bulk delete
- `GET /tickets/stats/summary` - Comprehensive stats

### **Tags** (`/tags`)
- `GET /tags/` - List tags
- `POST /tags/` - Create tag
- `PUT /tags/{id}` - Update tag
- `DELETE /tags/{id}` - Delete tag

### **Original** (Preserved)
- `GET /plac` - Health check
- `GET /ticket/` - List tickets
- `POST /ticket/` - Create ticket
- `PUT /ticket/{id}/` - Update ticket
- `GET /ticketcount` - Statistics

---

## 🎯 Production Readiness Checklist

- ✅ **File Upload Security** - Type and size validation
- ✅ **Input Validation** - Form and query parameter validation
- ✅ **Error Handling** - Comprehensive error responses
- ✅ **Pagination** - Efficient data loading
- ✅ **Search Performance** - Optimized queries
- ✅ **Bulk Operation Limits** - Prevent abuse
- ✅ **Status Workflow Validation** - Business rule enforcement
- ✅ **File Management** - Proper cleanup and storage
- ✅ **API Documentation** - Auto-generated OpenAPI docs
- ✅ **Backward Compatibility** - Legacy endpoint preservation

Your PlacDesk API is now enterprise-ready with full Zendesk-style functionality! 🚀

## 🔗 Quick Links
- **API Docs**: http://localhost:7001/docs
- **Alternative Docs**: http://localhost:7001/redoc
- **Health Check**: http://localhost:7001/plac