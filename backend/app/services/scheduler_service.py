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

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.running = False
        self.check_interval = 30  # Check every 30 seconds for faster testing
    
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
            
            # Find all active scheduled posts that are due for execution
            now = datetime.utcnow()
            due_posts = db.query(ScheduledPost).filter(
                ScheduledPost.is_active == True,
                ScheduledPost.next_execution <= now
            ).all()
            
            if due_posts:
                logger.info(f"📅 Found {len(due_posts)} scheduled posts due for execution")
            else:
                logger.info(f"🔍 No scheduled posts due for execution at {now}")
            
            for scheduled_post in due_posts:
                try:
                    await self.execute_scheduled_post(scheduled_post, db)
                except Exception as e:
                    logger.error(f"Failed to execute scheduled post {scheduled_post.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error processing scheduled posts: {e}")
        finally:
            if db:
                db.close()
    
    async def execute_scheduled_post(self, scheduled_post: ScheduledPost, db: Session):
        """Execute a single scheduled post"""
        try:
            logger.info(f"🔄 Executing scheduled post {scheduled_post.id}: '{scheduled_post.prompt[:50]}...'")
            
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
            
            logger.info(f"✅ Found connected social account: {social_account.display_name} (ID: {social_account.id})")
            
            # Generate content using AI
            generated_content = ""
            if groq_service.is_available():
                try:
                    ai_result = await groq_service.generate_facebook_post(scheduled_post.prompt)
                    if ai_result["success"]:
                        generated_content = ai_result["content"]
                        logger.info(f"✅ Generated AI content for scheduled post {scheduled_post.id}")
                    else:
                        # Fallback to prompt if AI fails
                        generated_content = scheduled_post.prompt
                        logger.warning(f"AI generation failed, using prompt as content for post {scheduled_post.id}")
                except Exception as e:
                    logger.error(f"AI generation error: {e}")
                    generated_content = scheduled_post.prompt
            else:
                generated_content = scheduled_post.prompt
            
            # Create post record in database
            post = Post(
                user_id=scheduled_post.user_id,
                social_account_id=scheduled_post.social_account_id,
                content=generated_content,
                post_type=PostType.TEXT,
                status=PostStatus.SCHEDULED,
                is_auto_post=True,
                metadata={
                    "scheduled_post_id": scheduled_post.id,
                    "ai_generated": groq_service.is_available(),
                    "original_prompt": scheduled_post.prompt,
                    "execution_time": datetime.utcnow().isoformat()
                }
            )
            
            db.add(post)
            db.commit()
            db.refresh(post)
            
            # Post to Facebook
            try:
                facebook_result = await facebook_service.create_post(
                    page_id=social_account.platform_user_id,
                    access_token=social_account.access_token,
                    message=generated_content,
                    media_url=None,
                    media_type="text"
                )
                
                if facebook_result and facebook_result.get("success"):
                    post.status = PostStatus.PUBLISHED
                    post.platform_post_id = facebook_result.get("post_id")
                    post.platform_response = facebook_result
                    logger.info(f"✅ Successfully posted scheduled content to Facebook: {post.id}")
                else:
                    post.status = PostStatus.FAILED
                    post.error_message = facebook_result.get("error", "Unknown Facebook API error")
                    logger.error(f"❌ Failed to post to Facebook: {facebook_result.get('error')}")
                    
            except Exception as fb_error:
                logger.error(f"Facebook posting error: {fb_error}")
                post.status = PostStatus.FAILED
                post.error_message = str(fb_error)
            
            # Update scheduled post execution info
            scheduled_post.last_executed = datetime.utcnow()
            scheduled_post.next_execution = self.calculate_next_execution(
                scheduled_post.post_time, 
                scheduled_post.frequency
            )
            
            db.commit()
            
            logger.info(f"✅ Scheduled post {scheduled_post.id} executed successfully. Next execution: {scheduled_post.next_execution}")
            
        except Exception as e:
            logger.error(f"Error executing scheduled post {scheduled_post.id}: {e}")
            # Update the next execution even if failed to avoid getting stuck
            scheduled_post.next_execution = self.calculate_next_execution(
                scheduled_post.post_time, 
                scheduled_post.frequency
            )
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