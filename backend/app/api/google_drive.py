from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request as FastAPIRequest
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import Optional, List
import io
import base64
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import os
import json
import tempfile

from ..database import get_db
from ..models.user import User
from ..api.auth import get_current_user
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google-drive", tags=["Google Drive"])

# Google Drive API scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file'
]

# Get settings
settings = get_settings()

def get_google_drive_service():
    """Get authenticated Google Drive service."""
    creds = None
    
    # First, try to use environment variables for tokens
    if settings.google_drive_access_token and settings.google_drive_refresh_token:
        try:
            creds = Credentials(
                token=settings.google_drive_access_token,
                refresh_token=settings.google_drive_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_drive_client_id,
                client_secret=settings.google_drive_client_secret,
                scopes=SCOPES
            )
            logger.info("Using Google Drive credentials from environment variables")
        except Exception as e:
            logger.warning(f"Failed to create credentials from environment variables: {e}")
            creds = None
    
    # If no environment credentials, try token.json file
    if not creds and os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            logger.info("Loaded existing credentials from token.json")
        except Exception as e:
            logger.warning(f"Failed to load existing credentials: {e}")
            # Remove invalid token file
            if os.path.exists("token.json"):
                os.remove("token.json")
            creds = None
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed expired credentials")
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            # Check if we have environment variables configured
            if not settings.google_drive_client_id or not settings.google_drive_client_secret:
                raise HTTPException(
                    status_code=500,
                    detail="Google Drive credentials not configured. Please set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET environment variables."
                )
            
            # Create client config from environment variables
            client_config = {
                "installed": {
                    "client_id": settings.google_drive_client_id,
                    "client_secret": settings.google_drive_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost:8000/"]
                }
            }
            
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            logger.info("Starting OAuth flow on port 8000...")
            creds = flow.run_local_server(port=8000)
            logger.info("OAuth flow completed successfully")
            
            # Save the credentials for the next run
            try:
                with open("token.json", 'w') as token:
                    token.write(creds.to_json())
                logger.info("Saved credentials to token.json")
            except Exception as e:
                logger.error(f"Failed to save credentials: {e}")
    
    return build('drive', 'v3', credentials=creds)

@router.get("/auth")
async def get_auth_token(current_user: User = Depends(get_current_user)):
    """Get Google Drive authentication token."""
    try:
        logger.info("Attempting to authenticate with Google Drive...")
        service = get_google_drive_service()
        logger.info("Google Drive service created successfully")
        
        # Test the connection
        about = service.about().get(fields="user").execute()
        logger.info("Successfully connected to Google Drive API")
        
        user_email = about.get("user", {}).get("emailAddress", "Unknown")
        logger.info(f"Authenticated as: {user_email}")
        
        # Get the current access token
        access_token = None
        if settings.google_drive_access_token:
            access_token = settings.google_drive_access_token
        elif os.path.exists("token.json"):
            try:
                token_creds = Credentials.from_authorized_user_file("token.json", SCOPES)
                access_token = token_creds.token
            except Exception as token_err:
                logger.warning(f"Unable to load access token from token.json: {token_err}")
        
        return {
            "success": True,
            "message": "Google Drive authenticated successfully",
            "user_email": user_email,
            "access_token": access_token
        }
    except Exception as e:
        logger.error(f"Google Drive authentication error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to authenticate with Google Drive: {str(e)}"
        )

