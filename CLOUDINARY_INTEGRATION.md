# Cloudinary Integration in Scheduler Service

## Overview

This document describes the implementation of Cloudinary integration in the scheduler service to automatically generate AI images and upload them to Cloudinary when scheduled posts don't have media URLs.

## Implementation Details

### 1. Modified Files

#### `backend/app/services/scheduler_service.py`
- **Added imports**: `cloudinary_service`, `base64`, `io`
- **New method**: `generate_and_upload_image()` - Generates AI images and uploads to Cloudinary
- **New method**: `generate_and_upload_video()` - Placeholder for future video generation
- **Enhanced**: `execute_scheduled_instagram_post()` - Now automatically generates media when missing

#### `backend/app/services/cloudinary_service.py`
- **Improved**: `upload_image_with_instagram_transform()` - Added proper error handling and logging
- **Added**: Configuration checks and better error messages

### 2. How It Works

#### For Photo Posts:
1. When a scheduled post has no `image_url`, the scheduler automatically:
   - Generates an AI image using the post's prompt
   - Uploads the generated image to Cloudinary with Instagram-optimized transforms
   - Updates the scheduled post with the Cloudinary URL
   - Proceeds with posting to Instagram

#### For Carousel Posts:
1. When a scheduled post has no `media_urls`, the scheduler automatically:
   - Generates 3-5 AI images (based on prompt length) with variations
   - Uploads each image to Cloudinary
   - Updates the scheduled post with an array of Cloudinary URLs
   - Proceeds with posting to Instagram

#### For Reel Posts:
1. Currently requires a `video_url` to be provided
2. Future enhancement: Will support AI video generation

### 3. Cloudinary Configuration

The service requires these environment variables:
```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 4. Image Transformations

Images uploaded to Cloudinary are automatically transformed for Instagram:
- **Size**: 1080x1080 pixels (Instagram square format)
- **Crop**: Fill with auto gravity
- **Format**: JPG with auto quality
- **Folder**: "instagram" folder in Cloudinary

### 5. Error Handling

- **Configuration errors**: Graceful handling when Cloudinary is not configured
- **Generation errors**: Posts are marked as failed if image generation fails
- **Upload errors**: Posts are marked as failed if Cloudinary upload fails
- **Logging**: Comprehensive logging for debugging

## Usage Examples

### Creating a Scheduled Post Without Media

```python
# The scheduler will automatically generate and upload an image
scheduled_post = ScheduledPost(
    user_id=user.id,
    social_account_id=account.id,
    prompt="A beautiful sunset over mountains",
    post_type=PostType.PHOTO,
    scheduled_datetime=datetime.now() + timedelta(minutes=5),
    status="scheduled",
    is_active=True
    # No image_url provided - will be auto-generated
)
```

### Creating a Carousel Post Without Media

```python
# The scheduler will automatically generate 3-5 images
scheduled_post = ScheduledPost(
    user_id=user.id,
    social_account_id=account.id,
    prompt="Travel destinations around the world",
    post_type=PostType.CAROUSEL,
    scheduled_datetime=datetime.now() + timedelta(minutes=5),
    status="scheduled",
    is_active=True
    # No media_urls provided - will be auto-generated
)
```

## Testing

Run the test script to verify the integration:

```bash
cd automation-dashboard
python test_scheduler_cloudinary.py
```

## Future Enhancements

1. **Video Generation**: Implement AI video generation for reel posts
2. **Custom Prompts**: Allow users to specify custom image generation prompts
3. **Style Variations**: Add different artistic styles for image generation
4. **Batch Processing**: Optimize for generating multiple images simultaneously
5. **Caching**: Cache generated images to avoid regenerating similar content

## API Integration

The scheduler service works seamlessly with existing API endpoints:
- `/scheduler/save-posts` - Already has Cloudinary integration
- `/social/bulk-composer/schedule` - Handles media uploads
- `/social/instagram/bulk-schedule` - Supports media URLs

## Monitoring and Logging

The implementation includes comprehensive logging:
- Image generation progress
- Cloudinary upload status
- Error messages and debugging information
- Success confirmations with URLs

All logs are prefixed with emojis for easy identification:
- 🎨 Image generation
- ☁️ Cloudinary operations
- ✅ Success operations
- ❌ Error operations
- 🔄 Processing operations 