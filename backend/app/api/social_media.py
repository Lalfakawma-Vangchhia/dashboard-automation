from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.social_account import SocialAccount
from app.models.post import Post, PostStatus, PostType
from app.models.automation_rule import AutomationRule, RuleType, TriggerType
from app.models.scheduled_post import ScheduledPost, FrequencyType
from app.schemas.social_media import (
    SocialAccountResponse, PostCreate, PostResponse, PostUpdate,
    AutomationRuleCreate, AutomationRuleResponse, AutomationRuleUpdate,
    FacebookConnectRequest, FacebookPostRequest, AutoReplyToggleRequest,
    InstagramConnectRequest, InstagramPostRequest, InstagramAccountInfo,
    InstagramAutoReplyToggleRequest, SuccessResponse, ErrorResponse
)
from pydantic import BaseModel, Field, validator, model_validator
from datetime import datetime
import logging
from app.services.instagram_service import instagram_service


# Image Generation Request Models
class ImageGenerationRequest(BaseModel):
    """Request model for image generation."""
    image_prompt: str = Field(..., min_length=1, max_length=500, description="Prompt for image generation")
    post_type: str = Field(default="feed", description="Type of post for sizing (feed, story, square, etc.)")


# Unified Facebook post request model
class UnifiedFacebookPostRequest(BaseModel):
    """Unified request model for creating Facebook posts with various options."""
    page_id: str = Field(..., description="Facebook page ID")
    text_content: Optional[str] = Field(None, description="Text content for the post (if not using AI generation)")
    content_prompt: Optional[str] = Field(None, description="Prompt for AI text generation")
    image_prompt: Optional[str] = Field(None, description="Prompt for AI image generation")
    image_url: Optional[str] = Field(None, description="URL of existing image to use")
    image_filename: Optional[str] = Field(None, description="Filename of existing image")
    video_url: Optional[str] = Field(None, description="URL of existing video to use (base64 data URL)")
    video_filename: Optional[str] = Field(None, description="Filename of existing video")
    post_type: str = Field(default="feed", description="Type of post for sizing")
    use_ai_text: bool = Field(default=False, description="Whether to generate text using AI")
    use_ai_image: bool = Field(default=False, description="Whether to generate image using AI")
    
    @model_validator(mode='after')
    def validate_content_requirements(self):
        """Ensure at least one content source is provided."""
        text_content = self.text_content
        content_prompt = self.content_prompt
        image_url = self.image_url
        image_prompt = self.image_prompt
        video_url = self.video_url
        
        # Check if we have any content
        has_text = text_content and text_content.strip()
        has_content_prompt = content_prompt and content_prompt.strip()
        has_image_url = image_url and image_url.strip()
        has_image_prompt = image_prompt and image_prompt.strip()
        has_video_url = video_url and video_url.strip()
        
        if not any([has_text, has_content_prompt, has_image_url, has_image_prompt, has_video_url]):
            raise ValueError("At least one of text_content, content_prompt, image_url, image_prompt, or video_url must be provided")
        
        return self


# Instagram Image Generation Request Models
class InstagramImageGenerationRequest(BaseModel):
    """Request model for Instagram image generation."""
    image_prompt: str = Field(..., min_length=1, max_length=500, description="Prompt for image generation")
    post_type: str = Field(default="feed", description="Type of post for sizing (feed, story, square, etc.)")


# Instagram Carousel Generation Request Models
class InstagramCarouselGenerationRequest(BaseModel):
    """Request model for Instagram carousel generation."""
    image_prompt: str = Field(..., min_length=1, max_length=500, description="Prompt for carousel images")
    count: int = Field(default=3, ge=3, le=7, description="Number of images to generate (3-7)")
    post_type: str = Field(default="feed", description="Type of post for sizing (feed, story, square, etc.)")


# Instagram Carousel Post Request Models
class InstagramCarouselPostRequest(BaseModel):
    """Request model for Instagram carousel posting."""
    instagram_user_id: str = Field(..., description="Instagram user ID")
    caption: str = Field(..., min_length=1, max_length=2200, description="Caption for the carousel")
    image_urls: List[str] = Field(..., min_items=3, max_items=7, description="List of image URLs (3-7 images)")


# Unified Instagram post request model
class UnifiedInstagramPostRequest(BaseModel):
    """Unified request model for creating Instagram posts with various options."""
    instagram_user_id: str = Field(..., description="Instagram user ID")
    caption: Optional[str] = Field(None, description="Text caption for the post")
    content_prompt: Optional[str] = Field(None, description="Prompt for AI text generation")
    image_prompt: Optional[str] = Field(None, description="Prompt for AI image generation")
    image_url: Optional[str] = Field(None, description="URL of existing image to use")
    image_filename: Optional[str] = Field(None, description="Filename of existing image")
    video_url: Optional[str] = Field(None, description="URL of existing video to use (base64 data URL)")
    video_filename: Optional[str] = Field(None, description="Filename of existing video")
    post_type: str = Field(default="feed", description="Type of post for sizing")
    use_ai_text: bool = Field(default=False, description="Whether to generate text using AI")
    use_ai_image: bool = Field(default=False, description="Whether to generate image using AI")
    media_type: str = Field(default="image", description="Type of media (image, video, carousel)")
    
    @model_validator(mode='after')
    def validate_content_requirements(self):
        """Ensure at least one content source is provided."""
        caption = self.caption
        content_prompt = self.content_prompt
        image_url = self.image_url
        image_prompt = self.image_prompt
        video_url = self.video_url
        video_filename = self.video_filename
        
        # Check if we have any content
        has_caption = caption and caption.strip()
        has_content_prompt = content_prompt and content_prompt.strip()
        has_image_url = image_url and image_url.strip()
        has_image_prompt = image_prompt and image_prompt.strip()
        has_video_url = video_url and video_url.strip()
        has_video_filename = video_filename and video_filename.strip()
        
        if not any([has_caption, has_content_prompt, has_image_url, has_image_prompt, has_video_url, has_video_filename]):
            raise ValueError("At least one of caption, content_prompt, image_url, image_prompt, video_url, or video_filename must be provided")
        
        return self

router = APIRouter(prefix="/social", tags=["social media"])

logger = logging.getLogger(__name__)


# Social Account Management
@router.get("/accounts", response_model=List[SocialAccountResponse])
async def get_social_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all connected social media accounts for the current user."""
    accounts = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id
    ).all()
    return accounts


@router.get("/accounts/{account_id}", response_model=SocialAccountResponse)
async def get_social_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific social media account."""
    account = db.query(SocialAccount).filter(
        SocialAccount.id == account_id,
        SocialAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found"
        )
    
    return account


