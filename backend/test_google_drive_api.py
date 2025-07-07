#!/usr/bin/env python3
"""
Test script to verify Google Drive API endpoints.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from api.google_drive import get_google_drive_service

def test_google_drive_service():
    print("🔧 Testing Google Drive Service")
    print("=" * 40)
    
    try:
        # Test getting the service
        print("📡 Testing Google Drive service creation...")
        service = get_google_drive_service()
        print("✅ Google Drive service created successfully")
        
        # Test connection
        print("📡 Testing Google Drive connection...")
        about = service.about().get(fields="user").execute()
        user_email = about.get("user", {}).get("emailAddress", "Unknown")
        print(f"✅ Connected to Google Drive as: {user_email}")
        
        # Test listing files
        print("📡 Testing file listing...")
        results = service.files().list(
            q="trashed=false",
            pageSize=5,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        print(f"✅ Found {len(files)} files in Google Drive")
        
        if files:
            print("📁 Sample files:")
            for file in files[:3]:
                print(f"   - {file.get('name', 'Unknown')} ({file.get('mimeType', 'Unknown type')})")
        
        print("\n🎉 Google Drive API is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Google Drive API: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def main():
    success = test_google_drive_service()
    
    if success:
        print("\n✅ All tests passed! Google Drive integration is ready.")
    else:
        print("\n❌ Tests failed. Please check your configuration.")

if __name__ == "__main__":
    main() 