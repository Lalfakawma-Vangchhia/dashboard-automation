from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Create database engine
if settings.database_url.startswith("postgresql"):
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.debug,
        pool_size=30,         # Increased from 10 to 30
        max_overflow=60,      # Increased from 20 to 60
        pool_timeout=60,      # Increased timeout to 60 seconds
        pool_recycle=1800     # Recycle connections every 30 minutes
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database (for Alembic compatibility)
def init_db():
    """Initialize database - imports all models to ensure they're registered with SQLAlchemy"""
    try:
        # Import all models to ensure they're registered with Base.metadata
        from app.models import user, automation_rule, post, social_account
        print("✅ Database models registered successfully")
        return True
    except Exception as e:
        print(f"❌ Database model registration error: {e}")
        return False


# Verify database connection
def verify_db_connection():
    """Verify database connection without creating tables"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        print("✅ Database connection verified")
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False 