@router.get("/files")
async def list_files(
    mime_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List files from Google Drive."""
    try:
        service = get_google_drive_service()
        
        # Build query
        query = "trashed=false"
        if mime_type:
            query += f" and mimeType contains '{mime_type}'"
        
        results = service.files().list(
            q=query,
            pageSize=50,
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, thumbnailLink)"
        ).execute()
        
        files = results.get('files', [])
        
        return {
            "success": True,
            "files": files
        }
    except Exception as e:
        logger.error(f"Error listing Google Drive files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list Google Drive files: {str(e)}"
        )

@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download a file from Google Drive."""
    try:
        service = get_google_drive_service()
        
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id).execute()
        
        # Download the file
        request = service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        file_content.seek(0)
        
        # Return the file content as base64
        file_data = file_content.read()
        file_base64 = base64.b64encode(file_data).decode('utf-8')
        
        return {
            "success": True,
            "fileContent": file_base64,
            "fileName": file_metadata.get('name', 'unknown'),
            "mimeType": file_metadata.get('mimeType', 'application/octet-stream'),
            "size": len(file_data)
        }
    except Exception as e:
        logger.error(f"Error downloading Google Drive file {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file from Google Drive: {str(e)}"
        )

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload a file to Google Drive."""
    try:
        service = get_google_drive_service()
        
        # Read file content
        file_content = await file.read()
        
        # Prepare file metadata
        file_metadata = {
            'name': file.filename,
            'mimeType': file.content_type
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create media upload
        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype=file.content_type,
            resumable=True
        )
        
        # Upload the file
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        return {
            "success": True,
            "fileId": uploaded_file.get('id'),
            "fileName": uploaded_file.get('name'),
            "webViewLink": uploaded_file.get('webViewLink')
        }
    except Exception as e:
        logger.error(f"Error uploading file to Google Drive: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file to Google Drive: {str(e)}"
        )

@router.get("/folders")
async def list_folders(current_user: User = Depends(get_current_user)):
    """List folders from Google Drive."""
    try:
        service = get_google_drive_service()
        
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=50,
            fields="nextPageToken, files(id, name, modifiedTime)"
        ).execute()
        
        folders = results.get('files', [])
        
        return {
            "success": True,
            "folders": folders
        }
    except Exception as e:
        logger.error(f"Error listing Google Drive folders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list Google Drive folders: {str(e)}"
        )

@router.get("/status")
async def google_drive_status(current_user: User = Depends(get_current_user)):
    """
    Lightweight check: returns authenticated: true/false.
    NEVER triggers the OAuth flow.    
    """
    creds_ok = False
    
    # Check environment variables first
    if settings.google_drive_access_token and settings.google_drive_refresh_token:
        try:
            creds = Credentials(
                token=settings.google_drive_access_token,
                refresh_token=settings.google_drive_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_drive_client_id,
                client_secret=settings.google_drive_client_secret,
                scopes=SCOPES
            )
            creds_ok = creds.valid and not creds.expired
        except Exception:
            pass
    
    # Check token.json file if environment variables not available
    if not creds_ok and os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            creds_ok = creds.valid and not creds.expired
        except Exception:
            # corrupted token.json – treat as unauthenticated
            pass

    return {"authenticated": creds_ok}

@router.get("/authorize")
async def get_google_drive_authorize_url(current_user: User = Depends(get_current_user)):
    """
    Get Google OAuth consent URL for popup authentication.
    Returns the URL without triggering a redirect.
    """
    try:
        # Check if already authenticated
        if settings.google_drive_access_token and settings.google_drive_refresh_token:
            try:
                creds = Credentials(
                    token=settings.google_drive_access_token,
                    refresh_token=settings.google_drive_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.google_drive_client_id,
                    client_secret=settings.google_drive_client_secret,
                    scopes=SCOPES
                )
                if creds and creds.valid and not creds.expired:
                    return {"consent_url": None, "already_authenticated": True}
            except Exception:
                # Invalid environment tokens, continue with auth flow
                pass
        
        if os.path.exists("token.json"):
            try:
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
                if creds and creds.valid and not creds.expired:
                    return {"consent_url": None, "already_authenticated": True}
            except Exception:
                # Invalid token file, continue with auth flow
                pass

        # Check if we have environment variables configured
        if not settings.google_drive_client_id or not settings.google_drive_client_secret:
            raise HTTPException(
                status_code=500,
                detail="Google Drive credentials not configured. Please set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET environment variables."
            )

        # Create client config from environment variables
        client_config = {
            "web": {
                "client_id": settings.google_drive_client_id,
                "client_secret": settings.google_drive_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [f"{settings.backend_base_url}/api/google-drive/oauth2callback"]
            }
        }

        # Create Flow with redirect to our callback
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=f"{settings.backend_base_url}/api/google-drive/oauth2callback"
        )

        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return {"consent_url": auth_url}

    except Exception as e:
        logger.error(f"Error getting authorization URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get authorization URL: {str(e)}"
        )

@router.get("/oauth2callback", response_model=None)
async def oauth2callback(request: FastAPIRequest):
    """Handle OAuth2 callback and save credentials."""
    try:
        # Get the authorization code from query parameters
        code = request.query_params.get('code')
        if not code:
            return HTMLResponse("""
                <html><body>
                    <script>
                        window.opener.postMessage({error: 'No authorization code received'}, '*');
                        window.close();
                    </script>
                    <p>Authorization failed. You may close this window.</p>
                </body></html>
            """)

        # Create client config
        client_config = {
            "web": {
                "client_id": settings.google_drive_client_id,
                "client_secret": settings.google_drive_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [f"{settings.backend_base_url}/api/google-drive/oauth2callback"]
            }
        }

        # Create Flow and exchange code for token
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=f"{settings.backend_base_url}/api/google-drive/oauth2callback"
        )

        # Fetch token
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save credentials
        with open("token.json", 'w') as token:
            token.write(creds.to_json())
        
        logger.info(f"Google Drive credentials saved successfully")

        # Return HTML that closes the popup and notifies parent
        return HTMLResponse("""
            <html><body>
                <script>
                    window.opener.postMessage({success: true}, '*');
                    window.close();
                </script>
                <p>Authentication successful! You may close this window.</p>
            </body></html>
        """)

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(f"""
            <html><body>
                <script>
                    window.opener.postMessage({{error: '{str(e)}'}}, '*');
                    window.close();
                </script>
                <p>Authentication failed: {str(e)}. You may close this window.</p>
            </body></html>
        """) 