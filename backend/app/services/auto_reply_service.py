import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.automation_rule import AutomationRule, RuleType
from app.models.social_account import SocialAccount
from app.models.post import Post
from app.services.facebook_service import facebook_service
from app.services.groq_service import groq_service

logger = logging.getLogger(__name__)


class AutoReplyService:
    """Service for handling automatic replies to Facebook comments."""
    
    def __init__(self):
        self.graph_api_base = "https://graph.facebook.com/v18.0"
    
    async def process_auto_replies(self, db: Session):
        """
        Process auto-replies for all active automation rules.
        This should be called periodically (e.g., every 5 minutes).
        """
        try:
            # Get all active auto-reply rules
            auto_reply_rules = db.query(AutomationRule).filter(
                AutomationRule.rule_type == RuleType.AUTO_REPLY,
                AutomationRule.is_active == True
            ).all()
            
            logger.info(f"🔄 Processing auto-replies for {len(auto_reply_rules)} active rules")
            
            if not auto_reply_rules:
                logger.info("📭 No active auto-reply rules found")
                return
            
            for rule in auto_reply_rules:
                try:
                    logger.info(f"🎯 Processing auto-reply rule {rule.id} for account {rule.social_account_id}")
                    await self._process_rule_auto_replies(rule, db)
                except Exception as e:
                    logger.error(f"❌ Error processing auto-reply rule {rule.id}: {e}")
                    # Continue with other rules even if one fails
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in process_auto_replies: {e}")
    
    async def _process_rule_auto_replies(self, rule: AutomationRule, db: Session):
        """Process auto-replies for a specific rule."""
        try:
            # Get the social account
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == rule.social_account_id
            ).first()
            
            if not social_account or not social_account.is_connected:
                logger.warning(f"⚠️ Social account {rule.social_account_id} not found or not connected")
                return
            
            logger.info(f"✅ Found connected social account: {social_account.display_name}")
            
            # Get selected post IDs from the rule
            selected_post_ids = rule.actions.get("selected_facebook_post_ids", [])
            logger.info(f"🔍 Rule actions: {rule.actions}")
            logger.info(f"🔍 Selected Facebook post IDs: {selected_post_ids}")
            
            if not selected_post_ids:
                logger.info(f"📭 No selected posts for rule {rule.id}")
                return
            
            logger.info(f"📋 Processing {len(selected_post_ids)} selected posts for auto-reply")
            
            # Get the last check time for this rule
            last_check = rule.last_execution_at or (datetime.utcnow() - timedelta(minutes=10))
            logger.info(f"⏰ Last check: {last_check}, checking comments since then")
            
            # Process comments for each selected post
            for post_id in selected_post_ids:
                logger.info(f"📝 Processing comments for post: {post_id}")
                await self._process_post_comments(
                    post_id=post_id,
                    page_id=social_account.platform_user_id,
                    access_token=social_account.access_token,
                    rule=rule,
                    last_check=last_check,
                    db=db
                )
            
            # Update last execution time
            rule.last_execution_at = datetime.utcnow()
            db.commit()
            logger.info(f"✅ Updated last execution time for rule {rule.id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing rule {rule.id}: {e}")
    
    async def _process_post_comments(
        self, 
        post_id: str, 
        page_id: str, 
        access_token: str, 
        rule: AutomationRule,
        last_check: datetime,
        db: Session
    ):
        """Process comments for a specific post."""
        try:
            since_param = int(last_check.timestamp())
            
            async with httpx.AsyncClient() as client:
                # Get comments on this post since last check
                comments_resp = await client.get(
                    f"{self.graph_api_base}/{post_id}/comments",
                    params={
                        "access_token": access_token,
                        "since": since_param,
                        "fields": "id,message,from,created_time,parent"
                    }
                )
                
                if comments_resp.status_code != 200:
                    logger.error(f"Failed to get comments for post {post_id}: {comments_resp.text}")
                    return
                
                comments_data = comments_resp.json()
                comments = comments_data.get("data", [])
                
                logger.info(f"Found {len(comments)} new comments for post {post_id}")
                
                # Group comments by conversation thread
                conversation_threads = self._group_comments_by_thread(comments)
                
                for thread_id, thread_comments in conversation_threads.items():
                    # Only process the most recent comment in each thread
                    latest_comment = thread_comments[-1]
                    
                    logger.info(f"🔄 Processing thread {thread_id} with {len(thread_comments)} comments")
                    logger.info(f"📝 Latest comment: {latest_comment.get('message', '')[:50]}...")
                    
                    # Skip comments from the page itself
                    if latest_comment["from"]["id"] == page_id:
                        logger.info(f"⏭️ Skipping comment from our own page")
                        continue
                    
                    # Check if we should reply to this comment
                    should_reply = await self._should_reply_to_comment(
                        latest_comment, 
                        thread_comments, 
                        access_token,
                        page_id
                    )
                    
                    if should_reply:
                        logger.info(f"✅ Will reply to comment {latest_comment['id']}")
                        # Generate and post AI reply
                        await self._generate_and_post_reply(
                            comment=latest_comment,
                            access_token=access_token,
                            rule=rule,
                            page_id=page_id
                        )
                    else:
                        logger.info(f"⏭️ Skipping comment {latest_comment['id']} - no reply needed")
            
        except Exception as e:
            logger.error(f"Error processing comments for post {post_id}: {e}")
    
    def _group_comments_by_thread(self, comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group comments by conversation thread.
        Top-level comments start new threads, replies continue existing threads.
        """
        threads = {}
        
        for comment in comments:
            # If comment has a parent, it's a reply - add to parent's thread
            if comment.get("parent"):
                parent_id = comment["parent"]["id"]
                if parent_id not in threads:
                    threads[parent_id] = []
                threads[parent_id].append(comment)
            else:
                # Top-level comment - start new thread
                thread_id = comment["id"]
                if thread_id not in threads:
                    threads[thread_id] = []
                threads[thread_id].append(comment)
        
        return threads
    
    async def _should_reply_to_comment(
        self, 
        latest_comment: Dict[str, Any], 
        thread_comments: List[Dict[str, Any]], 
        access_token: str,
        page_id: str
    ) -> bool:
        """
        Determine if we should reply to the latest comment in a thread.
        
        Rules:
        1. If it's a new top-level comment -> reply
        2. If it's a reply to our AI response -> reply back
        3. If it's a reply to someone else -> don't reply
        4. If we already replied to this comment -> don't reply again
        """
        try:
            comment_id = latest_comment["id"]
            commenter_id = latest_comment["from"]["id"]
            
            # Check if we already replied to this specific comment
            if await self._has_replied_to_comment(comment_id, access_token):
                logger.info(f"Already replied to comment {comment_id}, skipping")
                return False
            
            # If it's a top-level comment (no parent), always reply
            if not latest_comment.get("parent"):
                logger.info(f"New top-level comment {comment_id}, will reply")
                return True
            
            # If it's a reply, check if it's replying to our AI response
            parent_id = latest_comment["parent"]["id"]
            
            # Get the parent comment to see who it's from
            async with httpx.AsyncClient() as client:
                parent_resp = await client.get(
                    f"{self.graph_api_base}/{parent_id}",
                    params={
                        "access_token": access_token,
                        "fields": "from,message"
                    }
                )
                
                if parent_resp.status_code == 200:
                    parent_data = parent_resp.json()
                    parent_from_id = parent_data.get("from", {}).get("id")
                    parent_message = parent_data.get("message", "")
                    
                    # If parent is from our page and contains our AI signature, reply
                    if parent_from_id == page_id and self._is_ai_response(parent_message):
                        logger.info(f"Comment {comment_id} is replying to our AI response, will reply back")
                        return True
                    else:
                        logger.info(f"Comment {comment_id} is replying to someone else, won't reply")
                        return False
                else:
                    logger.warning(f"Could not get parent comment {parent_id}, skipping")
                    return False
                    
        except Exception as e:
            logger.error(f"Error determining if should reply to comment {latest_comment.get('id')}: {e}")
            return False
    
    def _is_ai_response(self, message: str) -> bool:
        """
        Check if a message is likely from our AI.
        Look for patterns that indicate it's our auto-reply.
        """
        if not message:
            return False
        
        # Check for common AI response patterns
        ai_indicators = [
            "thanks for your comment",
            "we appreciate your engagement",
            "thank you for",
            "we're glad",
            "thanks for sharing",
            "we love hearing from you",
            "thanks! we're",
            "we're excited",
            "you can find it",
            "let us know if",
            "you're welcome"
        ]
        
        message_lower = message.lower()
        
        # Check if any AI indicator is present
        for indicator in ai_indicators:
            if indicator in message_lower:
                logger.info(f"🤖 AI response detected: '{indicator}' found in message")
                return True
        
        # Also check for @mentions at the beginning (our AI always mentions users)
        if message.strip().startswith('@'):
            logger.info(f"🤖 AI response detected: Message starts with @mention")
            return True
        
        logger.info(f"❌ Not an AI response: {message[:50]}...")
        return False
    
    async def _has_replied_to_comment(self, comment_id: str, access_token: str) -> bool:
        """Check if we already replied to a comment."""
        try:
            async with httpx.AsyncClient() as client:
                # Get replies to this comment
                replies_resp = await client.get(
                    f"{self.graph_api_base}/{comment_id}/comments",
                    params={
                        "access_token": access_token,
                        "fields": "from,message,created_time"
                    }
                )
                
                if replies_resp.status_code == 200:
                    replies_data = replies_resp.json()
                    replies = replies_data.get("data", [])
                    
                    logger.info(f"🔍 Checking {len(replies)} replies to comment {comment_id}")
                    
                    # Check if any of our AI replies exist
                    for reply in replies:
                        reply_message = reply.get("message", "")
                        reply_from = reply.get("from", {})
                        reply_from_id = reply_from.get("id", "")
                        
                        logger.info(f"🔍 Reply from {reply_from_id}: {reply_message[:50]}...")
                        
                        if self._is_ai_response(reply_message):
                            logger.info(f"✅ Found existing AI reply to comment {comment_id}")
                            return True
                else:
                    logger.warning(f"❌ Failed to get replies for comment {comment_id}: {replies_resp.status_code}")
                
                logger.info(f"❌ No AI reply found for comment {comment_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking replies for comment {comment_id}: {e}")
            return False
    
    async def _generate_and_post_reply(
        self, 
        comment: Dict[str, Any], 
        access_token: str, 
        rule: AutomationRule,
        page_id: str
    ):
        """Generate AI reply and post it to Facebook."""
        try:
            comment_text = comment.get("message", "")
            commenter_name = comment["from"].get("name", "there")
            commenter_id = comment["from"].get("id", "")
            comment_id = comment["id"]
            
            # Get conversation context for more intelligent responses
            conversation_context = await self._get_conversation_context(comment_id, access_token, page_id)
            
            # Generate AI reply with user mention and context
            reply_text = await self._generate_ai_reply(
                comment_text=comment_text,
                commenter_name=commenter_name,
                template=rule.actions.get("response_template"),
                conversation_context=conversation_context
            )
            
            # Post reply to Facebook
            async with httpx.AsyncClient() as client:
                reply_resp = await client.post(
                    f"{self.graph_api_base}/{comment_id}/comments",
                    data={
                        "access_token": access_token,
                        "message": reply_text
                    }
                )
                
                if reply_resp.status_code == 200:
                    reply_data = reply_resp.json()
                    logger.info(f"✅ Auto-reply posted successfully to comment {comment_id}")
                    logger.info(f"📝 Reply: {reply_text}")
                    logger.info(f"💬 Context: {conversation_context}")
                    
                    # Update rule statistics
                    rule.success_count += 1
                    rule.last_success_at = datetime.utcnow()
                    
                else:
                    logger.error(f"❌ Failed to post auto-reply: {reply_resp.text}")
                    rule.error_count += 1
                    rule.last_error_at = datetime.utcnow()
                    rule.last_error_message = reply_resp.text
                    
        except Exception as e:
            logger.error(f"Error generating/posting reply: {e}")
            rule.error_count += 1
            rule.last_error_at = datetime.utcnow()
            rule.last_error_message = str(e)
    
    async def _generate_ai_reply(
        self, 
        comment_text: str, 
        commenter_name: str, 
        template: Optional[str] = None,
        conversation_context: str = ""
    ) -> str:
        """Generate AI reply mentioning the commenter."""
        try:
            # Create a context for the AI
            context = f"Comment by {commenter_name}: {comment_text}"
            if conversation_context:
                context += f" | Conversation context: {conversation_context}"
            
            # Use the template if provided, otherwise use a default approach
            if template:
                # Use template as a guide for AI
                ai_prompt = f"""
                Generate a friendly, engaging reply to this comment. 
                The reply should mention the commenter by name and be contextual to their comment.
                
                Template guide: {template}
                Comment: {comment_text}
                Commenter: {commenter_name}
                Conversation context: {conversation_context}
                
                Generate a natural, conversational reply that mentions the commenter.
                Keep it under 200 characters and use appropriate emojis sparingly.
                If this is a continuing conversation, make the response feel natural and contextual.
                """
            else:
                # Use default AI approach for contextual conversation
                ai_prompt = f"""
                Generate a friendly, engaging reply to this Facebook comment.
                The reply should:
                1. Mention the commenter by name (e.g., "@{commenter_name}" or "Hey {commenter_name}")
                2. Be contextual and relevant to their comment
                3. Be warm, professional, and encouraging
                4. Keep it under 200 characters
                5. Use appropriate emojis sparingly
                6. Feel natural and conversational
                7. If this is a continuing conversation, reference the context appropriately
                
                Comment: {comment_text}
                Commenter: {commenter_name}
                Conversation context: {conversation_context}
                
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

    async def _get_conversation_context(self, comment_id: str, access_token: str, page_id: str) -> str:
        """
        Get conversation context for more intelligent AI responses.
        Returns a summary of the conversation thread.
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get the comment and its replies
                comment_resp = await client.get(
                    f"{self.graph_api_base}/{comment_id}",
                    params={
                        "access_token": access_token,
                        "fields": "message,from,parent"
                    }
                )
                
                if comment_resp.status_code != 200:
                    return ""
                
                comment_data = comment_resp.json()
                conversation_context = []
                
                # Add the current comment
                commenter_name = comment_data.get("from", {}).get("name", "User")
                comment_text = comment_data.get("message", "")
                conversation_context.append(f"{commenter_name}: {comment_text}")
                
                # If it's a reply, get the parent comment context
                if comment_data.get("parent"):
                    parent_id = comment_data["parent"]["id"]
                    parent_resp = await client.get(
                        f"{self.graph_api_base}/{parent_id}",
                        params={
                            "access_token": access_token,
                            "fields": "message,from"
                        }
                    )
                    
                    if parent_resp.status_code == 200:
                        parent_data = parent_resp.json()
                        parent_from = parent_data.get("from", {})
                        parent_name = parent_from.get("name", "Unknown")
                        parent_message = parent_data.get("message", "")
                        
                        # Check if parent is from our page (AI response)
                        if parent_from.get("id") == page_id:
                            conversation_context.insert(0, f"AI: {parent_message}")
                        else:
                            conversation_context.insert(0, f"{parent_name}: {parent_message}")
                
                return " | ".join(conversation_context)
                
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""


# Create a singleton instance
auto_reply_service = AutoReplyService() 