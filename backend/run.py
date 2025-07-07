
#!/usr/bin/env python3
"""
FastAPI server startup script with proper Ctrl+C handling for Windows.
"""

import uvicorn
import signal
import sys
import os
from pathlib import Path
from app.config import get_settings

def main():
    """Start the FastAPI server with proper signal handling."""
    
    settings = get_settings()
    
    def signal_handler(signum, frame):
        print("\n🛑 Received shutdown signal, stopping server...")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    print("🚀 Starting Automation Dashboard API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs will be at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.debug,
            log_level="info" if settings.debug else "warning",
            access_log=True,
            # Windows-specific settings for better compatibility
            use_colors=True,
            loop="asyncio"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
    finally:
        print("✅ Server shutdown complete")

if __name__ == "__main__":
    main() 