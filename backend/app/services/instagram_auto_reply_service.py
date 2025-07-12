import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.automation_rule import AutomationRule, RuleType
from app.models.social_account import SocialAccount
from app.models.post import Post
from app.services.instagram_service import instagram_service
from app.services.groq_service import groq_service
from app.database import get_db
import random

logger = logging.getLogger(__name__)


class InstagramAutoReplyService:
    """Service for handling automatic replies to Instagram comments."""
    
    def __init__(self):
        self.graph_api_base = "https://graph.facebook.com/v18.0"
    
    async def process_auto_replies(self, db: Session):
        """
        Process auto-replies for all active Instagram automation rules.
        This should be called periodically (e.g., every 5 minutes).
        """
        try:
            # Get all active auto-reply rules for Instagram
            auto_reply_rules = db.query(AutomationRule).filter(
                AutomationRule.rule_type == RuleType.AUTO_REPLY,
                AutomationRule.is_active == True
            ).all()
            
            # Filter for Instagram rules only
            instagram_rules = []
            for rule in auto_reply_rules:
                social_account = db.query(SocialAccount).filter(
                    SocialAccount.id == rule.social_account_id
                ).first()
                if social_account and social_account.platform == "instagram":
                    instagram_rules.append(rule)
            
            logger.info(f"🔄 Processing auto-replies for {len(instagram_rules)} active Instagram rules")
            
            if not instagram_rules:
                logger.info("📭 No active Instagram auto-reply rules found")
                return
            
            for rule in instagram_rules:
                try:
                    logger.info(f"🎯 Processing Instagram auto-reply rule {rule.id} for account {rule.social_account_id}")
                    await self._process_rule_auto_replies(rule, db)
                except Exception as e:
                    logger.error(f"❌ Error processing Instagram auto-reply rule {rule.id}: {e}")
                    # Continue with other rules even if one fails
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in process_auto_replies: {e}")
    
    async def _process_rule_auto_replies(self, rule: AutomationRule, db: Session):
        """Process auto-replies for a specific Instagram rule."""
        try:
            # Get the social account
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == rule.social_account_id
            ).first()
            
            if not social_account or not social_account.is_connected:
                logger.warning(f"⚠️ Instagram account {rule.social_account_id} not found or not connected")
                return
            
            logger.info(f"✅ Found connected Instagram account: {social_account.display_name}")
            
            # Get selected post IDs from the rule
            selected_post_ids = rule.actions.get("selected_instagram_post_ids", [])
            logger.info(f"🔍 Rule actions: {rule.actions}")
            logger.info(f"🔍 Selected Instagram post IDs: {selected_post_ids}")
            
            if not selected_post_ids:
                logger.info(f"📭 No selected posts for rule {rule.id}")
                return
            
            logger.info(f"📋 Processing {len(selected_post_ids)} selected posts for auto-reply")
            
            # Get the last check time for this rule
            last_check = rule.last_execution_at or (datetime.utcnow() - timedelta(minutes=10))
            logger.info(f"⏰ Last check: {last_check}, checking comments since then")
            
            # Get page access token from platform_data
            page_access_token = social_account.access_token
            if not page_access_token:
                logger.error(f"❌ No page access token found for Instagram account {social_account.id}")
                return
            
            # Process comments for each selected post with distribution logic
            total_replies = 0
            max_replies_per_execution = 3  # Limit replies per execution to avoid spam
            
            # Shuffle the post IDs to distribute replies across different posts
            shuffled_post_ids = list(selected_post_ids)
            random.shuffle(shuffled_post_ids)
            
            for post_id in shuffled_post_ids:
                if total_replies >= max_replies_per_execution:
                    logger.info(f"🛑 Reached maximum replies per execution ({max_replies_per_execution})")
                    break
                    
                logger.info(f"📝 Processing comments for Instagram post: {post_id}")
                replies_for_post = await self._process_post_comments(
                    post_id=post_id,
                    instagram_user_id=social_account.platform_user_id,
                    page_access_token=page_access_token,
                    rule=rule,
                    last_check=last_check,
                    db=db,
                    max_replies=max_replies_per_execution - total_replies
                )
                total_replies += replies_for_post
                
                if total_replies >= max_replies_per_execution:
                    break
            
            # Update last execution time
            rule.last_execution_at = datetime.utcnow()
            db.commit()
            logger.info(f"✅ Updated last execution time for rule {rule.id}. Total replies: {total_replies}")
            
        except Exception as e:
            logger.error(f"❌ Error processing Instagram rule {rule.id}: {e}")
    
    async def _process_post_comments(
        self, 
        post_id: str, 
        instagram_user_id: str,
        page_access_token: str, 
        rule: AutomationRule,
        last_check: datetime,
        db: Session,
        max_replies: int
    ):
        """Process comments for a specific Instagram post."""
        try:
            # Get comments for this Instagram post
            comments_result = await instagram_service.get_comments(
                instagram_user_id=instagram_user_id,
                page_access_token=page_access_token,
                media_id=post_id,
                limit=25
            )
            
            if not comments_result:
                logger.info(f"📭 No comments found for Instagram post {post_id}")
                return 0
            
            # Filter comments since last check
            recent_comments = []
            for comment in comments_result:
                try:
                    # Parse timestamp - Instagram uses ISO format
                    timestamp_str = comment.get('timestamp', '')
                    if timestamp_str:
                        comment_time = self.parse_instagram_timestamp(timestamp_str)
                        if comment_time > last_check:
                            recent_comments.append(comment)
                            logger.info(f"📝 Found recent comment {comment.get('id')} from {comment_time}")
                        else:
                            logger.info(f"⏭️ Skipping old comment {comment.get('id')} from {comment_time} (last check: {last_check})")
                    else:
                        # If no timestamp, include the comment to be safe
                        recent_comments.append(comment)
                        logger.info(f"📝 Found comment {comment.get('id')} without timestamp (including for safety)")
                except Exception as time_error:
                    logger.warning(f"Failed to parse comment timestamp: {time_error}")
                    # If we can't parse the timestamp, include the comment to be safe
                    recent_comments.append(comment)
                    logger.info(f"📝 Found comment {comment.get('id')} with unparseable timestamp (including for safety)")
            
            logger.info(f"Found {len(recent_comments)} new comments for Instagram post {post_id}")
            
            # Process each recent comment
            replies_for_post = 0
            for comment in recent_comments:
                if replies_for_post >= max_replies:
                    logger.info(f"🛑 Reached maximum replies for this post ({max_replies})")
                    break
                    
                comment_id = comment.get('id')
                comment_text = comment.get('text', '')
                commenter_id = comment.get('from', {}).get('id')
                
                logger.info(f"🔄 Processing comment {comment_id}: '{comment_text[:50]}...'")
                
                # Skip comments from the account owner
                if commenter_id == instagram_user_id:
                    logger.info(f"⏭️ Skipping comment from own account")
                    continue
                
                # Check if we should reply to this comment
                should_reply = await self._should_reply_to_comment(
                    comment, 
                    page_access_token,
                    instagram_user_id
                )
                
                if should_reply:
                    logger.info(f"✅ Will reply to Instagram comment {comment_id}")
                    # Generate and post AI reply
                    await self._generate_and_post_reply(
                        comment=comment,
                        page_access_token=page_access_token,
                        rule=rule,
                        instagram_user_id=instagram_user_id
                    )
                    replies_for_post += 1
                else:
                    logger.info(f"⏭️ Skipping comment {comment_id} - no reply needed")
            
            return replies_for_post
            
        except Exception as e:
            logger.error(f"Error processing comments for Instagram post {post_id}: {e}")
            return 0
    
    async def _should_reply_to_comment(
        self, 
        comment: Dict[str, Any], 
        page_access_token: str,
        instagram_user_id: str
    ) -> bool:
        """
        Determine if we should reply to an Instagram comment.
        
        Rules:
        1. If it's a new comment -> reply
        2. If we already replied to this comment -> don't reply again
        3. If it's from our own account -> don't reply
        4. If it's an AI-generated reply -> don't reply to avoid loops
        """
        try:
            comment_id = comment.get("id")
            commenter_id = comment.get("from", {}).get("id")
            comment_text = comment.get("text", "")
            
            logger.info(f"🔍 Evaluating comment {comment_id}: '{comment_text[:50]}...' from {commenter_id}")
            
            # Skip comments from our own account
            if commenter_id == instagram_user_id:
                logger.info(f"⏭️ Skipping comment from own account")
                return False
            
            # Skip AI-generated replies to avoid loops
            if self._is_ai_response(comment_text):
                logger.info(f"⏭️ Skipping AI-generated comment to avoid loops")
                return False
            
            # Check if we already replied to this comment
            if await self._has_replied_to_comment(comment_id, page_access_token):
                logger.info(f"Already replied to comment {comment_id}, skipping")
                return False
            
            # For Instagram, we'll reply to all new comments (simpler than Facebook threading)
            logger.info(f"✅ New Instagram comment {comment_id} from {commenter_id}, will reply")
            return True
                
        except Exception as e:
            logger.error(f"Error determining if should reply to Instagram comment {comment.get('id')}: {e}")
            return False
    
    def _is_ai_response(self, message: str) -> bool:
        """
        Check if a message is likely from our AI.
        Look for patterns that indicate it's our auto-reply.
        """
        if not message:
            return False
        
        # Check for common AI response patterns - be more specific
        ai_indicators = [
            "thanks for your comment",
            "we appreciate your engagement",
            "thank you for your comment",
            "we're glad you",
            "thanks for sharing",
            "we love hearing from you",
            "thanks! we're",
            "we're excited",
            "you can find it",
            "let us know if",
            "you're welcome",
            "we appreciate your",
            "thanks for the",
            "thank you so much",
            "we're so glad you",
            "we love that you",
            "feel free to reach out",
            "don't hesitate to contact",
            "we'd love to hear",
            "we're here to help"
        ]
        
        message_lower = message.lower()
        
        # Check if any AI indicator is present - be more strict
        for indicator in ai_indicators:
            if indicator in message_lower:
                logger.info(f"🤖 AI response detected: '{indicator}' found in message")
                return True
        
        # Check for our own account replies (more specific pattern)
        # Look for @mentions combined with typical AI response patterns
        if "@" in message:
            ai_mention_patterns = [
                "thanks for your comment",
                "we appreciate your",
                "thank you for",
                "we're glad you",
                "we love hearing"
            ]
            
            for pattern in ai_mention_patterns:
                if pattern in message_lower:
                    logger.info(f"🤖 AI response detected: @mention with '{pattern}'")
                    return True
        
        logger.info(f"❌ Not an AI response: {message[:50]}...")
        return False
    
    async def _has_replied_to_comment(self, comment_id: str, page_access_token: str) -> bool:
        """Check if we already replied to an Instagram comment."""
        try:
            # Store replied comment IDs with timestamps to allow expiration
            # This prevents duplicate replies to the same comment
            
            # For now, we'll use a simple in-memory cache with expiration (in production, use database)
            # In a real implementation, you'd store this in a database table
            if not hasattr(self, '_replied_comments'):
                self._replied_comments = {}
            
            # Check if comment was replied to recently (within 24 hours)
            if comment_id in self._replied_comments:
                reply_time = self._replied_comments[comment_id]
                if datetime.utcnow() - reply_time < timedelta(hours=24):
                    logger.info(f"Already replied to comment {comment_id} recently")
                    return True
                else:
                    # Remove expired entry
                    del self._replied_comments[comment_id]
                    logger.info(f"Removed expired reply tracking for comment {comment_id}")
            
            return False
                
        except Exception as e:
            logger.error(f"❌ Error checking replies for Instagram comment {comment_id}: {e}")
            return False
    
    def _mark_comment_as_replied(self, comment_id: str):
        """Mark a comment as replied to prevent duplicate replies."""
        if not hasattr(self, '_replied_comments'):
            self._replied_comments = {}
        self._replied_comments[comment_id] = datetime.utcnow()
        logger.info(f"Marked comment {comment_id} as replied at {datetime.utcnow()}")
    

    
    async def _generate_and_post_reply(
        self, 
        comment: Dict[str, Any], 
        page_access_token: str, 
        rule: AutomationRule,
        instagram_user_id: str
    ):
        """Generate AI reply and post it to Instagram."""
        try:
            comment_text = comment.get("text", "")
            commenter_name = comment.get("from", {}).get("username", "there")
            comment_id = comment.get("id")
            
            # Get the media ID from the comment's media_id field (if available)
            # or extract it from the comment ID structure
            media_id = comment.get("media_id")
            if not media_id:
                # Instagram comment IDs are typically in format: {media_id}_{comment_id}
                # But sometimes they're just the comment ID
                if "_" in comment_id:
                    media_id = comment_id.split("_")[0]
                else:
                    # If we can't extract media_id, we need to get it from the rule's selected posts
                    selected_post_ids = rule.actions.get("selected_instagram_post_ids", [])
                    if selected_post_ids:
                        media_id = selected_post_ids[0]  # Use the first selected post
                    else:
                        logger.error(f"❌ Cannot determine media_id for comment {comment_id}")
                        return
            
            logger.info(f"📝 Posting reply to media {media_id} for comment {comment_id}")
            
            # Generate AI reply with user mention and context
            reply_text = await self._generate_ai_reply(
                comment_text=comment_text,
                commenter_name=commenter_name,
                template=rule.actions.get("response_template")
            )
            
            # Post reply to Instagram
            reply_result = await instagram_service.post_comment(
                media_id=media_id,
                page_access_token=page_access_token,
                comment_text=reply_text,
                parent_comment_id=comment_id
            )
            
            if reply_result["success"]:
                logger.info(f"✅ Auto-reply posted successfully to Instagram comment {comment_id}")
                logger.info(f"📝 Reply: {reply_text}")
                
                # Mark this comment as replied to prevent duplicate replies
                self._mark_comment_as_replied(comment_id)
                
                # Update rule statistics
                rule.success_count += 1
                rule.last_success_at = datetime.utcnow()
                
            else:
                logger.error(f"❌ Failed to post Instagram auto-reply: {reply_result.get('error')}")
                rule.error_count += 1
                rule.last_error_at = datetime.utcnow()
                rule.last_error_message = reply_result.get('error', 'Unknown error')
                    
        except Exception as e:
            logger.error(f"Error generating/posting Instagram reply: {e}")
            rule.error_count += 1
            rule.last_error_at = datetime.utcnow()
            rule.last_error_message = str(e)
    
    async def _generate_ai_reply(
        self, 
        comment_text: str, 
        commenter_name: str, 
        template: Optional[str] = None
    ) -> str:
        """Generate AI reply mentioning the commenter."""
        try:
            # Create a context for the AI
            context = f"Instagram comment by {commenter_name}: {comment_text}"
            
            # Use the template if provided, otherwise use a default approach
            if template:
                # Use template as a guide for AI
                ai_prompt = f"""
                Generate a friendly, engaging reply to this Instagram comment. 
                The reply should mention the commenter by name and be contextual to their comment.
                
                Template guide: {template}
                Comment: {comment_text}
                Commenter: {commenter_name}
                
                Generate a natural, conversational reply that mentions the commenter.
                Keep it under 200 characters and use appropriate emojis sparingly.
                """
            else:
                # Use default AI approach for contextual conversation
                ai_prompt = f"""
                Generate a friendly, engaging reply to this Instagram comment.
                The reply should:
                1. Mention the commenter by name (e.g., "@{commenter_name}" or "Hey {commenter_name}")
                2. Be contextual and relevant to their comment
                3. Be warm, professional, and encouraging
                4. Keep it under 200 characters
                5. Use appropriate emojis sparingly
                6. Feel natural and conversational
                
                Comment: {comment_text}
                Commenter: {commenter_name}
                
                Generate a natural, conversational reply that feels like a real person responding.
                """
            
            # Generate reply using Groq AI
            ai_result = await groq_service.generate_auto_reply(comment_text, context)
            
            if ai_result["success"]:
                reply_content = ai_result["content"]
                
                # Ensure we mention the commenter
                if commenter_name.lower() not in reply_content.lower():
                    # Add mention at the beginning if not already present
                    reply_content = f"@{commenter_name} {reply_content}"
                
                return reply_content
            else:
                # Fallback reply
                return f"@{commenter_name} Thanks for your comment! We appreciate your engagement. 😊"
                
        except Exception as e:
            logger.error(f"Error generating AI reply: {e}")
            # Fallback reply
            return f"@{commenter_name} Thanks for your comment! We appreciate your engagement. 😊"

    def parse_instagram_timestamp(self, ts):
        """
        Parse Instagram timestamps like '2025-07-06T07:55:57+0000' or '2025-07-06T07:55:57Z'.
        Converts '+0000' to '+00:00' for Python compatibility.
        """
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        elif ts.endswith('+0000'):
            ts = ts[:-5] + '+00:00'
        return datetime.fromisoformat(ts)


# Create a singleton instance
instagram_auto_reply_service = InstagramAutoReplyService() 