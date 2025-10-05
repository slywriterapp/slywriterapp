"""
Migration script to add profile_picture column to users table
Run this once to update the database schema
"""

import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add profile_picture column if it doesn't exist"""
    try:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./slywriter.db")
        logger.info(f"Connecting to database: {database_url[:30]}...")

        engine = create_engine(database_url)

        # Check if column already exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        if 'profile_picture' in columns:
            logger.info("Column 'profile_picture' already exists. No migration needed.")
            return True

        # Add the column
        logger.info("Adding 'profile_picture' column to 'users' table...")
        with engine.connect() as conn:
            # Use appropriate SQL for the database type
            if 'postgresql' in database_url:
                conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture TEXT"))
            conn.commit()

        logger.info("✓ Migration successful: profile_picture column added")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
