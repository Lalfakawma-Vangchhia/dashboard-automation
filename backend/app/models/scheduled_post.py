from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class FrequencyType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)
    
    # Content settings
    prompt = Column(Text, nullable=False)  # AI prompt for content generation
    
    # Schedule settings
    post_time = Column(String(5), nullable=False)  # HH:MM format
    frequency = Column(Enum(FrequencyType), nullable=False, default=FrequencyType.DAILY)
    
    # Status
    is_active = Column(Boolean, default=False)
    last_executed = Column(DateTime(timezone=True), nullable=True)
    next_execution = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="scheduled_posts")
    social_account = relationship("SocialAccount", back_populates="scheduled_posts")
    
    def __repr__(self):
        return f"<ScheduledPost(id={self.id}, prompt='{self.prompt[:50]}...', frequency={self.frequency.value})>" 