import os
import sys
from pathlib import Path


def setup_stability_ai():
    print("🎨 Setting up Stability AI Image Generation")
    print("=" * 50)
    
    # Check if API key is provided as command line argument
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("\n❌ Error: Stability AI API key is required")
        print("\nUsage:")
        print("  python scripts/setup_stability_ai.py <YOUR_API_KEY>")
        print("\nExample:")
        print("  python scripts/setup_stability_ai.py sk-1WPMEBzP8fp4yvFhvGf87E39GC23l280GOGFyFCk4fKr5gGx")
        print("\nOr set the environment variable directly:")
        print("  export STABILITY_API_KEY=sk-1WPMEBzP8fp4yvFhvGf87E39GC23l280GOGFyFCk4fKr5gGx")
        return False
    
    # Set the environment variable
    os.environ["STABILITY_API_KEY"] = api_key
    
    print(f"✅ Stability AI API key configured")
    print(f"✅ Key starts with: {api_key[:8]}...")
    
    # Test the configuration
    print("\n🧪 Testing Stability AI configuration...")
    
    try:
        from app.services.fb_stability_service import stability_service
        
        if stability_service.is_configured():
            print("✅ Stability AI service is properly configured")
            
            # Create temp_images directory
            temp_dir = Path("temp_images")
            temp_dir.mkdir(exist_ok=True)
            print("✅ Image storage directory created")
            
            print("\n🎉 Setup completed successfully!")
            print("\n📝 Available endpoints:")
            print("  POST /api/social/facebook/generate-image")
            print("    - Generate an image without posting")
            print("  POST /api/social/facebook/create-post")
            print("    - Unified endpoint for all Facebook post types")
            print("    - Supports text-only, AI-generated text, AI-generated images, and pre-generated images")
            
            print("\n🔧 Configuration summary:")
            print(f"  - Stability AI: ✅ Configured")
            print(f"  - Image storage: ✅ temp_images/ directory")
            print(f"  - Image serving: ✅ http://localhost:8000/temp_images/")
            
            print("\n💡 Usage tips:")
            print("  - Images are optimized for Facebook post dimensions")
            print("  - Supported post types: feed, story, square, cover, profile")
            print("  - Images are temporarily stored and served via HTTP")
            print("  - Use descriptive prompts for better image quality")
            
            return True
        else:
            print("❌ Stability AI service configuration failed")
            print("Please check your API key and try again")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def print_env_setup():
    """Print environment setup instructions."""
    print("\n📋 Environment Setup Instructions:")
    print("=" * 40)
    print("Add the following to your environment:")
    print()
    print("For Unix/Linux/macOS (.bashrc, .zshrc, etc.):")
    print("  export STABILITY_API_KEY=sk-1WPMEBzP8fp4yvFhvGf87E39GC23l280GOGFyFCk4fKr5gGx")
    print()
    print("For Windows (Command Prompt):")
    print("  set STABILITY_API_KEY=sk-1WPMEBzP8fp4yvFhvGf87E39GC23l280GOGFyFCk4fKr5gGx")
    print()
    print("For Windows (PowerShell):")
    print("  $env:STABILITY_API_KEY='sk-1WPMEBzP8fp4yvFhvGf87E39GC23l280GOGFyFCk4fKr5gGx'")
    print()
    print("Or create a .env file in the backend directory:")
    print("  STABILITY_API_KEY=sk-1WPMEBzP8fp4yvFhvGf87E39GC23l280GOGFyFCk4fKr5gGx")


if __name__ == "__main__":
    if not setup_stability_ai():
        print_env_setup()
        sys.exit(1)
    
    print("\n🚀 You can now start the server with:")
    print("  python run.py")
    print("\n🌐 API documentation will be available at:")
    print("  http://localhost:8000/docs") 