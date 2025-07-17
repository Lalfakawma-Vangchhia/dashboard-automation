import logging
from groq import Groq
from typing import Optional, Dict, Any
from app.config import get_settings
import re

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
        max_length: int = 500
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
                model="llama3-70b-8192",  # Fast and efficient model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.6,
                top_p=0.9,
                stream=False
            )
            
            generated_content = completion.choices[0].message.content.strip()
            generated_content = strip_outer_quotes(generated_content)
            
            # Validate content length
            if len(generated_content) > max_length:
                generated_content = generated_content[:max_length-3] + "..."
            
            return {
                "content": generated_content,
                "model_used": "llama3-70b-8192",
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
        base_prompt = f"""IMPORTANT: If you include a quote, DO NOT use any quotation marks (" or ') around it. Write the quote as plain text. It should not start or end with quotation marks.

BAD: As Nelson Mandela once said, "The greatest glory in living lies not in never falling, but in rising every time we fall."
GOOD: As Nelson Mandela once said, The greatest glory in living lies not in never falling, but in rising every time we fall.

BAD: "Just a Thursday chilling, rest of the week will be a day for me."
GOOD: Just a Thursday chilling, rest of the week will be a day for me.

You are a regular person sharing content on Facebook in a natural, conversational way.

CRITICAL: Generate ONLY the post content. Do not include any headers, titles, footers, or explanatory text.

Guidelines:
- Write like a real person would naturally speak
- Keep under {max_length} characters
- Use casual, conversational tone
- Include 2-3 relevant emojis naturally in the text, but do not keep too much.
- Write as if you're sharing with friends
- Make it feel spontaneous and authentic
- Avoid corporate or robotic language
- Use newline before hashtags 
- Start directly with the content, no introductions
- Start with capital letter
- End with period
"""
        
        if content_type == "post":
            return base_prompt + """
Write natural Facebook post content that:
- Do not use quotation mark(" ") at the beginning or end of the caption
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
                model="llama3-70b-8192",
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
        max_length: int = 250
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
            system_prompt = f"""You are a creative social media content writer specializing in Instagram captions.

Your mission:
- Generate a platform-appropriate, engaging Instagram caption based on the user's prompt.
- Keep the total length under {max_length} characters.
- Compose the caption in 1–2 paragraphs. Each paragraph should contain a single, clear sentence and use line breaks for readability.
- Write in an authentic, conversational tone that suits Instagram culture.
- Naturally incorporate **2–3 relevant emojis** to enhance emotional impact.
- Add **2–5 hashtags** (a mix of popular and niche) at the end.
- When relevant, include a call-to-action to boost engagement (comment, like, save, share).
- Personalize the caption: make it relatable, visually evocative, and encourage followers to interact.
- Avoid using headers, footers, or special characters (like asterisks) to start or end the caption.
- No dense blocks of text; use line breaks to create visual interest.
- Employ Instagram slang appropriately, but stay true to your brand voice and audience.
- Where possible, ask a question or use statements that invite comments.
- Make all content entertaining, visually descriptive, and valuable for Instagram followers.

Example:
To anyone who feels behind – remember,

slow progress is still progress. Keep showing up.

#civilservant #civilservicesexam #civilservices #mpsc #upscexam

Create a complete Instagram caption that includes the main message and hashtags at the end."""

            # Generate content using Groq
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",  # Fast and efficient model
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
            generated_content = strip_outer_quotes(generated_content)
            
            # Validate content length
            if len(generated_content) > max_length:
                generated_content = generated_content[:max_length-3] + "..."
            
            return {
                "content": generated_content,
                "model_used": "llama3-70b-8192",
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

    async def generate_caption_with_custom_strategy(
        self,
        custom_strategy: str,
        context: str = "",
        max_length: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate caption using a custom strategy template.
        
        Args:
            custom_strategy: The custom strategy template provided by the user
            context: Additional context or topic for the caption
            max_length: Maximum character length for the caption
            
        Returns:
            Dict containing generated content and metadata
        """
        if not self.client:
            raise Exception("Groq client not initialized. Please check your API key configuration.")
        
        try:
            # Construct system prompt using the custom strategy
            system_prompt = f"""You are a professional social media content creator.

Your task is to create engaging social media captions based on the user's custom strategy template.

Custom Strategy Template:
{custom_strategy}

Guidelines:
- Keep content under {max_length} characters
- Follow the custom strategy template provided
- Use a conversational, authentic tone
- Include relevant emojis naturally
- Make it engaging and shareable
- Create content that encourages interaction
- Be creative while staying true to the strategy

Generate a caption that follows the custom strategy template."""

            # Create the user prompt with context
            user_prompt = f"Create a social media caption for: {context}" if context else "Create a social media caption following the custom strategy."

            # Generate content using Groq
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                top_p=0.9,
                stream=False
            )
            
            generated_content = completion.choices[0].message.content.strip()
            generated_content = strip_outer_quotes(generated_content)
            
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
            logger.error(f"Error generating caption with custom strategy: {e}")
            return {
                "content": f"Excited to share this amazing content! {context} ✨",
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

def strip_outer_quotes(text: str) -> str:
    # Remove leading/trailing single or double quotes, and any leading/trailing whitespace/newlines
    return re.sub(r'^[\'"]+|[\'"]+$', '', text).strip() 