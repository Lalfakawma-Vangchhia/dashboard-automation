from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class GlobalAutoReplyStatus(Base):
    __tablename__ = "global_auto_reply_status"
    
    id = Column(Integer, primary_key=True, index=True)
    instagram_user_id = Column(String(255), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @classmethod
    def is_enabled(cls, instagram_user_id: str, db=None):
        """Check if global auto-reply is enabled for an Instagram user."""
        if db is None:
            from app.database import get_db
            db = next(get_db())
        
        status = db.query(cls).filter_by(instagram_user_id=instagram_user_id).first()
        return status.enabled if status else False
    
    @classmethod
    def set_enabled(cls, instagram_user_id: str, enabled: bool, db=None):
        """Set global auto-reply status for an Instagram user."""
        if db is None:
            from app.database import get_db
            db = next(get_db())
        
        status = db.query(cls).filter_by(instagram_user_id=instagram_user_id).first()
        if status:
            status.enabled = enabled
        else:
            status = cls(instagram_user_id=instagram_user_id, enabled=enabled)
            db.add(status)
        
        db.commit()
        return status 