import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scheduled_post import ScheduledPost, FrequencyType
from app.models.social_account import SocialAccount
from app.models.post import Post, PostStatus, PostType
from app.services.groq_service import groq_service
from app.services.facebook_service import facebook_service
from app.services.auto_reply_service import auto_reply_service
from app.services.instagram_service import instagram_service
import pytz
from pytz import timezone, UTC

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
    
    async def start(self):
        """Start the scheduler service"""
        if self.running:
            logger.info("Scheduler service already running")
            return
        
        self.running = True
        logger.info("🚀 Scheduler service started - checking every 30 seconds")
        
        while self.running:
            try:
                await self.process_scheduled_posts()
                await self.process_auto_replies()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the scheduler service"""
        self.running = False
        logger.info("🛑 Scheduler service stopped")
    
    async def process_scheduled_posts(self):
        """Process all scheduled posts that are due for execution"""
        db: Session = None
        try:
            # Get database session
            db = next(get_db())
            # Find all scheduled Instagram posts that are due for execution
            now_local = datetime.now(timezone("Asia/Kolkata"))
            logger.info(f"[DEBUG] Scheduler now (Asia/Kolkata): {now_local}")
            all_posts = db.query(ScheduledPost).filter(
                ScheduledPost.is_active == True,
                ScheduledPost.status == "scheduled",
                ScheduledPost.platform == "instagram"
            ).all()
            for post in all_posts:
                logger.info(f"[DEBUG] Post {post.id} scheduled_datetime: {post.scheduled_datetime} (type: {type(post.scheduled_datetime)})")
            # Query for due posts (works with Asia/Kolkata or UTC depending on now)
            now_utc = now_local.astimezone(UTC)
            due_posts = db.query(ScheduledPost).filter(
                ScheduledPost.status.in_(['scheduled', 'ready']),
                ScheduledPost.platform == 'instagram',
                ScheduledPost.scheduled_datetime <= now_utc,
                ScheduledPost.is_active == True
            ).all()
            logger.info(f"✅ Found {len(due_posts)} posts ready to publish at {now_local}")
            # NOTE: If you migrate all scheduled_datetime to UTC, set now = datetime.utcnow() and ensure all DB times are UTC.
            if due_posts:
                logger.info(f"📅 Found {len(due_posts)} scheduled Instagram posts due for execution")
            else:
                logger.info(f"🔍 No scheduled Instagram posts due for execution at {now_local}")
            for scheduled_post in due_posts:
                try:
                    await self.execute_scheduled_instagram_post(scheduled_post, db)
                except Exception as e:
                    logger.error(f"Failed to execute scheduled Instagram post {scheduled_post.id}: {e}")
        except Exception as e:
            logger.error(f"Error processing scheduled Instagram posts: {e}")
        finally:
            if db:
                db.close()

    async def execute_scheduled_instagram_post(self, scheduled_post: ScheduledPost, db: Session):
        """Execute a single scheduled Instagram post"""
        try:
            logger.info(f"🔄 Executing scheduled Instagram post {scheduled_post.id}: '{scheduled_post.prompt[:50]}...'")
            logger.info(f"📋 Post type: {scheduled_post.post_type.value if hasattr(scheduled_post.post_type, 'value') else scheduled_post.post_type}")
            
            # Validate presence of caption and media
            if not scheduled_post.prompt:
                logger.error(f"❌ Scheduled post {scheduled_post.id} missing caption. Marking as failed.")
                scheduled_post.status = "failed"
                scheduled_post.is_active = False
                scheduled_post.last_executed = datetime.utcnow()
                db.commit()
                return
            
            # Check for appropriate media based on post type
            post_type = scheduled_post.post_type.value if hasattr(scheduled_post.post_type, 'value') else scheduled_post.post_type
            has_media = False
            
            if post_type == "photo":
                has_media = bool(scheduled_post.image_url)
                logger.info(f"📸 Photo post - Image URL: {scheduled_post.image_url}")
            elif post_type == "carousel":
                has_media = bool(scheduled_post.media_urls and len(scheduled_post.media_urls) > 0)
                logger.info(f"🖼️ Carousel post - Media URLs: {scheduled_post.media_urls}")
            elif post_type == "reel":
                has_media = bool(scheduled_post.video_url)
                logger.info(f"🎬 Reel post - Video URL: {scheduled_post.video_url}")
            
            if not has_media:
                logger.error(f"❌ Scheduled post {scheduled_post.id} missing required media for {post_type} post. Marking as failed.")
                scheduled_post.status = "failed"
                scheduled_post.is_active = False
                scheduled_post.last_executed = datetime.utcnow()
                db.commit()
                return
            
            # Get the social account
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == scheduled_post.social_account_id
            ).first()
            if not social_account:
                logger.error(f"❌ Social account {scheduled_post.social_account_id} not found in database")
                return
            if not social_account.is_connected:
                logger.error(f"❌ Social account {scheduled_post.social_account_id} ({social_account.display_name}) is not connected")
                return
            logger.info(f"✅ Found connected Instagram account: {social_account.display_name} (ID: {social_account.id})")
            
            # Get access token and Instagram user ID
            page_access_token = social_account.platform_data.get("page_access_token")
            instagram_user_id = social_account.platform_user_id
            if not page_access_token or not instagram_user_id:
                logger.error(f"❌ Missing Instagram user ID or access token for account {social_account.id}")
                scheduled_post.status = "failed"
                db.commit()
                return
            
            # Post to Instagram based on post type
            try:
                if post_type == "photo":
                    # Single photo post
                    result = await instagram_service.create_post(
                        instagram_user_id=instagram_user_id,
                        page_access_token=page_access_token,
                        caption=scheduled_post.prompt,
                        image_url=scheduled_post.image_url
                    )
                elif post_type == "carousel":
                    # Carousel post with multiple images
                    result = await instagram_service.create_carousel_post(
                        instagram_user_id=instagram_user_id,
                        page_access_token=page_access_token,
                        caption=scheduled_post.prompt,
                        image_urls=scheduled_post.media_urls
                    )
                elif post_type == "reel":
                    # Reel post with video
                    result = await instagram_service.create_post(
                        instagram_user_id=instagram_user_id,
                        page_access_token=page_access_token,
                        caption=scheduled_post.prompt,
                        video_url=scheduled_post.video_url,
                        is_reel=True
                    )
                else:
                    logger.error(f"❌ Unknown post type: {post_type}")
                    scheduled_post.status = "failed"
                    db.commit()
                    return
                
                if result and result.get("success"):
                    scheduled_post.status = "posted"
                    logger.info(f"✅ Successfully posted scheduled {post_type} to Instagram: {scheduled_post.id}")
                else:
                    scheduled_post.status = "failed"
                    logger.error(f"❌ Failed to post {post_type} to Instagram: {result.get('error')}")
            except Exception as ig_error:
                logger.error(f"Instagram posting error: {ig_error}")
                scheduled_post.status = "failed"
            
            scheduled_post.is_active = False
            scheduled_post.last_executed = datetime.utcnow()
            db.commit()
            logger.info(f"✅ Scheduled Instagram post {scheduled_post.id} executed (final status: {scheduled_post.status}).")
        except Exception as e:
            logger.error(f"Error executing scheduled Instagram post {scheduled_post.id}: {e}")
            scheduled_post.status = "failed"
            db.commit()
    
    def calculate_next_execution(self, post_time: str, frequency: FrequencyType) -> datetime:
        """Calculate the next execution time based on frequency"""
        try:
            time_parts = post_time.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
        except (ValueError, IndexError):
            # Default to current time + frequency if time parsing fails
            hour = datetime.utcnow().hour
            minute = datetime.utcnow().minute
        
        now = datetime.utcnow()
        
        if frequency == FrequencyType.DAILY:
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_exec += timedelta(days=1)
        elif frequency == FrequencyType.WEEKLY:
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_exec += timedelta(weeks=1)
        elif frequency == FrequencyType.MONTHLY:
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            # Add approximately 30 days for monthly
            next_exec += timedelta(days=30)
        else:
            # Default to daily
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_exec += timedelta(days=1)
        
        return next_exec

    async def process_auto_replies(self):
        """Process auto-replies for all active automation rules"""
        db: Session = None
        try:
            # Get database session
            db = next(get_db())
            
            # Process Facebook auto-replies
            await auto_reply_service.process_auto_replies(db)
            
            # Process Instagram auto-replies
            from app.services.instagram_auto_reply_service import instagram_auto_reply_service
            await instagram_auto_reply_service.process_auto_replies(db)
            
        except Exception as e:
            logger.error(f"Error processing auto-replies: {e}")
        finally:
            if db:
                db.close()

# Create global scheduler instance
scheduler_service = SchedulerService() 