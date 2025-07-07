import logging
from groq import Groq
from typing import Optional, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GroqService:
    """Service for AI content generation using Groq API."""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Groq client."""
        try:
            if not settings.groq_api_key:
                logger.warning("Groq API key not configured")
                return
            
            self.client = Groq(api_key=settings.groq_api_key)
            logger.info("Groq client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None
    
    async def generate_facebook_post(
        self, 
        prompt: str, 
        content_type: str = "post",
        max_length: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate Facebook post content using Groq AI.
        
        Args:
            prompt: User's input prompt
            content_type: Type of content (post, comment, reply)
            max_length: Maximum character length for the content
            
        Returns:
            Dict containing generated content and metadata
        """
        if not self.client:
            raise Exception("Groq client not initialized. Please check your API key configuration.")
        
        try:
            # Construct system prompt for Facebook content generation
            system_prompt = self._get_facebook_system_prompt(content_type, max_length)
            
            # Generate content using Groq
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Fast and efficient model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                top_p=0.9,
                stream=False
            )
            
            generated_content = completion.choices[0].message.content.strip()
            
            # Validate content length
            if len(generated_content) > max_length:
                generated_content = generated_content[:max_length-3] + "..."
            
            return {
                "content": generated_content,
                "model_used": "llama-3.1-8b-instant",
                "tokens_used": completion.usage.total_tokens if completion.usage else 0,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating content with Groq: {e}")
            return {
                "content": f"I'd love to share thoughts about {prompt}! What an interesting topic to explore.",
                "model_used": "fallback",
                "tokens_used": 0,
                "success": False,
                "error": str(e)
            }
    
    def _get_facebook_system_prompt(self, content_type: str, max_length: int) -> str:
        """Get system prompt based on content type."""
        base_prompt = f"""You are a regular person sharing content on Facebook in a natural, conversational way.

CRITICAL: Generate ONLY the post content. Do not include any headers, titles, footers, or explanatory text.

Guidelines:
- Write like a real person would naturally speak
- Keep under {max_length} characters
- Use casual, conversational tone
- Include 2-3 relevant emojis naturally in the text
- Write as if you're sharing with friends
- Make it feel spontaneous and authentic
- Avoid corporate or robotic language
- No hashtags unless specifically requested
- Start directly with the content, no introductions

"""
        
        if content_type == "post":
            return base_prompt + """
Write natural Facebook post content that:
- Feels like a real person wrote it
- Flows naturally without forced structure
- Includes personal touches or relatable experiences
- Asks questions naturally in conversation style
- Sounds like something you'd actually say to friends

REMEMBER: Output ONLY the post text. No "Here's your post:" or similar prefixes.
"""
        elif content_type == "comment":
            return base_prompt + """
Write a natural comment response that:
- Sounds like genuine human conversation
- Shows authentic interest or support
- Responds directly to what was said
- Uses casual language

REMEMBER: Output ONLY the comment text.
"""
        else:
            return base_prompt + "Write natural, human-like social media content. Output ONLY the content text."
    
    async def generate_auto_reply(
        self, 
        original_comment: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate automatic reply to Facebook comments.
        
        Args:
            original_comment: The comment to reply to
            context: Additional context about the post/brand
            
        Returns:
            Dict containing generated reply and metadata
        """
        if not self.client:
            return {
                "content": "Thank you for your comment! We appreciate your engagement.",
                "model_used": "fallback",
                "success": False,
                "error": "Groq client not initialized"
            }
        
        try:
            system_prompt = """You are a friendly customer service representative responding to Facebook comments.

Guidelines:
- Be warm, professional, and helpful
- Keep responses under 200 characters
- Acknowledge the commenter's input
- Provide value when possible
- Be conversational but professional
- Use appropriate emojis sparingly
- Always be positive and helpful

Generate a personalized response to the following comment:"""
            
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Comment: {original_comment}\nContext: {context or 'General social media page'}"}
                ],
                max_tokens=100,
                temperature=0.6,
                stream=False
            )
            
            reply_content = completion.choices[0].message.content.strip()
            
            return {
                "content": reply_content,
                "model_used": "llama-3.1-8b-instant",
                "tokens_used": completion.usage.total_tokens if completion.usage else 0,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating auto-reply with Groq: {e}")
            return {
                "content": "Thank you for your comment! We appreciate your engagement. 😊",
                "model_used": "fallback",
                "tokens_used": 0,
                "success": False,
                "error": str(e)
            }
    
    async def generate_instagram_post(
        self,
        prompt: str,
        max_length: int = 2200
    ) -> Dict[str, Any]:
        """
        Generate Instagram post caption using Groq AI.
        
        Args:
            prompt: User's input prompt
            max_length: Maximum character length for the caption
            
        Returns:
            Dict containing generated content and metadata
        """
        if not self.client:
            raise Exception("Groq client not initialized. Please check your API key configuration.")
        
        try:
            # Construct system prompt for Instagram content generation
            system_prompt = f"""You are a professional social media content creator specializing in Instagram posts.

Your task is to create engaging, authentic, and platform-appropriate Instagram captions based on the user's prompt.

Guidelines:
- Keep content under {max_length} characters
- Use a conversational, authentic tone that fits Instagram culture
- Include relevant emojis naturally throughout (Instagram users love emojis)
- Make it visually engaging with line breaks for readability
- Include relevant hashtags (5-15 hashtags is ideal for Instagram)
- Create engaging hooks in the first line
- Include a call-to-action when appropriate
- Make it feel personal and relatable
- Focus on storytelling and visual description
- Encourage engagement (comments, likes, saves, shares)

Instagram-specific best practices:
- Use line breaks to create visual appeal
- Include a mix of popular and niche hashtags
- Ask questions to encourage comments
- Use Instagram slang and culture appropriately
- Create content that's both entertaining and valuable

Create a complete Instagram caption that includes the main content and relevant hashtags at the end."""

            # Generate content using Groq
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Fast and efficient model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,  # More tokens for Instagram captions with hashtags
                temperature=0.8,  # Slightly higher for more creative content
                top_p=0.9,
                stream=False
            )
            
            generated_content = completion.choices[0].message.content.strip()
            
            # Validate content length
            if len(generated_content) > max_length:
                generated_content = generated_content[:max_length-3] + "..."
            
            return {
                "content": generated_content,
                "model_used": "llama-3.1-8b-instant",
                "tokens_used": completion.usage.total_tokens if completion.usage else 0,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating Instagram content with Groq: {e}")
            return {
                "content": f"✨ Excited to share this amazing moment! {prompt} ✨\n\n#instagram #socialmedia #content #amazing #life #photography #beautiful #inspiration #daily #mood",
                "model_used": "fallback",
                "tokens_used": 0,
                "success": False,
                "error": str(e)
            }

    def is_available(self) -> bool:
        """Check if Groq service is available."""
        return self.client is not None


# Global service instance
groq_service = GroqService() 