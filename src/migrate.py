#!/usr/bin/env python3
"""
Migration script for PlacDesk database schema enhancement
Run this script to migrate from the old schema to the new enhanced schema
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment or default"""
    return os.getenv("DATABASE_URL", "postgresql://placdesk:placdesk@db:5432/placdesk")

def run_alembic_command(cmd_name: str, *args, **kwargs):
    """Run an Alembic command"""
    try:
        alembic_cfg = Config("alembic.ini")
        getattr(command, cmd_name)(alembic_cfg, *args, **kwargs)
        logger.info(f"Successfully executed: alembic {cmd_name}")
        return True
    except Exception as e:
        logger.error(f"Error executing alembic {cmd_name}: {e}")
        return False

def check_database_connection():
    """Check if database is accessible"""
    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def check_existing_schema():
    """Check if the database has the old schema"""
    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            # Check if tickets table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'tickets'
                );
            """))
            return result.scalar()
    except Exception as e:
        logger.error(f"Error checking schema: {e}")
        return False

def backup_database():
    """Create a database backup before migration"""
    try:
        db_url = get_database_url()
        # Extract connection details
        # Format: postgresql://user:password@host:port/database
        parts = db_url.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        database = host_db[1]
        
        backup_file = f"backup_{database}_{os.urandom(4).hex()}.sql"
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        cmd = f"pg_dump -h {host} -p {port} -U {user} -d {database} > {backup_file}"
        
        logger.info(f"Creating backup: {backup_file}")
        logger.warning("Backup creation requires pg_dump to be installed and accessible")
        logger.info(f"Manual backup command: {cmd}")
        
        return True
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("=== PlacDesk Database Migration ===")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database. Please ensure PostgreSQL is running.")
        sys.exit(1)
    
    # Check if we need to initialize Alembic
    has_existing_schema = check_existing_schema()
    
    if has_existing_schema:
        logger.info("Existing tickets table found. Will migrate existing data.")
        
        # Create backup
        logger.info("Creating database backup...")
        backup_database()
        
        # Stamp current state as baseline
        logger.info("Marking current schema as baseline...")
        if not run_alembic_command("stamp", "001"):
            logger.error("Failed to stamp baseline migration")
            sys.exit(1)
        
        # Apply enhancement migration
        logger.info("Applying schema enhancements...")
        if not run_alembic_command("upgrade", "002"):
            logger.error("Failed to apply enhancement migration")
            sys.exit(1)
    else:
        logger.info("No existing schema found. Creating fresh database.")
        
        # Run all migrations
        if not run_alembic_command("upgrade", "head"):
            logger.error("Failed to create database schema")
            sys.exit(1)
    
    logger.info("=== Migration completed successfully! ===")
    logger.info("Your database now supports:")
    logger.info("  ✓ Priority levels (Low, Normal, High, Urgent)")
    logger.info("  ✓ Enhanced statuses (New, Open, Pending, On-Hold, Resolved, Closed)")
    logger.info("  ✓ Ticket types (Incident, Request, Problem, Change)")
    logger.info("  ✓ Custom fields with multiple data types")
    logger.info("  ✓ Tags/labels for ticket organization")
    logger.info("  ✓ Improved timestamps and SLA tracking")

if __name__ == "__main__":
    main()