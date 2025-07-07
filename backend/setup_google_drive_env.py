#!/usr/bin/env python3
"""
Script to help set up Google Drive environment variables.
This script will help you add your Google Drive access and refresh tokens to your .env file.
"""

import os
import sys
from pathlib import Path

def main():
    print("🔧 Google Drive Environment Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Creating one...")
        env_file.touch()
    
    print("\n📝 Please provide your Google Drive credentials:")
    
    # Get Google Drive Client ID
    client_id = input("Google Drive Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required!")
        return
    
    # Get Google Drive Client Secret
    client_secret = input("Google Drive Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required!")
        return
    
    # Get Access Token (optional)
    access_token = input("Google Drive Access Token (optional, press Enter to skip): ").strip()
    
    # Get Refresh Token (optional)
    refresh_token = input("Google Drive Refresh Token (optional, press Enter to skip): ").strip()
    
    # Read existing .env file
    env_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Remove existing Google Drive variables
    env_lines = [line for line in env_lines if not line.startswith(('GOOGLE_DRIVE_CLIENT_ID=', 'GOOGLE_DRIVE_CLIENT_SECRET=', 'GOOGLE_DRIVE_ACCESS_TOKEN=', 'GOOGLE_DRIVE_REFRESH_TOKEN='))]
    
    # Add new Google Drive variables
    env_lines.append(f"GOOGLE_DRIVE_CLIENT_ID={client_id}\n")
    env_lines.append(f"GOOGLE_DRIVE_CLIENT_SECRET={client_secret}\n")
    
    if access_token:
        env_lines.append(f"GOOGLE_DRIVE_ACCESS_TOKEN={access_token}\n")
    
    if refresh_token:
        env_lines.append(f"GOOGLE_DRIVE_REFRESH_TOKEN={refresh_token}\n")
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    print("\n✅ Google Drive environment variables have been set!")
    print(f"📁 Updated file: {env_file.absolute()}")
    
    if access_token and refresh_token:
        print("\n🎉 You're all set! The Google Drive integration should work with your tokens.")
    else:
        print("\n⚠️  Note: You didn't provide access/refresh tokens.")
        print("   The system will use OAuth flow for authentication.")
        print("   You can add them later by running this script again.")

if __name__ == "__main__":
    main() 