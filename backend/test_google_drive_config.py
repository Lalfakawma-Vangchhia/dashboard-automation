#!/usr/bin/env python3
"""
Test script to verify Google Drive configuration.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from config import get_settings

def main():
    print("🔧 Google Drive Configuration Test")
    print("=" * 40)
    
    try:
        settings = get_settings()
        
        print(f"✅ Google Drive Client ID: {'✅ Set' if settings.google_drive_client_id else '❌ Not set'}")
        print(f"✅ Google Drive Client Secret: {'✅ Set' if settings.google_drive_client_secret else '❌ Not set'}")
        print(f"✅ Google Drive Access Token: {'✅ Set' if settings.google_drive_access_token else '❌ Not set'}")
        print(f"✅ Google Drive Refresh Token: {'✅ Set' if settings.google_drive_refresh_token else '❌ Not set'}")
        
        # Check if .env file exists
        env_file = Path(".env")
        if env_file.exists():
            print(f"✅ .env file exists: {env_file.absolute()}")
        else:
            print(f"❌ .env file not found")
        
        # Check if token.json exists
        token_file = Path("token.json")
        if token_file.exists():
            print(f"✅ token.json exists: {token_file.absolute()}")
        else:
            print(f"❌ token.json not found")
        
        print("\n📋 Summary:")
        if settings.google_drive_client_id and settings.google_drive_client_secret:
            print("✅ Basic Google Drive credentials are configured")
        else:
            print("❌ Google Drive credentials are missing")
            
        if settings.google_drive_access_token and settings.google_drive_refresh_token:
            print("✅ Google Drive tokens are configured (will use environment variables)")
        elif token_file.exists():
            print("✅ Google Drive tokens are configured (will use token.json)")
        else:
            print("❌ Google Drive tokens are not configured (will use OAuth flow)")
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")

if __name__ == "__main__":
    main() 