"""
Startup script for SlyWriter Backend
Handles database initialization and environment setup
"""

import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database import Base, init_db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('slywriter_backend.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for AI features',
        'GOOGLE_CLIENT_ID': 'Google OAuth Client ID',
        'SECRET_KEY': 'JWT Secret key for authentication'
    }
    
    missing = []
    warnings = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"- {var}: {description}")
        elif 'placeholder' in value.lower() or 'test' in value.lower():
            warnings.append(f"- {var}: Currently using placeholder value")
    
    if missing:
        logger.error("Missing required environment variables:")
        for item in missing:
            logger.error(item)
        logger.error("Please set these in your .env file")
        return False
    
    if warnings:
        logger.warning("Environment variable warnings:")
        for item in warnings:
            logger.warning(item)
    
    return True

def initialize_database():
    """Initialize database tables"""
    try:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./slywriter.db")
        logger.info(f"Initializing database: {database_url}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result:
                logger.info("Database connection successful")
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'uploads',
        'temp',
        'backups'
    ]
    
    for directory in directories:
        path = os.path.join(os.path.dirname(__file__), directory)
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created directory: {directory}")

def check_dependencies():
    """Check if all required Python packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'openai',
        'sqlalchemy',
        'pyautogui',
        'keyboard',
        'python-jose',
        'passlib',
        'google-auth'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"Missing Python packages: {', '.join(missing)}")
        logger.error("Run: pip install -r requirements.txt")
        return False
    
    logger.info("All required packages are installed")
    return True

def main():
    """Main startup routine"""
    logger.info("=" * 60)
    logger.info("SlyWriter Backend Startup")
    logger.info("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error(f"Python 3.8+ required. Current version: {sys.version}")
        sys.exit(1)
    
    # Run startup checks
    checks = [
        ("Checking dependencies", check_dependencies),
        ("Checking environment", check_environment),
        ("Creating directories", create_directories),
        ("Initializing database", initialize_database)
    ]
    
    for name, func in checks:
        logger.info(f"{name}...")
        if not func():
            logger.error(f"{name} failed!")
            sys.exit(1)
        logger.info(f"{name} completed ✓")
    
    logger.info("=" * 60)
    logger.info("Startup completed successfully!")
    logger.info("You can now run: python main_complete.py")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())