# 🐳 Docker Testing Guide for Enhanced PlacDesk API

## Quick Start for Docker Compose

### 1. Build and Start Services
```bash
# Stop any running services
docker compose down

# Build and start with new changes
docker compose up -d --build

# Check if services are running
docker compose ps
```

### 2. Test Basic Health Check
```bash
curl http://localhost:7001/plac
# Should return: {"plac": "Welcome to PlacDesk API backend: node1"}
```

### 3. Test Original Endpoints (Backward Compatibility)
```bash
# Get all tickets (original endpoint)
curl http://localhost:7001/ticket/

# Get ticket count
curl http://localhost:7001/ticketcount

# Create a ticket (original format)
curl -X POST http://localhost:7001/ticket/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Original Ticket",
    "description": "Testing backward compatibility",
    "status": "new",
    "customer": "test@example.com",
    "agent": "agent1",
    "agent_notes": "Created via original API"
  }'
```

### 4. Test Enhanced Endpoints

#### List Tickets with Pagination
```bash
# List tickets with pagination
curl "http://localhost:7001/tickets/?page=1&per_page=10"

# List tickets with filtering
curl "http://localhost:7001/tickets/?status=new&customer=test"
```

#### Create Ticket with File Upload
```bash
# Create a simple text file for testing
echo "This is a test attachment" > test_file.txt

# Create ticket with file attachment
curl -X POST http://localhost:7001/tickets/ \
  -F "title=Enhanced Ticket with File" \
  -F "description=Testing file upload functionality" \
  -F "status=new" \
  -F "customer=filetest@example.com" \
  -F "agent=agent1" \
  -F "files=@test_file.txt"
```

#### Get Ticket with Attachments
```bash
# Get specific ticket (replace 1 with actual ticket ID)
curl http://localhost:7001/tickets/1

# Get ticket attachments
curl http://localhost:7001/tickets/1/attachments
```

#### Search Tickets
```bash
# Search tickets with text query
curl "http://localhost:7001/tickets/search/?q=login&status=new"
```

#### Update Ticket Status
```bash
# Change ticket status
curl -X PUT http://localhost:7001/tickets/1/status \
  -F "new_status=open" \
  -F "comment=Started working on this issue"
```

#### Assign Ticket
```bash
# Assign ticket to agent
curl -X PUT http://localhost:7001/tickets/1/assign \
  -F "agent=john.doe" \
  -F "comment=Assigned to John for investigation"
```

### 5. Test API Documentation
```bash
# Access interactive API docs
open http://localhost:7001/docs

# Access alternative docs
open http://localhost:7001/redoc
```

## 🔍 Troubleshooting

### Check Container Logs
```bash
# Check web service logs
docker compose logs web

# Check database logs
docker compose logs db

# Follow logs in real-time
docker compose logs -f web
```

### Access Container Shell
```bash
# Access web container
docker compose exec web bash

# Check file structure inside container
docker compose exec web ls -la /usr/src/app/

# Check uploads directory
docker compose exec web ls -la /usr/src/app/uploads/
```

### Database Checks
```bash
# Access database directly
docker compose exec db psql -U placdesk -d placdesk

# Check tables
\dt

# Check tickets table structure
\d tickets

# Exit database
\q
```

### File Upload Debugging
```bash
# Check if upload directory exists in container
docker compose exec web ls -la /usr/src/app/uploads/

# Check file permissions
docker compose exec web ls -la /usr/src/app/uploads/attachments/

# Check disk space
docker compose exec web df -h
```

## 📋 Common Issues & Solutions

### 1. Import Errors
**Issue:** ModuleNotFoundError for enhanced modules
**Solution:** 
```bash
# Restart with rebuild
docker compose down
docker compose up -d --build
```

### 2. File Upload Fails
**Issue:** File upload returns 500 error
**Solutions:**
- Check upload directory permissions
- Verify file size limits
- Check allowed file extensions

### 3. Database Connection Issues
**Issue:** Database connection refused
**Solutions:**
```bash
# Restart database
docker compose restart db

# Check database is ready
docker compose exec db pg_isready -U placdesk

# Recreate network if needed
docker network rm plac-net
docker network create plac-net
```

### 4. Port Conflicts
**Issue:** Port 7001 already in use
**Solutions:**
- Stop other services using the port
- Change port in docker-compose.yml
- Use different port for testing

## 🎯 API Endpoint Summary

### Original Endpoints (Preserved)
- `GET /ticket/` - List all tickets
- `GET /ticket/{id}/` - Get single ticket
- `POST /ticket/` - Create ticket
- `PUT /ticket/{id}/` - Update ticket
- `GET /ticketcount` - Ticket statistics

### Enhanced Endpoints (New)
- `GET /tickets/` - List with pagination & filtering
- `GET /tickets/{id}` - Get single ticket
- `POST /tickets/` - Create with file uploads
- `PUT /tickets/{id}` - Update with file uploads
- `GET /tickets/{id}/attachments` - List attachments
- `GET /tickets/{id}/attachments/{att_id}/download` - Download file
- `DELETE /tickets/{id}/attachments/{att_id}` - Delete attachment
- `GET /tickets/search/` - Advanced search
- `PUT /tickets/{id}/status` - Change status
- `PUT /tickets/{id}/assign` - Assign to agent

## 🚀 Next Steps

Once basic functionality is working:

1. **Add Database Migration** (if needed):
   ```bash
   docker compose run --rm migrate
   ```

2. **Test with Real Files**:
   - Upload images (JPG, PNG)
   - Upload documents (PDF, DOC)
   - Test file size limits

3. **Performance Testing**:
   - Create multiple tickets
   - Upload multiple files
   - Test pagination with large datasets

4. **Security Testing**:
   - Test file type restrictions
   - Test file size limits
   - Verify file access controls

Your enhanced Docker-based helpdesk API is ready for testing! 🎯