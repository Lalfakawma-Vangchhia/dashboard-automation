#!/usr/bin/env python3
"""
PostgreSQL Setup Script for Automation Dashboard
This script helps set up PostgreSQL database and user for the application.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import get_settings

def create_database_and_user():
    """Create PostgreSQL database and user if they don't exist."""
    settings = get_settings()
    
    # Connect to PostgreSQL server (default database)
    try:
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database="postgres"  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL server")
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.db_name,))
        database_exists = cursor.fetchone()
        
        if not database_exists:
            print(f"📦 Creating database '{settings.db_name}'...")
            cursor.execute(f"CREATE DATABASE {settings.db_name}")
            print(f"✅ Database '{settings.db_name}' created successfully")
        else:
            print(f"✅ Database '{settings.db_name}' already exists")
        
        # Connect to the new database to create tables
        conn.close()
        
        # Connect to the application database
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name
        )
        cursor = conn.cursor()
        
        print(f"✅ Connected to database '{settings.db_name}'")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'social_accounts', 'posts', 'automation_rules', 'scheduled_posts')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if existing_tables:
            print(f"📋 Found existing tables: {', '.join(existing_tables)}")
        else:
            print("📋 No existing tables found - ready for migration")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL connection error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your connection credentials")
        print("3. Ensure the postgres user has permission to create databases")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_migrations():
    """Run Alembic migrations."""
    print("\n🔄 Running database migrations...")
    
    # Change to the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Run alembic upgrade
    import subprocess
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Migrations completed successfully")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("🚀 PostgreSQL Setup for Automation Dashboard")
    print("=" * 50)
    
    # Step 1: Create database and user
    if not create_database_and_user():
        print("\n❌ Database setup failed. Please check your PostgreSQL configuration.")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_migrations():
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
    
    print("\n🎉 PostgreSQL setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Start your FastAPI application: python run.py")
    print("2. Access your application at: http://localhost:8000")
    print("3. Use pgAdmin to manage your database")

if __name__ == "__main__":
    main() 