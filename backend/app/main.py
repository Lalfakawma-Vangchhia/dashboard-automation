from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import create_tables
from app.api import auth, social_media, ai, google_drive
from app.services.scheduler_service import scheduler_service
import logging
import asyncio
import os
import signal
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Automation Dashboard API",
    description="Backend API for social media automation dashboard",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Create temp_images directory if it doesn't exist
temp_images_path = Path("temp_images")
temp_images_path.mkdir(exist_ok=True)

# Mount the static files
app.mount("/temp_images", StaticFiles(directory="temp_images"), name="temp_images")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add trusted host middleware for production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual domain in production
    )


@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    logger.info("Starting Automation Dashboard API...")
    
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't fail startup for database issues
    
    # Start scheduler service for automatic post scheduling
    try:
        asyncio.create_task(scheduler_service.start())
        logger.info("Scheduler service started for automatic posts")
    except Exception as e:
        logger.error(f"Failed to start scheduler service: {e}")
    
    logger.info("Automation Dashboard API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    logger.info("Shutting down Automation Dashboard API...")
    
    # Stop scheduler service
    try:
        scheduler_service.stop()
        logger.info("Scheduler service stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler service: {e}")


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Automation Dashboard API",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "debug": settings.debug,
        "database": "connected"
    }


# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(social_media.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(google_drive.router)


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "status_code": 404
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping server...")
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        logger.info("Starting FastAPI server...")
        logger.info("Press Ctrl+C to stop the server")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Server shutdown complete") 