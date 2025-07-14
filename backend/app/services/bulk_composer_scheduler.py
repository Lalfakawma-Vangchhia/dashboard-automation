import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.bulk_composer_content import BulkComposerContent, BulkComposerStatus
from app.models.social_account import SocialAccount
from app.services.facebook_service import facebook_service

logger = logging.getLogger(__name__)


class BulkComposerScheduler:
    def __init__(self):
        self.is_running = False
        self.check_interval = 300  # Check every 5 minutes instead of 60 seconds
        
    async def start(self):
        """Start the bulk composer scheduler."""
        self.is_running = True
        logger.info("🚀 Starting Bulk Composer Scheduler...")
        
        # Add initial delay to prevent immediate execution
        await asyncio.sleep(10)
        
        while self.is_running:
            try:
                await self.process_due_posts()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in bulk composer scheduler: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the bulk composer scheduler."""
        self.is_running = False
        logger.info("🛑 Stopping Bulk Composer Scheduler...")
    
    async def process_due_posts(self):
        """Process posts that are due to be published."""
        try:
            # Get database session
            db = next(get_db())
            
            # Find posts that are due to be published
            now = datetime.now(timezone.utc)
            logger.info(f"[DEBUG] Scheduler current UTC time: {now.isoformat()}")
            due_posts = db.query(BulkComposerContent).filter(
                BulkComposerContent.status == BulkComposerStatus.SCHEDULED.value,
                BulkComposerContent.scheduled_datetime <= now
            ).all()
            
            if due_posts:
                logger.info(f"📅 Found {len(due_posts)} posts due for publishing")
                for post in due_posts:
                    logger.info(f"[DEBUG] Post ID {post.id} scheduled_datetime: {post.scheduled_datetime} (UTC)")
                    await self.publish_post(post, db)
            # Remove the else clause that logs "No posts due for publishing" every 60 seconds
                
        except Exception as e:
            logger.error(f"Error processing due posts: {str(e)}")
    
    async def publish_post(self, post: BulkComposerContent, db: Session):
        """Publish a single post to Facebook."""
        try:
            # Get the social account
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == post.social_account_id,
                SocialAccount.is_connected == True
            ).first()
            
            if not social_account:
                logger.error(f"Social account {post.social_account_id} not found or not connected")
                post.status = BulkComposerStatus.FAILED.value
                post.error_message = "Social account not connected"
                db.commit()
                return
            
            # Update publish attempt tracking
            post.publish_attempts += 1
            post.last_publish_attempt = datetime.now(timezone.utc)
            
            # Post to Facebook
            if post.media_file:
                # Photo post with media
                result = await facebook_service.post_photo_to_facebook(
                    page_id=social_account.platform_user_id,
                    access_token=social_account.access_token,
                    message=post.caption,
                    image_data=post.media_file
                )
            else:
                # Text-only feed post
                result = await facebook_service.post_text_to_facebook(
                    page_id=social_account.platform_user_id,
                    access_token=social_account.access_token,
                    message=post.caption
                )
            
            # Update post status
            if result and result.get('id'):
                post.status = BulkComposerStatus.PUBLISHED.value
                post.facebook_post_id = result.get('id')
                post.error_message = None
                logger.info(f"✅ Successfully published post {post.id} to Facebook: {result.get('id')}")
            else:
                post.status = BulkComposerStatus.FAILED.value
                post.error_message = "Facebook API returned no post ID"
                logger.error(f"❌ Failed to publish post {post.id}: No post ID returned")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error publishing post {post.id}: {str(e)}")
            post.status = BulkComposerStatus.FAILED.value
            post.error_message = str(e)
            db.commit()
    
    async def retry_failed_posts(self):
        """Retry posts that failed to publish (up to 3 attempts)."""
        try:
            db = next(get_db())
            
            # Find failed posts with less than 3 attempts
            failed_posts = db.query(BulkComposerContent).filter(
                BulkComposerContent.status == BulkComposerStatus.FAILED.value,
                BulkComposerContent.publish_attempts < 3
            ).all()
            
            if failed_posts:
                logger.info(f"🔄 Retrying {len(failed_posts)} failed posts")
                
                for post in failed_posts:
                    # Reset status to scheduled for retry
                    post.status = BulkComposerStatus.SCHEDULED.value
                    await self.publish_post(post, db)
                    
        except Exception as e:
            logger.error(f"Error retrying failed posts: {str(e)}")


# Create a singleton instance
bulk_composer_scheduler = BulkComposerScheduler() 