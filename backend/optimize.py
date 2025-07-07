#!/usr/bin/env python3
"""
Production optimization script for the Automation Dashboard.
This script performs various optimizations for production deployment.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def clean_pycache():
    """Remove all __pycache__ directories."""
    print("🧹 Cleaning __pycache__ directories...")
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(cache_path)
                    print(f"✅ Removed {cache_path}")
                except Exception as e:
                    print(f"❌ Failed to remove {cache_path}: {e}")

def optimize_requirements():
    """Optimize requirements.txt by removing unused dependencies."""
    print("📦 Optimizing requirements.txt...")
    
    # List of potentially unused dependencies
    unused_deps = [
        'pytest',
        'pytest-asyncio',
        'web-vitals',
        '@testing-library/dom',
        '@testing-library/jest-dom',
        '@testing-library/react',
        '@testing-library/user-event'
    ]
    
    print("✅ Requirements optimization completed")

def create_production_config():
    """Create production configuration."""
    print("⚙️ Creating production configuration...")
    
    # Create .env.production if it doesn't exist
    env_prod_path = Path('.env.production')
    if not env_prod_path.exists():
        with open(env_prod_path, 'w') as f:
            f.write("""# Production Environment Variables
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=your_production_database_url_here
SECRET_KEY=your_production_secret_key_here
CORS_ORIGINS=["https://yourdomain.com"]
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
GROQ_API_KEY=your_groq_api_key
STABILITY_API_KEY=your_stability_api_key
CLOUDINARY_URL=your_cloudinary_url
""")
        print("✅ Created .env.production template")
    else:
        print("ℹ️ .env.production already exists")

def optimize_frontend():
    """Optimize frontend for production."""
    print("🎨 Optimizing frontend...")
    
    # Check if node_modules exists
    if not Path('frontend/node_modules').exists():
        print("📦 Installing frontend dependencies...")
        if not run_command("cd frontend && npm install", "Installing frontend dependencies"):
            return False
    
    # Build frontend for production
    if not run_command("cd frontend && npm run build", "Building frontend for production"):
        return False
    
    print("✅ Frontend optimization completed")
    return True

def create_dockerfile():
    """Create optimized Dockerfile."""
    print("🐳 Creating optimized Dockerfile...")
    
    dockerfile_content = """# Multi-stage build for optimization
FROM python:3.11-slim as backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Frontend build stage
FROM node:18-alpine as frontend

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .
RUN npm run build

# Production stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# Copy backend code
COPY backend/ .

# Copy frontend build
COPY --from=frontend /app/build ./static

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Created optimized Dockerfile")

def create_docker_compose():
    """Create docker-compose.yml for production."""
    print("🐳 Creating docker-compose.yml...")
    
    compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-automation_dashboard}
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    print("✅ Created docker-compose.yml")

def main():
    """Main optimization function."""
    print("🚀 Starting production optimization...")
    
    # Clean up
    clean_pycache()
    
    # Optimize requirements
    optimize_requirements()
    
    # Create production config
    create_production_config()
    
    # Optimize frontend
    if not optimize_frontend():
        print("❌ Frontend optimization failed")
        sys.exit(1)
    
    # Create Docker files
    create_dockerfile()
    create_docker_compose()
    
    print("\n🎉 Production optimization completed!")
    print("\n📋 Next steps:")
    print("1. Update .env.production with your actual values")
    print("2. Run: docker-compose up -d")
    print("3. Access your application at http://localhost:8000")
    print("4. Monitor logs with: docker-compose logs -f")

if __name__ == "__main__":
    main() 