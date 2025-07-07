from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Platform details
    platform = Column(String, nullable=False)  # facebook, instagram, twitter, etc.
    platform_user_id = Column(String, nullable=False)  # Platform's user/page ID
    username = Column(String, nullable=True)  # @username or page name
    display_name = Column(String, nullable=True)  # Display name
    
    # Authentication tokens (encrypted)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Account metadata
    profile_picture_url = Column(String, nullable=True)
    follower_count = Column(Integer, default=0)
    account_type = Column(String, nullable=True)  # personal, business, page
    is_verified = Column(Boolean, default=False)
    
    # Platform-specific data
    platform_data = Column(JSON, nullable=True)  # Store platform-specific info
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="social_accounts")
    posts = relationship("Post", back_populates="social_account")
    scheduled_posts = relationship("ScheduledPost", back_populates="social_account")
    automation_rules = relationship("AutomationRule", back_populates="social_account")
    
    def __repr__(self):
        return f"<SocialAccount(id={self.id}, platform='{self.platform}', username='{self.username}')>" 