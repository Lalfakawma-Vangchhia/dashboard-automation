from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.post import PostStatus, PostType
from app.models.automation_rule import RuleType, TriggerType


class SocialAccountBase(BaseModel):
    platform: str
    username: Optional[str] = None
    display_name: Optional[str] = None


class SocialAccountCreate(SocialAccountBase):
    platform_user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class SocialAccountResponse(SocialAccountBase):
    id: int
    user_id: int
    platform_user_id: str
    profile_picture_url: Optional[str] = None
    follower_count: int
    account_type: Optional[str] = None
    is_verified: bool
    is_active: bool
    is_connected: bool
    connected_at: datetime
    last_sync_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PostBase(BaseModel):
    content: str
    post_type: PostType = PostType.TEXT
    link_url: Optional[str] = None
    hashtags: Optional[List[str]] = None


class PostCreate(PostBase):
    social_account_id: int
    scheduled_at: Optional[datetime] = None
    media_urls: Optional[List[str]] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[PostStatus] = None


class PostResponse(PostBase):
    id: int
    user_id: int
    social_account_id: int
    status: PostStatus
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    platform_post_id: Optional[str] = None
    likes_count: int
    comments_count: int
    shares_count: int
    views_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AutomationRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: RuleType
    trigger_type: TriggerType
    trigger_conditions: Dict[str, Any]
    actions: Dict[str, Any]


class AutomationRuleCreate(AutomationRuleBase):
    social_account_id: int
    daily_limit: Optional[int] = None
    active_hours_start: Optional[str] = None
    active_hours_end: Optional[str] = None
    active_days: Optional[List[str]] = None


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    daily_limit: Optional[int] = None


class AutomationRuleResponse(AutomationRuleBase):
    id: int
    user_id: int
    social_account_id: int
    is_active: bool
    daily_limit: Optional[int] = None
    daily_count: int
    total_executions: int
    success_count: int
    error_count: int
    last_execution_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Facebook-specific schemas
class FacebookPageInfo(BaseModel):
    id: str
    name: str
    category: str
    access_token: str
    can_post: bool = True
    canPost: Optional[bool] = True  # Alternative naming from frontend
    canComment: Optional[bool] = True
    profilePicture: Optional[str] = None
    followerCount: Optional[int] = 0


class FacebookConnectRequest(BaseModel):
    access_token: str
    user_id: str
    pages: Optional[List[FacebookPageInfo]] = None


class FacebookPostRequest(BaseModel):
    page_id: str
    message: str
    post_type: str = "post-auto"
    image: Optional[str] = None


class AutoReplyToggleRequest(BaseModel):
    enabled: bool
    page_id: str
    response_template: Optional[str] = "Thank you for your comment! We'll get back to you soon."
    selected_post_ids: Optional[List[int]] = Field(default=[], description="List of post IDs to enable auto-reply for")


# Webhook payload schemas
class WebhookPayload(BaseModel):
    user_id: int
    social_account_id: int
    action: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()


# Response schemas
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None


# Instagram-specific schemas
class InstagramAccountInfo(BaseModel):
    id: str
    username: str
    profile_picture_url: Optional[str] = None
    followers_count: Optional[int] = 0
    media_count: Optional[int] = 0
    account_type: str = "BUSINESS"
    page_id: str
    page_name: str
    access_token: str


class InstagramConnectRequest(BaseModel):
    access_token: str
    user_id: Optional[str] = None  # Not needed - user determined from auth token
    instagram_accounts: Optional[List[InstagramAccountInfo]] = None


class InstagramPostRequest(BaseModel):
    instagram_user_id: str
    caption: str
    image_url: str
    post_type: str = "post-auto"


class InstagramMediaResponse(BaseModel):
    id: str
    caption: Optional[str] = None
    media_type: str
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    permalink: str
    timestamp: str
    like_count: Optional[int] = 0
    comments_count: Optional[int] = 0


class InstagramAutoReplyToggleRequest(BaseModel):
    enabled: bool
    instagram_user_id: str
    response_template: Optional[str] = "Thank you for your comment! We'll get back to you soon."
    selected_post_ids: Optional[List[int]] = Field(default=[], description="List of post IDs to enable auto-reply for")


# LinkedIn-specific schemas
class LinkedInProfileInfo(BaseModel):
    id: str
    firstName: str
    lastName: str
    profilePicture: Optional[str] = None


class LinkedInConnectRequest(BaseModel):
    access_token: str
    user_id: str
    profile: LinkedInProfileInfo


class LinkedInPostRequest(BaseModel):
    profile_id: str
    content: str
    post_type: str = "post-auto"
    image_url: Optional[str] = None 