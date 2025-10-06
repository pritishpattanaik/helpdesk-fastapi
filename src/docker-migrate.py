#!/usr/bin/env python3
"""
Docker-compatible migration script for PlacDesk database schema enhancement
This script is designed to run inside the Docker container
"""

import os
import sys
import time
import logging
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment"""
    return os.getenv("DATABASE_URL", "postgresql://placdesk:placdesk@db:5432/placdesk")

def wait_for_database(max_retries=30, delay=2):
    """Wait for database to be ready"""
    logger.info("Waiting for database to be ready...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(get_database_url())
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database is ready!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"Database not ready (attempt {attempt + 1}/{max_retries}). Waiting {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                return False
    
    return False

def run_alembic_command(cmd_name: str, *args, **kwargs):
    """Run an Alembic command"""
    try:
        alembic_cfg = Config("alembic.ini")
        # Override the database URL from environment
        alembic_cfg.set_main_option("sqlalchemy.url", get_database_url())
        
        getattr(command, cmd_name)(alembic_cfg, *args, **kwargs)
        logger.info(f"Successfully executed: alembic {cmd_name}")
        return True
    except Exception as e:
        logger.error(f"Error executing alembic {cmd_name}: {e}")
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

def check_alembic_version():
    """Check if Alembic version table exists"""
    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                );
            """))
            return result.scalar()
    except Exception as e:
        logger.error(f"Error checking Alembic version table: {e}")
        return False

def main():
    """Main migration function for Docker environment"""
    logger.info("=== PlacDesk Database Migration (Docker) ===")
    
    # Wait for database to be ready
    if not wait_for_database():
        logger.error("Database is not accessible. Exiting.")
        sys.exit(1)
    
    # Check current state
    has_existing_schema = check_existing_schema()
    has_alembic_version = check_alembic_version()
    
    if has_existing_schema and not has_alembic_version:
        logger.info("Existing tickets table found without Alembic versioning.")
        logger.info("This appears to be a legacy database that needs migration.")
        
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
            
    elif has_alembic_version:
        logger.info("Alembic version table found. Running standard upgrade...")
        
        # Get current version
        try:
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", get_database_url())
            current = command.current(alembic_cfg)
            logger.info(f"Current database version: {current if current else 'None'}")
        except Exception as e:
            logger.warning(f"Could not determine current version: {e}")
        
        # Run upgrade to latest
        if not run_alembic_command("upgrade", "head"):
            logger.error("Failed to upgrade database")
            sys.exit(1)
            
    else:
        logger.info("No existing schema found. Creating fresh database.")
        
        # Run all migrations from scratch
        if not run_alembic_command("upgrade", "head"):
            logger.error("Failed to create database schema")
            sys.exit(1)
    
    logger.info("=== Migration completed successfully! ===")
    logger.info("Database schema is now enhanced with:")
    logger.info("  ✓ Priority levels (Low, Normal, High, Urgent)")
    logger.info("  ✓ Enhanced statuses (New, Open, Pending, On-Hold, Resolved, Closed)")
    logger.info("  ✓ Ticket types (Incident, Request, Problem, Change)")
    logger.info("  ✓ Custom fields with multiple data types")
    logger.info("  ✓ Tags/labels for ticket organization")
    logger.info("  ✓ Improved timestamps and SLA tracking")

if __name__ == "__main__":
    main()