# Facebook Integration
@router.get("/facebook/status")
async def get_facebook_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has existing Facebook connections."""
    facebook_accounts = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.platform == "facebook",
        SocialAccount.is_connected == True
    ).all()
    
    if not facebook_accounts:
        return {
            "connected": False,
            "message": "No Facebook accounts connected"
        }
    
    # Separate personal accounts from pages
    personal_accounts = [acc for acc in facebook_accounts if acc.account_type == "personal"]
    page_accounts = [acc for acc in facebook_accounts if acc.account_type == "page"]
    
    return {
        "connected": True,
        "message": f"Found {len(facebook_accounts)} Facebook connection(s)",
        "accounts": {
            "personal": [{
                "id": acc.id,
                "platform_id": acc.platform_user_id,
                "name": acc.display_name or "Personal Profile",
                "profile_picture": acc.profile_picture_url,
                "connected_at": acc.connected_at.isoformat() if acc.connected_at else None
            } for acc in personal_accounts],
            "pages": [{
                "id": acc.id,
                "platform_id": acc.platform_user_id,
                "name": acc.display_name,
                "category": acc.platform_data.get("category", "Page") if acc.platform_data else "Page",
                "profile_picture": acc.profile_picture_url,
                "follower_count": acc.follower_count or 0,
                "can_post": acc.platform_data.get("can_post", True) if acc.platform_data else True,
                "can_comment": acc.platform_data.get("can_comment", True) if acc.platform_data else True,
                "connected_at": acc.connected_at.isoformat() if acc.connected_at else None
            } for acc in page_accounts]
        },
        "total_accounts": len(facebook_accounts),
        "pages_count": len(page_accounts)
    }


@router.post("/facebook/logout")
async def logout_facebook(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect all Facebook accounts for the user."""
    try:
        # Find all Facebook accounts for this user
        facebook_accounts = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook"
        ).all()
        
        if not facebook_accounts:
            return SuccessResponse(
                message="No Facebook accounts to disconnect"
            )
        
        # Mark all as disconnected and clear sensitive data
        disconnected_count = 0
        for account in facebook_accounts:
            account.is_connected = False
            account.access_token = ""  # Clear the token for security
            account.last_sync_at = datetime.utcnow()
            disconnected_count += 1
        
        db.commit()
        
        logger.info(f"User {current_user.id} disconnected {disconnected_count} Facebook accounts")
        
        return SuccessResponse(
            message=f"Successfully disconnected {disconnected_count} Facebook account(s)",
            data={
                "disconnected_accounts": disconnected_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error disconnecting Facebook accounts for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect Facebook accounts"
        )


@router.post("/facebook/connect")
async def connect_facebook(
    request: FacebookConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect Facebook account and pages."""
    try:
        from app.services.facebook_service import facebook_service
        
        logger.info(f"Facebook connect request for user {current_user.id}: {request.user_id}")
        logger.info(f"Pages data received: {len(request.pages or [])} pages")
        
        # Exchange short-lived token for long-lived token
        logger.info("Exchanging short-lived token for long-lived token...")
        token_exchange_result = await facebook_service.exchange_for_long_lived_token(request.access_token)
        
        if not token_exchange_result["success"]:
            logger.error(f"Token exchange failed: {token_exchange_result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get long-lived token: {token_exchange_result.get('error')}"
            )
        
        long_lived_token = token_exchange_result["access_token"]
        expires_at = token_exchange_result["expires_at"]
        
        logger.info(f"Successfully got long-lived token, expires at: {expires_at}")
        
        # Validate the new long-lived token
        validation_result = await facebook_service.validate_access_token(long_lived_token)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Long-lived token validation failed: {validation_result.get('error')}"
            )
        
        # Check if account already exists
        existing_account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.platform_user_id == request.user_id
        ).first()
        
        if existing_account:
            # Update existing account with long-lived token
            existing_account.access_token = long_lived_token
            existing_account.token_expires_at = expires_at
            existing_account.is_connected = True
            existing_account.last_sync_at = datetime.utcnow()
            existing_account.display_name = validation_result.get("name")
            existing_account.profile_picture_url = validation_result.get("picture")
            db.commit()
            account = existing_account
        else:
            # Create new account with long-lived token
            account = SocialAccount(
                user_id=current_user.id,
                platform="facebook",
                platform_user_id=request.user_id,
                access_token=long_lived_token,
                token_expires_at=expires_at,
                account_type="personal",
                display_name=validation_result.get("name"),
                profile_picture_url=validation_result.get("picture"),
                is_connected=True,
                last_sync_at=datetime.utcnow()
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        
        # Handle pages if provided - get long-lived page tokens
        connected_pages = []
        if request.pages:
            logger.info(f"Processing {len(request.pages)} Facebook pages with long-lived tokens")
            
            # Get long-lived page tokens
            long_lived_pages = await facebook_service.get_long_lived_page_tokens(long_lived_token)
            
            # Create a mapping of page IDs to long-lived tokens
            page_token_map = {page["id"]: page["access_token"] for page in long_lived_pages}
            
            for page_data in request.pages:
                # Ensure we have a dict so we can use .get safely
                if hasattr(page_data, "dict"):
                    page_data = page_data.dict()

                page_id = page_data.get("id")
                page_access_token = page_token_map.get(page_id, page_data.get("access_token", ""))
                
                if not page_access_token:
                    logger.warning(f"No access token found for page {page_id}")
                    continue
                
                # Check if page account already exists
                existing_page = db.query(SocialAccount).filter(
                    SocialAccount.user_id == current_user.id,
                    SocialAccount.platform == "facebook",
                    SocialAccount.platform_user_id == page_id
                ).first()
                
                if existing_page:
                    # Update existing page account
                    existing_page.access_token = page_access_token
                    existing_page.token_expires_at = None  # Page tokens don't expire
                    existing_page.display_name = page_data.get("name", existing_page.display_name)
                    existing_page.profile_picture_url = page_data.get("picture", {}).get("data", {}).get("url", existing_page.profile_picture_url)
                    existing_page.follower_count = page_data.get("fan_count", existing_page.follower_count)
                    existing_page.is_connected = True
                    existing_page.last_sync_at = datetime.utcnow()
                    existing_page.platform_data = {
                        "category": page_data.get("category"),
                        "tasks": page_data.get("tasks", []),
                        "can_post": "CREATE_CONTENT" in page_data.get("tasks", []),
                        "can_comment": "MODERATE" in page_data.get("tasks", [])
                    }
                    page_account = existing_page
                else:
                    # Create new page account
                    page_account = SocialAccount(
                        user_id=current_user.id,
                        platform="facebook",
                        platform_user_id=page_id,
                        username=page_data.get("name", "").replace(" ", "").lower(),
                        display_name=page_data.get("name"),
                        access_token=page_access_token,
                        token_expires_at=None,  # Page tokens don't expire
                        profile_picture_url=page_data.get("picture", {}).get("data", {}).get("url"),
                        follower_count=page_data.get("fan_count", 0),
                        account_type="page",
                        platform_data={
                            "category": page_data.get("category"),
                            "tasks": page_data.get("tasks", []),
                            "can_post": "CREATE_CONTENT" in page_data.get("tasks", []),
                            "can_comment": "MODERATE" in page_data.get("tasks", [])
                        },
                        is_connected=True,
                        last_sync_at=datetime.utcnow()
                    )
                    db.add(page_account)
                
                connected_pages.append({
                    "id": page_id,
                    "name": page_data.get("name"),
                    "category": page_data.get("category"),
                    "access_token_type": "long_lived_page_token"
                })
        
        db.commit()
        
        logger.info(f"Successfully connected Facebook account {request.user_id} with {len(connected_pages)} pages")
        
        return {
            "success": True,
            "message": f"Facebook account connected successfully with long-lived tokens",
            "data": {
                "account_id": account.id,
                "user_id": request.user_id,
                "pages_connected": len(connected_pages),
                "pages": connected_pages,
                "token_type": "long_lived_user_token",
                "token_expires_at": expires_at.isoformat() if expires_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Facebook account: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect Facebook account: {str(e)}"
        )


@router.post("/facebook/post")
async def create_facebook_post(
    request: FacebookPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and schedule a Facebook post with AI integration (replaces Make.com webhook)."""
    try:
        # Import Facebook service
        from app.services.facebook_service import facebook_service
        from app.services.groq_service import groq_service
        
        # Find the Facebook account/page
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.platform_user_id == request.page_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook page not found"
            )

        if not account.access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facebook access token not found. Please reconnect your account."
            )
        
        # Validate and potentially refresh the access token
        logger.info(f"Validating Facebook token for account {account.id}")
        validation_result = await facebook_service.validate_and_refresh_token(
            account.access_token, 
            account.token_expires_at
        )
        
        if not validation_result["valid"]:
            if validation_result.get("expired") or validation_result.get("needs_reconnection"):
                # Mark account as disconnected
                account.is_connected = False
                db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Facebook login session expired. Please reconnect your account."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Facebook token validation failed: {validation_result.get('error', 'Unknown error')}"
                )
        
        # Update last sync time since token is valid
        account.last_sync_at = datetime.utcnow()
        db.commit()
        
        final_content = request.message
        ai_generated = False
        
        # Handle AI-generated content for auto posts
        if request.post_type == "auto-generated" and groq_service.is_available():
            try:
                ai_result = await groq_service.generate_facebook_post(request.message)
                if ai_result["success"]:
                    final_content = ai_result["content"]
                    ai_generated = True
            except Exception as ai_error:
                logger.error(f"AI generation failed: {ai_error}")
                # Fall back to original message if AI fails
                print(f"AI generation failed, using original message: {ai_error}")
        
        # Create post record in database
        post = Post(
            user_id=current_user.id,
            social_account_id=account.id,
            content=final_content,
            post_type=PostType.IMAGE if request.image else PostType.TEXT,
            media_urls=[request.image] if request.image else None,
            status=PostStatus.SCHEDULED,
            is_auto_post=ai_generated,
            metadata={
                "ai_generated": ai_generated,
                "original_prompt": request.message if ai_generated else None,
                "post_type": request.post_type
            }
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # Actually post to Facebook
        try:
            # Determine media type
            media_type = "text"
            if request.image:
                media_type = "photo"
            
            # Use Facebook service to create the post
            facebook_result = await facebook_service.create_post(
                page_id=request.page_id,
                access_token=account.access_token,
                message=final_content,
                media_url=request.image,
                media_type=media_type
            )
            
            # Update post status based on Facebook result
            if facebook_result and facebook_result.get("success"):
                post.status = PostStatus.PUBLISHED
                post.platform_post_id = facebook_result.get("post_id")
                post.platform_response = facebook_result
            else:
                error_msg = facebook_result.get("error", "Unknown Facebook API error")
                post.status = PostStatus.FAILED
                post.error_message = error_msg
                
                # Check if the error is due to token expiration
                if "expired" in error_msg.lower() or "session" in error_msg.lower() or "token" in error_msg.lower():
                    account.is_connected = False
                    db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Facebook login session expired. Please reconnect your account."
                    )
            
            db.commit()
            
        except HTTPException:
            raise
        except Exception as fb_error:
            logger.error(f"Facebook posting error: {fb_error}")
            post.status = PostStatus.FAILED
            post.error_message = str(fb_error)
            db.commit()
            
            # Check if the error suggests token expiration
            error_str = str(fb_error).lower()
            if "expired" in error_str or "session" in error_str or "unauthorized" in error_str:
                account.is_connected = False
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Facebook login session expired. Please reconnect your account."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to post to Facebook: {str(fb_error)}"
                )
        
        # Prepare response
        if post.status == PostStatus.PUBLISHED:
            message = "Post published successfully to Facebook!"
        elif ai_generated:
            message = "Post created with AI content (Facebook posting failed)"
        else:
            message = "Post created successfully (Facebook posting failed)"
        
        return SuccessResponse(
            message=message,
            data={
                "post_id": post.id,
                "status": post.status,
                "platform": "facebook",
                "page_name": account.display_name,
                "ai_generated": ai_generated,
                "facebook_post_id": post.platform_post_id,
                "content": final_content
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Facebook post: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create post: {str(e)}"
        )


@router.get("/facebook/posts-for-auto-reply/{page_id}")
async def get_posts_for_auto_reply(
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get posts from this app for auto-reply selection."""
    try:
        # Find the Facebook account/page
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.platform_user_id == page_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook page not found"
            )
        
        # Get posts created by this app for this page
        posts = db.query(Post).filter(
            Post.social_account_id == account.id,
            Post.status.in_([PostStatus.PUBLISHED, PostStatus.SCHEDULED])
        ).order_by(Post.created_at.desc()).limit(50).all()
        
        # Format posts for frontend
        formatted_posts = []
        for post in posts:
            formatted_posts.append({
                "id": post.id,
                "facebook_post_id": post.platform_post_id,
                "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "full_content": post.content,
                "created_at": post.created_at.isoformat(),
                "status": post.status.value,
                "has_media": bool(post.media_urls),
                "media_count": len(post.media_urls) if post.media_urls else 0
            })
        
        return {
            "success": True,
            "posts": formatted_posts,
            "total_count": len(formatted_posts)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get posts for auto-reply: {str(e)}"
        )


@router.post("/facebook/auto-reply")
async def toggle_auto_reply(
    request: AutoReplyToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle auto-reply for Facebook page with AI integration and post selection."""
    try:
        # Import Facebook service
        from app.services.facebook_service import facebook_service
        
        # Find the Facebook account/page
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.platform_user_id == request.page_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook page not found"
            )
        
        # Validate selected posts if any
        selected_posts = []
        if request.selected_post_ids:
            posts = db.query(Post).filter(
                Post.id.in_(request.selected_post_ids),
                Post.social_account_id == account.id
            ).all()
            # Get the Facebook post IDs (platform_post_id) for the selected posts
            selected_posts = [post.platform_post_id for post in posts if post.platform_post_id]
            
            logger.info(f"Selected posts: {request.selected_post_ids}")
            logger.info(f"Facebook post IDs: {selected_posts}")
            logger.info(f"Found posts in DB: {[post.id for post in posts]}")
            logger.info(f"Platform post IDs: {[post.platform_post_id for post in posts]}")
        else:
            logger.info("No selected post IDs in request")
        
        # Use Facebook service to setup auto-reply
        facebook_result = await facebook_service.setup_auto_reply(
            page_id=request.page_id,
            access_token=account.access_token,
            enabled=request.enabled,
            template=request.response_template
        )
        
        # Find or create auto-reply rule in database
        auto_reply_rule = db.query(AutomationRule).filter(
            AutomationRule.user_id == current_user.id,
            AutomationRule.social_account_id == account.id,
            AutomationRule.rule_type == RuleType.AUTO_REPLY
        ).first()
        
        if auto_reply_rule:
            # Update existing rule
            auto_reply_rule.is_active = request.enabled
            rule_actions = {
                "response_template": request.response_template,
                "ai_enabled": True,
                "facebook_setup": facebook_result,
                "selected_post_ids": request.selected_post_ids,
                "selected_facebook_post_ids": selected_posts
            }
            auto_reply_rule.actions = rule_actions
            logger.info(f"🔄 Updated existing rule {auto_reply_rule.id} with actions: {rule_actions}")
        else:
            # Create new auto-reply rule
            rule_actions = {
                "response_template": request.response_template,
                "ai_enabled": True,
                "facebook_setup": facebook_result,
                "selected_post_ids": request.selected_post_ids,
                "selected_facebook_post_ids": selected_posts
            }
            auto_reply_rule = AutomationRule(
                user_id=current_user.id,
                social_account_id=account.id,
                name=f"Auto Reply - {account.display_name}",
                rule_type=RuleType.AUTO_REPLY,
                trigger_type=TriggerType.ENGAGEMENT_BASED,
                trigger_conditions={
                    "event": "comment",
                    "selected_posts": selected_posts
                },
                actions=rule_actions,
                is_active=request.enabled
            )
            db.add(auto_reply_rule)
            logger.info(f"🆕 Created new rule with actions: {rule_actions}")
        
        db.commit()
        logger.info(f"💾 Committed rule to database. Rule ID: {auto_reply_rule.id}")
        logger.info(f"💾 Final rule actions: {auto_reply_rule.actions}")
        
        return SuccessResponse(
            message=f"Auto-reply {'enabled' if request.enabled else 'disabled'} successfully with AI integration",
            data={
                "rule_id": auto_reply_rule.id,
                "enabled": request.enabled,
                "ai_enabled": True,
                "page_name": account.display_name,
                "facebook_setup": facebook_result,
                "selected_posts_count": len(selected_posts),
                "selected_post_ids": request.selected_post_ids
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to toggle auto-reply: {str(e)}"
        )


@router.post("/facebook/refresh-tokens")
async def refresh_facebook_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate and refresh Facebook tokens for all connected accounts."""
    try:
        from app.services.facebook_service import facebook_service
        
        # Get all Facebook accounts for this user
        facebook_accounts = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.is_connected == True
        ).all()
        
        if not facebook_accounts:
            return {
                "success": True,
                "message": "No Facebook accounts to refresh",
                "accounts": []
            }
        
        refresh_results = []
        
        for account in facebook_accounts:
            try:
                logger.info(f"Validating token for account {account.id} ({account.display_name})")
                
                validation_result = await facebook_service.validate_and_refresh_token(
                    account.access_token,
                    account.token_expires_at
                )
                
                if validation_result["valid"]:
                    # Token is still valid
                    account.last_sync_at = datetime.utcnow()
                    refresh_results.append({
                        "account_id": account.id,
                        "platform_user_id": account.platform_user_id,
                        "name": account.display_name,
                        "status": "valid",
                        "message": "Token is valid"
                    })
                else:
                    # Token is invalid or expired
                    if validation_result.get("expired") or validation_result.get("needs_reconnection"):
                        account.is_connected = False
                        refresh_results.append({
                            "account_id": account.id,
                            "platform_user_id": account.platform_user_id,
                            "name": account.display_name,
                            "status": "expired",
                            "message": "Token expired - reconnection required",
                            "needs_reconnection": True
                        })
                    else:
                        refresh_results.append({
                            "account_id": account.id,
                            "platform_user_id": account.platform_user_id,
                            "name": account.display_name,
                            "status": "error",
                            "message": validation_result.get("error", "Unknown validation error")
                        })
                
            except Exception as e:
                logger.error(f"Error validating account {account.id}: {e}")
                refresh_results.append({
                    "account_id": account.id,
                    "platform_user_id": account.platform_user_id,
                    "name": account.display_name,
                    "status": "error",
                    "message": f"Validation error: {str(e)}"
                })
        
        db.commit()
        
        # Count results
        valid_count = len([r for r in refresh_results if r["status"] == "valid"])
        expired_count = len([r for r in refresh_results if r["status"] == "expired"])
        error_count = len([r for r in refresh_results if r["status"] == "error"])
        
        return {
            "success": True,
            "message": f"Token validation complete: {valid_count} valid, {expired_count} expired, {error_count} errors",
            "summary": {
                "total_accounts": len(refresh_results),
                "valid": valid_count,
                "expired": expired_count,
                "errors": error_count
            },
            "accounts": refresh_results
        }
        
    except Exception as e:
        logger.error(f"Error refreshing Facebook tokens: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh tokens: {str(e)}"
        )


# Facebook Image Generation Endpoints
@router.post("/facebook/generate-image")
async def generate_facebook_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate an image using Stability AI for Facebook posts.
    
    This endpoint generates an image without posting it to Facebook.
    Use this to preview images before posting.
    """
    try:
        from app.services.facebook_service import facebook_service
        
        logger.info(f"Generating image for user {current_user.id} with prompt: {request.image_prompt}")
        
        # Generate image
        result = await facebook_service.generate_image_only(
            image_prompt=request.image_prompt,
            post_type=request.post_type
        )
        
        if result["success"]:
            logger.info(f"Image generated successfully for user {current_user.id}")
            return {
                "success": True,
                "message": "Image generated successfully",
                "data": {
                    "image_url": result["image_url"],
                    "filename": result["filename"],
                    "prompt": result["prompt"],
                    "image_details": result["image_details"]
                }
            }
        else:
            logger.error(f"Image generation failed for user {current_user.id}: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=f"Image generation failed: {result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image generation endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image: {str(e)}"
        )


@router.post("/facebook/create-post")
async def create_unified_facebook_post(
    request: UnifiedFacebookPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simplified endpoint for creating Facebook posts with enhanced error logging.
    """
    try:
        from app.services.facebook_service import facebook_service
        
        logger.info(f"=== FACEBOOK POST DEBUG START ===")
        logger.info(f"User ID: {current_user.id}")
        logger.info(f"Request data: {request.dict()}")
        
        # Verify the user has access to the specified page
        page_account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.platform_user_id == request.page_id,
            SocialAccount.is_connected == True
        ).first()
        
        if not page_account:
            logger.error(f"Page not found or not connected for user {current_user.id}, page_id: {request.page_id}")
            raise HTTPException(
                status_code=404,
                detail="Facebook page not found or not connected"
            )
        
        logger.info(f"Found page account: {page_account.display_name} (ID: {page_account.id})")
        logger.info(f"Page access token length: {len(page_account.access_token) if page_account.access_token else 0}")
        
        # Determine content
        final_text_content = None
        final_image_url = None
        
        # Handle text content
        if request.use_ai_text or request.content_prompt:
            logger.info("Generating AI text content")
            from app.services.groq_service import groq_service
            text_result = await groq_service.generate_facebook_post(
                request.content_prompt or request.text_content or "Create an engaging Facebook post"
            )
            
            if not text_result["success"]:
                logger.error(f"AI text generation failed: {text_result.get('error')}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Text generation failed: {text_result.get('error', 'Unknown error')}"
                )
            
            final_text_content = text_result["content"]
            logger.info(f"Generated text content: {final_text_content[:100]}...")
        else:
            final_text_content = request.text_content
            logger.info(f"Using provided text content: {final_text_content[:100] if final_text_content else 'None'}...")
        
        # Handle image content
        final_image_url = None
        if request.use_ai_image or request.image_prompt:
            logger.info("Generating AI image content")
            image_result = await facebook_service.generate_image_only(
                image_prompt=request.image_prompt or request.content_prompt or request.text_content,
                post_type=request.post_type
            )
            
            if not image_result["success"]:
                logger.error(f"AI image generation failed: {image_result.get('error')}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Image generation failed: {image_result.get('error', 'Unknown error')}"
                )
            
            final_image_url = image_result["image_url"]
            logger.info(f"Generated image URL: {final_image_url[:100] if final_image_url else 'None'}...")
        elif request.image_url:
            final_image_url = request.image_url
            logger.info(f"Using provided image URL: {final_image_url[:100] if final_image_url else 'None'}...")
        
        # Handle video content
        final_video_url = None
        if request.video_url:
            final_video_url = request.video_url
            logger.info(f"Using provided video URL: {final_video_url[:100] if final_video_url else 'None'}...")
        
        # Determine post type
        if final_video_url:
            post_type = "video"
        elif final_image_url:
            post_type = "photo"
        else:
            post_type = "text"
        logger.info(f"Post type determined: {post_type}")
        logger.info(f"Final text content: {final_text_content}")
        logger.info(f"Final image URL: {final_image_url}")
        logger.info(f"Final video URL: {final_video_url}")
        
        # Create the Facebook post using the service directly
        logger.info(f"Calling Facebook service create_post method")
        logger.info(f"Parameters: page_id={request.page_id}, message={final_text_content[:50] if final_text_content else 'None'}..., media_url={final_image_url[:50] if final_image_url else 'None'}..., media_type={post_type}")
        
        # Determine which media URL to use
        media_url = final_video_url if final_video_url else final_image_url
        
        result = await facebook_service.create_post(
            page_id=request.page_id,
            access_token=page_account.access_token,
            message=final_text_content or "Generated with AI",
            media_url=media_url,
            media_type=post_type
        )
        
        logger.info(f"Facebook service result: {result}")
        
        if result["success"]:
            # Save post to database
            post = None  # Initialize post variable
            try:
                logger.info("Saving post to database...")
                # Determine post type for database
                db_post_type = PostType.TEXT
                media_urls = []
                
                if final_video_url:
                    db_post_type = PostType.VIDEO
                    media_urls = [final_video_url]
                elif final_image_url:
                    db_post_type = PostType.IMAGE
                    media_urls = [final_image_url]
                
                post = Post(
                    user_id=current_user.id,
                    social_account_id=page_account.id,
                    post_type=db_post_type,
                    content=final_text_content or "Media post",  # Ensure content is never None
                    platform_post_id=result["post_id"],
                    status=PostStatus.PUBLISHED,
                    published_at=datetime.utcnow(),
                    media_urls=media_urls if media_urls else None,
                    platform_response={
                        "facebook_result": result,
                        "metadata": {
                            "post_type": request.post_type,
                            "ai_generated_text": request.use_ai_text or bool(request.content_prompt),
                            "ai_generated_image": request.use_ai_image or bool(request.image_prompt)
                        }
                    }
                )
                logger.info(f"Post object created: {post}")
                db.add(post)
                db.commit()
                logger.info(f"Post saved to database with ID: {post.id}")
            except Exception as db_error:
                logger.error(f"Database error while saving post: {db_error}")
                logger.error(f"Post data: user_id={current_user.id}, social_account_id={page_account.id}, content={final_text_content or 'Image post'}")
                import traceback
                logger.error(f"Database error traceback: {traceback.format_exc()}")
                # Don't fail the whole request if database save fails
                logger.warning("Continuing without database save due to error")
            
            logger.info(f"=== FACEBOOK POST SUCCESS ===")
            
            return {
                "success": True,
                "message": "Facebook post created successfully",
                "data": {
                    "post_id": result["post_id"],
                    "text_content": final_text_content,
                    "image_url": final_image_url,
                    "video_url": final_video_url,
                    "database_id": post.id if post else None  # Handle case where post wasn't saved
                }
            }
        else:
            # Enhanced error logging
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"=== FACEBOOK POST FAILED ===")
            logger.error(f"Error message: {error_msg}")
            logger.error(f"Full result: {result}")
            logger.error(f"Page ID: {request.page_id}")
            logger.error(f"Access token valid: {bool(page_account.access_token)}")
            logger.error(f"Image URL type: {type(final_image_url)}")
            logger.error(f"Image URL preview: {final_image_url[:100] if final_image_url else 'None'}...")
            
            # Provide specific error messages for common issues
            if "PHOTO" in error_msg:
                detailed_error = (
                    "Facebook photo upload failed. This could be due to:\n"
                    "1. Image format not supported (use JPG, PNG, GIF)\n"
                    "2. Image file too large (max 4MB)\n"
                    "3. Page doesn't have photo posting permissions\n"
                    "4. Access token doesn't have required permissions\n"
                    "5. Facebook API rate limiting\n\n"
                    f"Technical error: {error_msg}"
                )
                raise HTTPException(status_code=400, detail=detailed_error)
            elif "permission" in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Permission error: {error_msg}. Please check your Facebook page permissions."
                )
            elif "token" in error_msg.lower() or "expired" in error_msg.lower():
                # Mark account as disconnected
                page_account.is_connected = False
                db.commit()
                raise HTTPException(
                    status_code=401,
                    detail="Facebook access token expired. Please reconnect your account."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to create post: {error_msg}"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"=== UNEXPECTED ERROR ===")
        logger.error(f"Error creating Facebook post: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


# Instagram Integration
@router.post("/instagram/connect")
async def connect_instagram(
    request: InstagramConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect Instagram Business account through Facebook."""
    try:
        logger.info(f"Instagram connect request for user {current_user.id}")
        
        # Use the new service to get Instagram accounts with proper error handling
        try:
            instagram_accounts = instagram_service.get_facebook_pages_with_instagram(request.access_token)
        except Exception as service_error:
            # The service provides detailed troubleshooting messages
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(service_error)
            )
        
        # Save Instagram accounts to database
        connected_accounts = []
        for ig_account in instagram_accounts:
            # Check if account already exists
            existing_account = db.query(SocialAccount).filter(
                SocialAccount.user_id == current_user.id,
                SocialAccount.platform == "instagram",
                SocialAccount.platform_user_id == ig_account["platform_id"]
            ).first()
            
            if existing_account:
                # Update existing account
                existing_account.username = ig_account["username"]
                existing_account.display_name = ig_account["display_name"] or ig_account["username"]
                existing_account.is_connected = True
                existing_account.last_sync_at = datetime.utcnow()
                existing_account.follower_count = ig_account.get("followers_count", 0)
                existing_account.profile_picture_url = ig_account.get("profile_picture")
                existing_account.platform_data = {
                    "page_id": ig_account.get("page_id"),
                    "page_name": ig_account.get("page_name"),
                    "media_count": ig_account.get("media_count", 0),
                    "page_access_token": ig_account.get("page_access_token")
                }
                existing_account.access_token = ig_account.get("page_access_token")
                db.commit()
                connected_accounts.append(existing_account)
                logger.info(f"Updated existing Instagram account: {ig_account['username']} (ID: {ig_account['platform_id']})")
            else:
                # Create new account  
                ig_account_obj = SocialAccount(
                    user_id=current_user.id,
                    platform="instagram",
                    platform_user_id=ig_account["platform_id"],
                    username=ig_account["username"],
                    display_name=ig_account["display_name"] or ig_account["username"],
                    account_type="business",
                    follower_count=ig_account.get("followers_count", 0),
                    profile_picture_url=ig_account.get("profile_picture"),
                    platform_data={
                        "page_id": ig_account.get("page_id"),
                        "page_name": ig_account.get("page_name"),
                        "media_count": ig_account.get("media_count", 0),
                        "page_access_token": ig_account.get("page_access_token")
                    },
                    access_token=ig_account.get("page_access_token"),
                    is_connected=True,
                    last_sync_at=datetime.utcnow()
                )
                db.add(ig_account_obj)
                db.commit()
                db.refresh(ig_account_obj)
                connected_accounts.append(ig_account_obj)
                logger.info(f"Created new Instagram account: {ig_account['username']} (ID: {ig_account['platform_id']})")
        
        logger.info(f"Instagram connection successful. Connected accounts: {len(connected_accounts)}")
        
        return SuccessResponse(
            message=f"Instagram account(s) connected successfully ({len(connected_accounts)} accounts)",
            data={
                "accounts": [{
                    "platform_id": acc.platform_user_id,
                    "username": acc.username,
                    "display_name": acc.display_name,
                    "page_name": acc.platform_data.get("page_name"),
                    "followers_count": acc.follower_count or 0,
                    "media_count": acc.platform_data.get("media_count", 0),
                    "profile_picture": acc.profile_picture_url
                } for acc in connected_accounts]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Instagram account: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect Instagram account: {str(e)}"
        )


@router.post("/instagram/post")
async def create_instagram_post(
    request: InstagramPostRequest = None,
    instagram_user_id: str = None,
    caption: str = None,
    image_url: str = None,
    post_type: str = "manual",
    use_ai: bool = False,
    prompt: str = None,
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and publish an Instagram post."""
    try:
        # Handle both JSON and FormData requests
        if request:
            # JSON request
            instagram_user_id = request.instagram_user_id
            caption = request.caption
            image_url = request.image_url
            post_type = request.post_type
            use_ai = getattr(request, 'use_ai', False)
            prompt = getattr(request, 'prompt', None)
        else:
            # FormData request - parameters are already available
            pass
        
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instagram account not found"
            )
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page access token not found. Please reconnect your Instagram account."
            )
        
        # Handle file upload if present
        final_image_url = image_url
        if image and image.filename:
            # TODO: Implement file upload to cloud storage (AWS S3, etc.)
            # For now, we'll return an error for file uploads
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File upload not yet implemented. Please use image URL instead."
            )
        
        # Create the post using Instagram service
        if post_type == "post-auto" or use_ai:
            # AI-generated post
            post_result = await instagram_service.create_ai_generated_post(
                instagram_user_id=instagram_user_id,
                access_token=page_access_token,
                prompt=prompt or caption,
                image_url=final_image_url
            )
        else:
            # Manual post
            try:
                post_result = instagram_service.create_post(
                    instagram_user_id=instagram_user_id,
                    page_access_token=page_access_token,
                    caption=caption,
                    image_url=final_image_url
                )
            except Exception as service_error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(service_error)
                )
        
        if not post_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create Instagram post: {post_result.get('error', 'Unknown error')}"
            )
        
        # Save post to database
        post = Post(
            user_id=current_user.id,
            social_account_id=account.id,
            content=post_result.get("generated_caption") or caption,
            post_type=PostType.IMAGE,
            status=PostStatus.PUBLISHED,
            platform_post_id=post_result.get("post_id"),
            published_at=datetime.utcnow(),
            media_urls=[final_image_url] if final_image_url else None
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        return SuccessResponse(
            message="Instagram post created successfully",
            data={
                "post_id": post_result.get("post_id"),
                "database_id": post.id,
                "platform": "instagram",
                "account_username": account.username,
                "ai_generated": post_result.get("ai_generated", False),
                "generated_caption": post_result.get("generated_caption"),
                "original_prompt": post_result.get("original_prompt")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Instagram post: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Instagram post: {str(e)}"
        )


@router.get("/instagram/media/{instagram_user_id}")
async def get_instagram_media(
    instagram_user_id: str,
    limit: int = 25,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Instagram media for a connected account."""
    try:
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instagram account not found"
            )
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page access token not found. Please reconnect your Instagram account."
            )
        
        # Get media from Instagram API using new service
        media_items = instagram_service.get_user_media(
            instagram_user_id=instagram_user_id,
            page_access_token=page_access_token,
            limit=limit
        )
        
        return SuccessResponse(
            message=f"Retrieved {len(media_items)} media items",
            data={
                "media": media_items,
                "account_username": account.username,
                "total_items": len(media_items)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Instagram media: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Instagram media: {str(e)}"
        )


@router.post("/instagram/generate-image")
async def generate_instagram_image(
    request: InstagramImageGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate an image for Instagram using Stability AI."""
    try:
        from app.services.instagram_service import instagram_service
        from app.services.cloudinary_service import cloudinary_service
        
        logger.info(f"Generating Instagram image with prompt: {request.image_prompt}")
        
        # Generate image using Instagram-optimized Stability AI
        image_result = await instagram_service.generate_instagram_image_with_ai(
            prompt=request.image_prompt,
            post_type=request.post_type
        )
        
        if not image_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Image generation failed: {image_result.get('error', 'Unknown error')}"
            )
        
        # Upload to Cloudinary with Instagram-specific transforms
        upload_result = cloudinary_service.upload_image_with_instagram_transform(
            f"data:image/png;base64,{image_result['image_base64']}"
        )
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Image upload failed: {upload_result.get('error', 'Unknown error')}"
            )
        
        return SuccessResponse(
            message="Instagram image generated successfully",
            data={
                "image_url": upload_result["url"],
                "filename": f"instagram_generated_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg",
                "prompt": request.image_prompt,
                "enhanced_prompt": image_result.get("enhanced_prompt"),
                "post_type": request.post_type,
                "width": image_result.get("width"),
                "height": image_result.get("height")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Instagram image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Instagram image: {str(e)}"
        )


@router.post("/instagram/upload-image")
async def upload_instagram_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload an image for Instagram using Cloudinary with Instagram-specific transforms."""
    try:
        from app.services.cloudinary_service import cloudinary_service
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Cloudinary with Instagram-specific transforms
        upload_result = cloudinary_service.upload_image_with_instagram_transform(file_content)
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Image upload failed: {upload_result.get('error', 'Unknown error')}"
            )
        
        return SuccessResponse(
            message="Image uploaded successfully for Instagram",
            data={
                "url": upload_result["url"],
                "filename": file.filename,
                "size": len(file_content)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading Instagram image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload Instagram image: {str(e)}"
        )


@router.post("/instagram/upload-video")
async def upload_instagram_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a video for Instagram - saves to disk and uploads to Cloudinary."""
    try:
        from app.services.cloudinary_service import cloudinary_service
        import os
        
        # Validate file type
        if not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=400,
                detail="Only video files are allowed"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Create temp_images directory if it doesn't exist
        os.makedirs("temp_images", exist_ok=True)
        
        # Save file to temp_images directory for later use (like Facebook service)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1], dir="temp_images") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Get just the filename for database storage
        saved_filename = os.path.basename(temp_file_path)
        
        logger.info(f"Video file saved to disk: {temp_file_path}")
        logger.info(f"File size: {len(file_content)} bytes")
        logger.info(f"Saved filename: {saved_filename}")
        
        # Upload to Cloudinary with Instagram-specific transforms
        upload_result = cloudinary_service.upload_video_with_instagram_transform(file_content)
        
        if not upload_result["success"]:
            # Clean up temp file if upload failed
            try:
                os.unlink(temp_file_path)
                logger.warning(f"Cleaned up temp file after failed upload: {temp_file_path}")
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Video upload failed: {upload_result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Video uploaded to Cloudinary successfully: {upload_result['url']}")
        
        return SuccessResponse(
            message="Video uploaded successfully for Instagram",
            data={
                "url": upload_result["url"],  # Cloudinary URL for immediate use
                "filename": saved_filename,   # Saved filename for later file-based posting
                "original_filename": file.filename,
                "size": len(file_content),
                "cloudinary_url": upload_result["url"],
                "file_path": temp_file_path  # Full path for backend use
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading Instagram video: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload Instagram video: {str(e)}"
        )


@router.post("/instagram/generate-caption")
async def generate_instagram_caption(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Generate Instagram caption using AI."""
    try:
        from app.services.groq_service import groq_service
        
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt is required for caption generation"
            )
        
        result = await groq_service.generate_instagram_post(prompt)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Caption generation failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "content": result["content"],
            "prompt": prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Instagram caption: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate caption: {str(e)}"
        )


@router.post("/instagram/generate-carousel")
async def generate_instagram_carousel(
    request: InstagramCarouselGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate Instagram carousel images using AI."""
    try:
        result = await instagram_service.generate_carousel_images_with_ai(
            prompt=request.image_prompt,
            count=request.count,
            post_type=request.post_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Carousel generation failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "image_urls": result["image_urls"],
            "caption": result["caption"],
            "count": result["count"],
            "prompt": result["prompt"],
            "width": result["width"],
            "height": result["height"],
            "post_type": result["post_type"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Instagram carousel: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate carousel: {str(e)}"
        )


@router.post("/instagram/post-carousel")
async def create_instagram_carousel_post(
    request: InstagramCarouselPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an Instagram carousel post."""
    try:
        logger.info(f"Starting Instagram carousel post creation for user {current_user.id}")
        logger.info(f"Request data: instagram_user_id={request.instagram_user_id}, caption_length={len(request.caption)}, image_count={len(request.image_urls)}")
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == request.instagram_user_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instagram account not found"
            )
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page access token not found. Please reconnect your Instagram account."
            )
        
        # Create the carousel post
        result = await instagram_service.create_carousel_post(
            instagram_user_id=request.instagram_user_id,
            page_access_token=page_access_token,
            caption=request.caption,
            image_urls=request.image_urls
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create carousel post: {result.get('error', 'Unknown error')}"
            )
        
        # Save post to database
        post = Post(
            user_id=current_user.id,
            social_account_id=account.id,
            content=request.caption,
            post_type=PostType.CAROUSEL,
            status=PostStatus.PUBLISHED,
            platform_post_id=result.get("post_id"),
            published_at=datetime.utcnow(),
            media_urls=request.image_urls
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        return SuccessResponse(
            message="Instagram carousel post created successfully",
            data={
                "post_id": result.get("post_id"),
                "database_id": post.id,
                "platform": "instagram",
                "account_username": account.username,
                "caption": request.caption,
                "image_count": len(request.image_urls),
                "media_type": "carousel"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Instagram carousel post: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create carousel post: {str(e)}"
        )


@router.post("/instagram/create-post")
async def create_unified_instagram_post(
    request: UnifiedInstagramPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("=== API: /instagram/create-post endpoint called ===")
    print("Incoming Instagram post request:", request.dict())
    """Create an Instagram post with unified options (AI generation, file upload, etc.)."""
    try:
        # Debug logging
        logger.info(f"Received Instagram post request: {request}")
        logger.info(f"Request data: instagram_user_id={request.instagram_user_id}, "
                   f"caption={request.caption}, image_url={request.image_url}, "
                   f"video_url={request.video_url}, video_filename={request.video_filename}, "
                   f"media_type={request.media_type}")
        logger.info(f"Post type determination: media_type='{request.media_type}', "
                   f"has_video_url={bool(request.video_url)}, has_image_url={bool(request.image_url)}")
        
        # ADDITIONAL DEBUG: Check if this is a reel post
        if request.video_url:
            logger.info(f"🎬 REEL POST DETECTED: video_url present = {request.video_url[:100]}...")
        if request.media_type == "video":
            logger.info(f"🎬 REEL POST DETECTED: media_type='video'")
        if request.video_url and request.media_type == "video":
            logger.info(f"🎬 CONFIRMED REEL POST: Both video_url and media_type='video' present")
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == request.instagram_user_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instagram account not found"
            )
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page access token not found. Please reconnect your Instagram account."
            )
        
        # Initialize variables
        final_caption = request.caption
        final_image_url = request.image_url
        final_video_url = request.video_url
        final_video_file_path = None
        final_video_filename = request.video_filename
        
        # Handle video file path if provided
        if request.video_filename:
            # Convert filename to full path (assuming files are stored in temp_images directory)
            import os
            final_video_file_path = os.path.join("temp_images", request.video_filename)
            if not os.path.exists(final_video_file_path):
                logger.warning(f"Video file not found at path: {final_video_file_path}")
                final_video_file_path = None
        
        # Step 1: Generate AI text content if requested
        if request.use_ai_text and request.content_prompt:
            logger.info("Generating AI text content for Instagram post")
            from app.services.groq_service import groq_service
            
            ai_text_result = await groq_service.generate_instagram_post(request.content_prompt)
            if ai_text_result["success"]:
                final_caption = ai_text_result["content"]
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"AI text generation failed: {ai_text_result.get('error', 'Unknown error')}"
                )
        
        # Step 2: Generate AI image if requested
        if request.use_ai_image and request.image_prompt:
            logger.info("Generating AI image for Instagram post")
            from app.services.stability_service import stability_service
            from app.services.cloudinary_service import cloudinary_service
            
            image_result = await stability_service.generate_image(request.image_prompt)
            if image_result["success"]:
                upload_result = cloudinary_service.upload_image_with_instagram_transform(
                    f"data:image/png;base64,{image_result['image_base64']}"
                )
                if upload_result["success"]:
                    final_image_url = upload_result["url"]
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Image upload failed: {upload_result.get('error', 'Unknown error')}"
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Image generation failed: {image_result.get('error', 'Unknown error')}"
                )
        
        # Step 3: Create the Instagram post
        # Determine if this is a Reel post
        is_reel = (
            getattr(request, 'is_reel', False)
            or (hasattr(request, 'media_type') and str(request.media_type).upper() == 'REELS')
            or (hasattr(request, 'media_type') and str(request.media_type).lower() == 'video')
        )
        post_result = await instagram_service.create_post(
            instagram_user_id=request.instagram_user_id,
            page_access_token=account.access_token,
            caption=final_caption,
            image_url=final_image_url,
            video_url=final_video_url,
            video_file_path=final_video_file_path,
            video_filename=final_video_filename,
            is_reel=is_reel,
            thumbnail_url=getattr(request, 'thumbnail_url', None),
            thumbnail_filename=getattr(request, 'thumbnail_filename', None)
        )
        
        if not post_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Instagram post: {post_result.get('error', 'Unknown error')}"
            )
        
        # Determine post type based on media type and content
        logger.info(f"=== POST TYPE DETERMINATION DEBUG ===")
        logger.info(f"request.media_type: '{request.media_type}'")
        logger.info(f"final_video_url exists: {bool(final_video_url)}")
        logger.info(f"final_video_file_path exists: {bool(final_video_file_path)}")
        logger.info(f"final_image_url exists: {bool(final_image_url)}")
        if final_video_url:
            logger.info(f"final_video_url preview: {final_video_url[:100]}...")
        if final_image_url:
            logger.info(f"final_image_url preview: {final_image_url[:100]}...")
        
        # Determine post type based on media type and content
        if getattr(request, "is_reel", False) or (hasattr(request, "media_type") and request.media_type == "REELS"):
            post_type = PostType.REEL
            logger.info("Setting post type to REEL for media_type='REELS' or is_reel=True")
        elif final_video_url or final_video_file_path:
            post_type = PostType.VIDEO
            logger.info("Setting post type to VIDEO because video_url or video_file_path is present")
        elif final_image_url:
            post_type = PostType.IMAGE
            logger.info("Setting post type to IMAGE because image_url is present")
        else:
            post_type = PostType.TEXT
            logger.info("Setting post type to TEXT (default)")
        
        # ADDITIONAL SAFETY CHECK: If we have video_url or video_file_path, ALWAYS set to VIDEO
        if (final_video_url or final_video_file_path) and post_type != PostType.VIDEO:
            logger.warning(f"⚠️ OVERRIDING: Found video content but post_type was {post_type}, forcing to VIDEO")
            post_type = PostType.VIDEO
        
        # FINAL SAFETY CHECK: If media_type is "video", ALWAYS set to VIDEO
        if request.media_type == "video" and post_type != PostType.VIDEO:
            logger.warning(f"⚠️ OVERRIDING: media_type='video' but post_type was {post_type}, forcing to VIDEO")
            post_type = PostType.VIDEO
        
        logger.info(f"Final post_type determined: {post_type}")
        logger.info(f"=== END POST TYPE DETERMINATION DEBUG ===")
        
        # Save post to database
        logger.info(f"💾 SAVING TO DATABASE: post_type={post_type}, media_urls={[final_image_url] if final_image_url else ([final_video_url] if final_video_url else None)}")
        
        post = Post(
            user_id=current_user.id,
            social_account_id=account.id,
            content=final_caption,
            post_type=post_type,
            status=PostStatus.PUBLISHED,
            platform_post_id=post_result.get("post_id"),
            published_at=datetime.utcnow(),
            media_urls=[final_image_url] if final_image_url else ([final_video_url] if final_video_url else None)
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        logger.info(f"✅ DATABASE SAVE COMPLETE: post.id={post.id}, post.post_type={post.post_type}")
        
        return SuccessResponse(
            message="Instagram post created successfully",
            data={
                "post_id": post_result.get("post_id"),
                "database_id": post.id,
                "platform": "instagram",
                "account_username": account.username,
                "caption": final_caption,
                "media_type": request.media_type,
                "ai_generated_text": request.use_ai_text,
                "ai_generated_image": request.use_ai_image
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating unified Instagram post: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Instagram post: {str(e)}"
        )


# Post Management
@router.get("/posts", response_model=List[PostResponse])
async def get_posts(
    platform: Optional[str] = None,
    status: Optional[PostStatus] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's posts with optional filtering."""
    query = db.query(Post).filter(Post.user_id == current_user.id)
    
    if platform:
        query = query.join(SocialAccount).filter(SocialAccount.platform == platform)
    
    if status:
        query = query.filter(Post.status == status)
    
    posts = query.order_by(Post.created_at.desc()).limit(limit).all()
    return posts


@router.post("/posts", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new social media post."""
    # Verify user owns the social account
    account = db.query(SocialAccount).filter(
        SocialAccount.id == post_data.social_account_id,
        SocialAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found"
        )
    
    post = Post(
        user_id=current_user.id,
        social_account_id=post_data.social_account_id,
        content=post_data.content,
        post_type=post_data.post_type,
        link_url=post_data.link_url,
        hashtags=post_data.hashtags,
        media_urls=post_data.media_urls,
        scheduled_at=post_data.scheduled_at,
        status=PostStatus.SCHEDULED if post_data.scheduled_at else PostStatus.DRAFT
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return post


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a post."""
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Update fields
    if post_data.content is not None:
        post.content = post_data.content
    if post_data.scheduled_at is not None:
        post.scheduled_at = post_data.scheduled_at
    if post_data.status is not None:
        post.status = post_data.status
    
    db.commit()
    db.refresh(post)
    
    return post


# Automation Rules Management
@router.get("/automation-rules", response_model=List[AutomationRuleResponse])
async def get_automation_rules(
    platform: Optional[str] = None,
    rule_type: Optional[RuleType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's automation rules."""
    query = db.query(AutomationRule).filter(AutomationRule.user_id == current_user.id)
    
    if platform:
        query = query.join(SocialAccount).filter(SocialAccount.platform == platform)
    
    if rule_type:
        query = query.filter(AutomationRule.rule_type == rule_type)
    
    rules = query.order_by(AutomationRule.created_at.desc()).all()
    return rules


@router.post("/automation-rules", response_model=AutomationRuleResponse)
async def create_automation_rule(
    rule_data: AutomationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new automation rule."""
    # Verify user owns the social account
    account = db.query(SocialAccount).filter(
        SocialAccount.id == rule_data.social_account_id,
        SocialAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found"
        )
    
    rule = AutomationRule(
        user_id=current_user.id,
        social_account_id=rule_data.social_account_id,
        name=rule_data.name,
        description=rule_data.description,
        rule_type=rule_data.rule_type,
        trigger_type=rule_data.trigger_type,
        trigger_conditions=rule_data.trigger_conditions,
        actions=rule_data.actions,
        daily_limit=rule_data.daily_limit,
        active_hours_start=rule_data.active_hours_start,
        active_hours_end=rule_data.active_hours_end,
        active_days=rule_data.active_days
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.put("/automation-rules/{rule_id}", response_model=AutomationRuleResponse)
async def update_automation_rule(
    rule_id: int,
    rule_data: AutomationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an automation rule."""
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.user_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation rule not found"
        )
    
    # Update fields
    if rule_data.name is not None:
        rule.name = rule_data.name
    if rule_data.description is not None:
        rule.description = rule_data.description
    if rule_data.trigger_conditions is not None:
        rule.trigger_conditions = rule_data.trigger_conditions
    if rule_data.actions is not None:
        rule.actions = rule_data.actions
    if rule_data.is_active is not None:
        rule.is_active = rule_data.is_active
    if rule_data.daily_limit is not None:
        rule.daily_limit = rule_data.daily_limit
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/automation-rules/{rule_id}")
async def delete_automation_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an automation rule."""
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.user_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation rule not found"
        )
    
    db.delete(rule)
    db.commit()
    
    return SuccessResponse(message="Automation rule deleted successfully")


# Debug endpoint for troubleshooting Facebook connections
@router.get("/debug/facebook-accounts")
async def debug_facebook_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to see all Facebook accounts for current user."""
    facebook_accounts = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.platform == "facebook"
    ).all()
    
    return {
        "user_id": current_user.id,
        "total_facebook_accounts": len(facebook_accounts),
        "accounts": [{
            "id": acc.id,
            "platform_user_id": acc.platform_user_id,
            "username": acc.username,
            "display_name": acc.display_name,
            "account_type": acc.account_type,
            "is_connected": acc.is_connected,
            "follower_count": acc.follower_count,
            "profile_picture_url": acc.profile_picture_url,
            "platform_data": acc.platform_data,
            "last_sync_at": acc.last_sync_at,
            "connected_at": acc.connected_at
        } for acc in facebook_accounts]
    }


# Scheduled Posts Endpoints
@router.get("/scheduled-posts")
async def get_scheduled_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scheduled posts for the current user."""
    scheduled_posts = db.query(ScheduledPost).filter(
        ScheduledPost.user_id == current_user.id
    ).all()
    
    return [{
        "id": post.id,
        "prompt": post.prompt,
        "post_time": post.post_time,
        "frequency": post.frequency.value,
        "is_active": post.is_active,
        "last_executed": post.last_executed.isoformat() if post.last_executed else None,
        "next_execution": post.next_execution.isoformat() if post.next_execution else None,
        "social_account": {
            "id": post.social_account.id,
            "platform": post.social_account.platform,
            "display_name": post.social_account.display_name
        } if post.social_account else None,
        "created_at": post.created_at.isoformat() if post.created_at else None
    } for post in scheduled_posts]


@router.post("/scheduled-posts")
async def create_scheduled_post(
    prompt: str,
    post_time: str,
    frequency: str = "daily",
    social_account_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scheduled post."""
    try:
        # Validate frequency
        if frequency not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid frequency. Must be 'daily', 'weekly', or 'monthly'"
            )
        
        # If no social account specified, find the first Facebook account
        if not social_account_id:
            facebook_account = db.query(SocialAccount).filter(
                SocialAccount.user_id == current_user.id,
                SocialAccount.platform == "facebook",
                SocialAccount.is_connected == True
            ).first()
            
            if not facebook_account:
                raise HTTPException(
                    status_code=400,
                    detail="No connected Facebook account found"
                )
            social_account_id = facebook_account.id
        
        # Check if there's already an active schedule for this social account
        existing_active = db.query(ScheduledPost).filter(
            ScheduledPost.user_id == current_user.id,
            ScheduledPost.social_account_id == social_account_id,
            ScheduledPost.is_active == True
        ).first()
        
        if existing_active:
            raise HTTPException(
                status_code=400,
                detail=f"An active schedule already exists for this account. Please deactivate the existing schedule first."
            )
        
        # Calculate next execution time
        from datetime import datetime, timedelta
        
        try:
            time_parts = post_time.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use HH:MM"
            )
        
        now = datetime.utcnow()
        next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the time has already passed today, schedule for next occurrence
        if next_exec <= now:
            if frequency == "daily":
                # For testing: if time passed today, schedule for next occurrence
                next_exec += timedelta(days=1)
            elif frequency == "weekly":
                next_exec += timedelta(weeks=1)
            elif frequency == "monthly":
                next_exec += timedelta(days=30)
        
        # FOR TESTING: If scheduled time is more than 2 hours away, set it to 1 minute from now
        time_diff = next_exec - now
        if time_diff.total_seconds() > 7200:  # More than 2 hours
            logger.info(f"Scheduled time is {time_diff.total_seconds()/3600:.1f} hours away, setting to 1 minute for testing")
            next_exec = now + timedelta(minutes=1)
        
        # Create scheduled post
        scheduled_post = ScheduledPost(
            user_id=current_user.id,
            social_account_id=social_account_id,
            prompt=prompt,
            post_time=post_time,
            frequency=FrequencyType(frequency),
            is_active=True,
            next_execution=next_exec
        )
        
        db.add(scheduled_post)
        db.commit()
        db.refresh(scheduled_post)
        
        logger.info(f"Created scheduled post {scheduled_post.id} for user {current_user.id}")
        
        return SuccessResponse(
            message="Scheduled post created successfully",
            data={
                "id": scheduled_post.id,
                "prompt": scheduled_post.prompt,
                "post_time": scheduled_post.post_time,
                "frequency": scheduled_post.frequency.value,
                "next_execution": scheduled_post.next_execution.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scheduled post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create scheduled post"
        )


@router.delete("/scheduled-posts/{schedule_id}")
async def delete_scheduled_post(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scheduled post."""
    try:
        # Find the scheduled post
        scheduled_post = db.query(ScheduledPost).filter(
            ScheduledPost.id == schedule_id,
            ScheduledPost.user_id == current_user.id
        ).first()
        
        if not scheduled_post:
            raise HTTPException(
                status_code=404,
                detail="Scheduled post not found"
            )
        
        # Delete the scheduled post
        db.delete(scheduled_post)
        db.commit()
        
        logger.info(f"Deleted scheduled post {schedule_id} for user {current_user.id}")
        
        return SuccessResponse(
            message="Scheduled post deleted successfully",
            data={"deleted_id": schedule_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled post {schedule_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete scheduled post"
        )


@router.put("/scheduled-posts/{schedule_id}/deactivate")
async def deactivate_scheduled_post(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a scheduled post (set is_active to False)."""
    try:
        # Find the scheduled post
        scheduled_post = db.query(ScheduledPost).filter(
            ScheduledPost.id == schedule_id,
            ScheduledPost.user_id == current_user.id
        ).first()
        
        if not scheduled_post:
            raise HTTPException(
                status_code=404,
                detail="Scheduled post not found"
            )
        
        # Deactivate the scheduled post
        scheduled_post.is_active = False
        db.commit()
        
        logger.info(f"Deactivated scheduled post {schedule_id} for user {current_user.id}")
        
        return SuccessResponse(
            message="Scheduled post deactivated successfully",
            data={
                "id": scheduled_post.id,
                "is_active": False
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating scheduled post {schedule_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to deactivate scheduled post"
        )


@router.post("/scheduled-posts/trigger")
async def trigger_scheduler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger the scheduler to check for due posts (for testing)."""
    try:
        from app.services.scheduler_service import scheduler_service
        
        # Manually process scheduled posts
        await scheduler_service.process_scheduled_posts()
        
        # Get updated scheduled posts
        scheduled_posts = db.query(ScheduledPost).filter(
            ScheduledPost.user_id == current_user.id
        ).all()
        
        return SuccessResponse(
            message="Scheduler triggered successfully",
            data={
                "processed_at": datetime.utcnow().isoformat(),
                "total_scheduled_posts": len(scheduled_posts),
                "active_schedules": len([p for p in scheduled_posts if p.is_active])
            }
        )
        
    except Exception as e:
        logger.error(f"Error triggering scheduler: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger scheduler"
        )


@router.get("/debug/stability-ai-status")
async def debug_stability_ai_status(
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check Stability AI service status."""
    try:
        from app.services.fb_stability_service import stability_service
        from app.services.image_service import image_service
        import os
        from pathlib import Path
        
        result = {
            "stability_configured": stability_service.is_configured(),
            "temp_images_dir_exists": Path("temp_images").exists(),
            "temp_images_writable": os.access("temp_images", os.W_OK) if Path("temp_images").exists() else False,
            "temp_images_files": []
        }
        
        # List files in temp_images directory
        if Path("temp_images").exists():
            try:
                result["temp_images_files"] = [f.name for f in Path("temp_images").iterdir() if f.is_file()][-10:]  # Last 10 files
            except Exception as e:
                result["temp_images_error"] = str(e)
        
        # Test a simple image generation if configured
        if stability_service.is_configured():
            try:
                test_result = await stability_service.generate_image(
                    prompt="A simple test image",
                    width=512,
                    height=512,
                    steps=10  # Quick generation
                )
                result["test_generation"] = {
                    "success": test_result["success"],
                    "error": test_result.get("error") if not test_result["success"] else None
                }
                
                # If generation worked, try saving the image
                if test_result["success"]:
                    save_result = image_service.save_base64_image(
                        base64_data=test_result["image_base64"],
                        filename="debug_test_image.png"
                    )
                    result["test_save"] = {
                        "success": save_result["success"],
                        "error": save_result.get("error") if not save_result["success"] else None,
                        "file_path": save_result.get("file_path")
                    }
                    
            except Exception as e:
                result["test_generation"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Debug stability AI status error: {e}")
        return {
            "error": str(e)
        }


@router.get("/debug/instagram-stability-status")
async def debug_instagram_stability_status(
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check Instagram Stability AI configuration."""
    try:
        from app.services.stability_service import stability_service
        import os
        
        # Check Instagram Stability service
        configured = stability_service.is_configured()
        api_key = stability_service.api_key
        
        key_info = "Configured" if api_key else "Not configured"
        if api_key:
            key_info += f" (starts with: {api_key[:10]}...)"
        
        # Test the API key with a simple request
        test_result = None
        if configured:
            try:
                test_result = await stability_service.generate_image("test")
                test_status = "Success" if test_result.get("success") else f"Failed: {test_result.get('error', 'Unknown error')}"
            except Exception as e:
                test_status = f"Exception: {str(e)}"
        else:
            test_status = "Not configured"
        
        return {
            "instagram_stability_service": {
                "configured": configured,
                "api_key_status": key_info,
                "test_result": test_status
            },
            "environment_variable": {
                "STABILITY_API_KEY_set": bool(os.getenv("STABILITY_API_KEY")),
                "value_preview": os.getenv("STABILITY_API_KEY", "")[:10] + "..." if os.getenv("STABILITY_API_KEY") else "Not set"
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking Instagram Stability AI status: {e}")
        return {
            "error": str(e)
        }


@router.post("/debug/test-facebook-image-post")
async def debug_test_facebook_image_post(
    page_id: str,
    test_message: str = "Test post from debug endpoint",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint for testing Facebook image posts."""
    try:
        from app.services.facebook_service import facebook_service
        
        logger.info(f"Debug: Testing Facebook image post for user {current_user.id}")
        
        # Get page account
        page_account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.platform_user_id == page_id,
            SocialAccount.is_connected == True
        ).first()
        
        if not page_account:
            return {
                "success": False,
                "error": "Page not found or not connected"
            }
        
        # Generate a test image
        result = await facebook_service.generate_and_post_image(
            page_id=page_id,
            access_token=page_account.access_token,
            image_prompt="a simple test image with bright colors",
            text_content=test_message,
            post_type="feed"
        )
        
        return {
            "success": result["success"],
            "data": result if result["success"] else {"error": result.get("error")}
        }
        
    except Exception as e:
        logger.error(f"Debug test error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/debug/imgbb-test")
async def debug_imgbb_test(
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to test IMGBB upload functionality."""
    try:
        from app.services.image_service import image_service
        from app.config import get_settings
        import base64
        
        settings = get_settings()
        
        # Check if IMGBB is configured
        if not settings.imgbb_api_key:
            return {
                "success": False,
                "error": "IMGBB_API_KEY not configured",
                "imgbb_configured": False
            }
        
        # Create a simple test image (1x1 pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAWqemowAAAABJRU5ErkJggg=="
        
        # Test IMGBB upload
        result = image_service.save_base64_image(
            base64_data=test_image_b64,
            filename="debug_test.png",
            format="png"
        )
        
        return {
            "success": result["success"],
            "imgbb_configured": True,
            "imgbb_api_key_length": len(settings.imgbb_api_key) if settings.imgbb_api_key else 0,
            "upload_result": result
        }
        
    except Exception as e:
        logger.error(f"IMGBB debug test error: {e}")
        return {
            "success": False,
            "error": str(e),
            "imgbb_configured": bool(get_settings().imgbb_api_key)
        }


@router.post("/debug/simple-facebook-test")
async def debug_simple_facebook_test(
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simple debug endpoint to test Facebook posting directly."""
    try:
        from app.services.facebook_service import facebook_service
        
        logger.info(f"=== SIMPLE FACEBOOK TEST ===")
        
        # Get page account
        page_account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "facebook",
            SocialAccount.platform_user_id == page_id,
            SocialAccount.is_connected == True
        ).first()
        
        if not page_account:
            return {
                "success": False,
                "error": "Page not found or not connected"
            }
        
        logger.info(f"Found page: {page_account.display_name}")
        logger.info(f"Access token: {page_account.access_token[:20]}..." if page_account.access_token else "None")
        
        # Test 1: Simple text post
        logger.info("Test 1: Simple text post")
        text_result = await facebook_service.create_post(
            page_id=page_id,
            access_token=page_account.access_token,
            message="Test post from debug endpoint - " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            media_type="text"
        )
        
        logger.info(f"Text post result: {text_result}")
        
        # Test 2: Image post with a simple test image
        logger.info("Test 2: Image post with test image")
        
        # Create a simple test image URL (using a public placeholder)
        test_image_url = "https://via.placeholder.com/800x600/FF0000/FFFFFF?text=Test+Image"
        
        image_result = await facebook_service.create_post(
            page_id=page_id,
            access_token=page_account.access_token,
            message="Test image post from debug endpoint - " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            media_url=test_image_url,
            media_type="photo"
        )
        
        logger.info(f"Image post result: {image_result}")
        
        return {
            "success": True,
            "tests": {
                "text_post": text_result,
                "image_post": image_result
            },
            "page_info": {
                "id": page_account.id,
                "name": page_account.display_name,
                "platform_id": page_account.platform_user_id,
                "has_token": bool(page_account.access_token)
            }
        }
        
    except Exception as e:
        logger.error(f"Simple test error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/debug/instagram-accounts")
async def debug_instagram_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to see all Instagram accounts for current user."""
    instagram_accounts = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.platform == "instagram"
    ).all()
    
    return {
        "user_id": current_user.id,
        "total_instagram_accounts": len(instagram_accounts),
        "accounts": [{
            "id": acc.id,
            "platform_user_id": acc.platform_user_id,
            "username": acc.username,
            "display_name": acc.display_name,
            "account_type": acc.account_type,
            "is_connected": acc.is_connected,
            "follower_count": acc.follower_count,
            "profile_picture_url": acc.profile_picture_url,
            "platform_data": acc.platform_data,
            "last_sync_at": acc.last_sync_at,
            "connected_at": acc.connected_at
        } for acc in instagram_accounts]
    }


@router.get("/instagram/posts-for-auto-reply/{instagram_user_id}")
async def get_instagram_posts_for_auto_reply(
    instagram_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get posts from this app for Instagram auto-reply selection."""
    try:
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            # Provide more helpful error message
            all_instagram_accounts = db.query(SocialAccount).filter(
                SocialAccount.user_id == current_user.id,
                SocialAccount.platform == "instagram"
            ).all()
            
            available_accounts = [acc.platform_user_id for acc in all_instagram_accounts]
            
            error_detail = f"Instagram account with ID '{instagram_user_id}' not found for current user. "
            if available_accounts:
                error_detail += f"Available Instagram accounts: {available_accounts}. "
            else:
                error_detail += "No Instagram accounts found. Please connect your Instagram account first."
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_detail
            )
        
        # Get posts created by this app for this account
        posts = db.query(Post).filter(
            Post.social_account_id == account.id,
            Post.status.in_([PostStatus.PUBLISHED, PostStatus.SCHEDULED])
        ).order_by(Post.created_at.desc()).limit(50).all()
        
        # Format posts for frontend
        formatted_posts = []
        for post in posts:
            formatted_posts.append({
                "id": post.id,
                "instagram_post_id": post.platform_post_id,
                "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "full_content": post.content,
                "created_at": post.created_at.isoformat(),
                "status": post.status.value,
                "has_media": bool(post.media_urls),
                "media_count": len(post.media_urls) if post.media_urls else 0
            })
        
        return {
            "success": True,
            "posts": formatted_posts,
            "total_count": len(formatted_posts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get posts for auto-reply: {str(e)}"
        )


@router.post("/instagram/auto-reply")
async def toggle_instagram_auto_reply(
    request: InstagramAutoReplyToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle auto-reply for Instagram account with AI integration and post selection."""
    try:
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == request.instagram_user_id
        ).first()
        
        if not account:
            # Provide more helpful error message
            all_instagram_accounts = db.query(SocialAccount).filter(
                SocialAccount.user_id == current_user.id,
                SocialAccount.platform == "instagram"
            ).all()
            
            available_accounts = [acc.platform_user_id for acc in all_instagram_accounts]
            
            error_detail = f"Instagram account with ID '{request.instagram_user_id}' not found for current user. "
            if available_accounts:
                error_detail += f"Available Instagram accounts: {available_accounts}. "
            else:
                error_detail += "No Instagram accounts found. Please connect your Instagram account first."
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_detail
            )
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page access token not found. Please reconnect your Instagram account."
            )
        
        # Validate selected posts if any
        selected_posts = []
        if request.selected_post_ids:
            posts = db.query(Post).filter(
                Post.id.in_(request.selected_post_ids),
                Post.social_account_id == account.id
            ).all()
            # Get the Instagram post IDs (platform_post_id) for the selected posts
            selected_posts = [post.platform_post_id for post in posts if post.platform_post_id]
            
            logger.info(f"Selected posts: {request.selected_post_ids}")
            logger.info(f"Instagram post IDs: {selected_posts}")
            logger.info(f"Found posts in DB: {[post.id for post in posts]}")
            logger.info(f"Platform post IDs: {[post.platform_post_id for post in posts]}")
        else:
            logger.info("No selected post IDs in request")
        
        # Use Instagram service to setup auto-reply
        instagram_result = await instagram_service.setup_auto_reply(
            instagram_user_id=request.instagram_user_id,
            page_access_token=page_access_token,
            enabled=request.enabled,
            template=request.response_template
        )
        
        # Find or create auto-reply rule in database
        auto_reply_rule = db.query(AutomationRule).filter(
            AutomationRule.user_id == current_user.id,
            AutomationRule.social_account_id == account.id,
            AutomationRule.rule_type == RuleType.AUTO_REPLY
        ).first()
        
        if auto_reply_rule:
            # Update existing rule
            auto_reply_rule.is_active = request.enabled
            rule_actions = {
                "response_template": request.response_template,
                "ai_enabled": True,
                "instagram_setup": instagram_result,
                "selected_post_ids": request.selected_post_ids,
                "selected_instagram_post_ids": selected_posts
            }
            auto_reply_rule.actions = rule_actions
            logger.info(f"🔄 Updated existing Instagram rule {auto_reply_rule.id} with actions: {rule_actions}")
        else:
            # Create new auto-reply rule
            rule_actions = {
                "response_template": request.response_template,
                "ai_enabled": True,
                "instagram_setup": instagram_result,
                "selected_post_ids": request.selected_post_ids,
                "selected_instagram_post_ids": selected_posts
            }
            auto_reply_rule = AutomationRule(
                user_id=current_user.id,
                social_account_id=account.id,
                name=f"Instagram Auto Reply - {account.display_name}",
                rule_type=RuleType.AUTO_REPLY,
                trigger_type=TriggerType.ENGAGEMENT_BASED,
                trigger_conditions={
                    "event": "comment",
                    "platform": "instagram",
                    "selected_posts": selected_posts
                },
                actions=rule_actions,
                is_active=request.enabled
            )
            db.add(auto_reply_rule)
            logger.info(f"🆕 Created new Instagram rule with actions: {rule_actions}")
        
        db.commit()
        logger.info(f"💾 Committed Instagram rule to database. Rule ID: {auto_reply_rule.id}")
        logger.info(f"💾 Final Instagram rule actions: {auto_reply_rule.actions}")
        
        return SuccessResponse(
            message=f"Instagram auto-reply {'enabled' if request.enabled else 'disabled'} successfully with AI integration",
            data={
                "rule_id": auto_reply_rule.id,
                "enabled": request.enabled,
                "ai_enabled": True,
                "account_username": account.username,
                "instagram_setup": instagram_result,
                "selected_posts_count": len(selected_posts),
                "selected_post_ids": request.selected_post_ids
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to toggle Instagram auto-reply: {str(e)}"
        )


@router.get("/debug/instagram-auto-reply-status")
async def debug_instagram_auto_reply_status(
    instagram_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check Instagram auto-reply configuration."""
    try:
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            return {
                "success": False,
                "error": "Instagram account not found"
            }
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        
        # Check for existing auto-reply rules
        auto_reply_rules = db.query(AutomationRule).filter(
            AutomationRule.user_id == current_user.id,
            AutomationRule.social_account_id == account.id,
            AutomationRule.rule_type == RuleType.AUTO_REPLY
        ).all()
        
        # Test Instagram API connection
        test_result = None
        if page_access_token:
            try:
                # Test getting recent media
                media_result = await instagram_service.get_comments(
                    instagram_user_id=instagram_user_id,
                    page_access_token=page_access_token,
                    limit=5
                )
                test_result = {
                    "success": True,
                    "media_count": len(media_result),
                    "sample_media": media_result[:2] if media_result else []
                }
            except Exception as e:
                test_result = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "account_info": {
                "id": account.id,
                "username": account.username,
                "display_name": account.display_name,
                "platform_user_id": account.platform_user_id,
                "has_page_token": bool(page_access_token),
                "page_token_length": len(page_access_token) if page_access_token else 0
            },
            "auto_reply_rules": [{
                "id": rule.id,
                "name": rule.name,
                "is_active": rule.is_active,
                "actions": rule.actions,
                "created_at": rule.created_at.isoformat() if rule.created_at else None
            } for rule in auto_reply_rules],
            "api_test": test_result,
            "total_rules": len(auto_reply_rules),
            "active_rules": len([r for r in auto_reply_rules if r.is_active])
        }
        
    except Exception as e:
        logger.error(f"Error checking Instagram auto-reply status: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/debug/test-instagram-comment")
async def debug_test_instagram_comment(
    instagram_user_id: str,
    media_id: str,
    comment_text: str = "Test comment from debug endpoint",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint for testing Instagram comment posting."""
    try:
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            return {
                "success": False,
                "error": "Instagram account not found"
            }
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            return {
                "success": False,
                "error": "Page access token not found"
            }
        
        # Test posting a comment
        result = await instagram_service.post_comment(
            media_id=media_id,
            page_access_token=page_access_token,
            comment_text=comment_text
        )
        
        return {
            "success": result["success"],
            "data": result if result["success"] else {"error": result.get("error")}
        }
        
    except Exception as e:
        logger.error(f"Debug test Instagram comment error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/debug/instagram-comments/{instagram_user_id}")
async def debug_get_instagram_comments(
    instagram_user_id: str,
    media_id: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to get Instagram comments."""
    try:
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            return {
                "success": False,
                "error": "Instagram account not found"
            }
        
        # Get the page access token from platform_data
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            return {
                "success": False,
                "error": "Page access token not found"
            }
        
        # Get comments
        comments = await instagram_service.get_comments(
            instagram_user_id=instagram_user_id,
            page_access_token=page_access_token,
            media_id=media_id,
            limit=limit
        )
        
        return {
            "success": True,
            "comments": comments,
            "total_count": len(comments),
            "account_username": account.username
        }
        
    except Exception as e:
        logger.error(f"Error getting Instagram comments: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/instagram/sync-posts/{instagram_user_id}")
async def sync_instagram_posts(
    instagram_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync all Instagram posts from the API into the local Post table for auto-reply."""
    try:
        logger.info(f"Starting Instagram sync for user {current_user.id}, instagram_user_id: {instagram_user_id}")
        
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            logger.error(f"Instagram account not found for user {current_user.id}, instagram_user_id: {instagram_user_id}")
            raise HTTPException(status_code=404, detail="Instagram account not found")
        
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            logger.error(f"Page access token not found for account {account.id}")
            raise HTTPException(status_code=400, detail="Page access token not found. Please reconnect your Instagram account.")
        
        logger.info(f"Found Instagram account: {account.username} (ID: {account.id})")
        
        # Fetch all media from Instagram API
        from app.services.instagram_service import instagram_service
        import asyncio
        
        # Run the synchronous method in a thread pool since it's not async
        loop = asyncio.get_event_loop()
        media_items = await loop.run_in_executor(
            None, 
            instagram_service.get_user_media, 
            instagram_user_id, 
            page_access_token, 
            100
        )
        
        synced = 0
        for media in media_items:
            # Check if post already exists in DB
            existing = db.query(Post).filter(
                Post.platform_post_id == media["id"],
                Post.social_account_id == account.id
            ).first()
            if existing:
                continue  # Skip if already exists
            # Create new Post row
            post = Post(
                user_id=current_user.id,
                social_account_id=account.id,
                content=media.get("caption", ""),
                post_type=PostType.IMAGE if media.get("media_type") == "IMAGE" else (PostType.VIDEO if media.get("media_type") == "VIDEO" else PostType.TEXT),
                status=PostStatus.PUBLISHED,
                platform_post_id=media["id"],
                published_at=media.get("timestamp"),
                media_urls=[media.get("media_url")] if media.get("media_url") else None
            )
            db.add(post)
            synced += 1
        
        db.commit()
        logger.info(f"Successfully synced {synced} posts out of {len(media_items)} total media items")
        return {"success": True, "synced": synced, "total": len(media_items)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing Instagram posts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync Instagram posts: {str(e)}"
        )


@router.get("/debug/instagram-sync-test/{instagram_user_id}")
async def debug_instagram_sync_test(
    instagram_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test Instagram sync functionality."""
    try:
        # Find the Instagram account
        account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == "instagram",
            SocialAccount.platform_user_id == instagram_user_id
        ).first()
        
        if not account:
            return {
                "success": False,
                "error": "Instagram account not found"
            }
        
        page_access_token = account.platform_data.get("page_access_token")
        if not page_access_token:
            return {
                "success": False,
                "error": "Page access token not found"
            }
        
        # Test getting media from Instagram API
        from app.services.instagram_service import instagram_service
        import asyncio
        
        loop = asyncio.get_event_loop()
        media_items = await loop.run_in_executor(
            None, 
            instagram_service.get_user_media, 
            instagram_user_id, 
            page_access_token, 
            10  # Just get 10 items for testing
        )
        
        # Check existing posts in DB
        existing_posts = db.query(Post).filter(
            Post.social_account_id == account.id
        ).count()
        
        return {
            "success": True,
            "account_info": {
                "id": account.id,
                "username": account.username,
                "platform_user_id": account.platform_user_id
            },
            "api_test": {
                "media_items_found": len(media_items),
                "sample_media": media_items[:3] if media_items else []
            },
            "database_test": {
                "existing_posts": existing_posts
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Instagram sync test: {e}")
        return {
            "success": False,
            "error": str(e)
        }