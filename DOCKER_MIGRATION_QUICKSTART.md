# 🚀 Docker Migration Quick Start

## Simple 3-Step Migration for Docker Compose

### Step 1: Backup Database
```bash
# Create backup
docker compose exec db pg_dump -U placdesk placdesk > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Run Migration
```bash
# Stop web service (keep database running)
docker compose stop web

# Run migration
docker compose run --rm migrate

# Or with profile
docker compose --profile migration up migrate
```

### Step 3: Restart Services
```bash
# Start web service
docker compose up -d web

# Verify it works
curl http://localhost:7001/plac
curl http://localhost:7001/ticketcount
```

## ✅ Done!

Your database now supports:
- ✅ Priority levels (Low, Normal, High, Urgent)
- ✅ Enhanced statuses (New, Open, Pending, On-Hold, Resolved, Closed)
- ✅ Ticket types (Incident, Request, Problem, Change)
- ✅ Custom fields system
- ✅ Tags/labels
- ✅ SLA tracking with due dates
- ✅ Improved timestamps

## 🔍 Quick Verification

```bash
# Check if migration worked
docker compose exec db psql -U placdesk -d placdesk -c "\dt"

# Should see: custom_field_values, custom_fields, tags, ticket_tags, tickets
```

## 🆘 If Something Goes Wrong

1. **Restore backup:**
   ```bash
   docker compose exec db psql -U placdesk -d placdesk < your_backup_file.sql
   ```

2. **Check logs:**
   ```bash
   docker compose logs migrate
   docker compose logs db
   ```

3. **Force rebuild:**
   ```bash
   docker compose build --no-cache
   ```

## 📖 Full Documentation

For detailed information, see [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md)