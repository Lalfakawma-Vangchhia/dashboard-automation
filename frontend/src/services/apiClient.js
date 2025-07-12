// API Client for Backend Integration
class ApiClient {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
    this.token = localStorage.getItem('authToken');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      console.log(`Making API request to: ${url}`);
      
      // Dynamic timeout – longer for AI image endpoints which can take ~30-60 s
      let timeoutMs = 15000; // default 15 s
      const longRunningEndpoints = [
        '/facebook/generate-image',
        '/facebook/post-with-image',
        '/facebook/ai-post-with-image',
        '/facebook/post-with-pre-generated-image',
        '/facebook/create-post',  // Add the unified Facebook post endpoint
        '/instagram/post-carousel',  // Add Instagram carousel endpoint
        '/social/instagram/upload-video',  // Add video upload endpoint
        '/social/instagram/upload-image',  // Add image upload endpoint
        '/api/social/instagram/upload-video',  // Alternative video upload path
        '/api/social/instagram/upload-image',   // Alternative image upload path
        '/api/social/instagram/generate-carousel',  // AI carousel generation
        '/api/social/instagram/generate-image',     // AI image generation
        '/api/social/instagram/generate-caption',   // AI caption generation
        '/api/social/facebook/generate-image',      // Facebook AI image generation
        '/api/ai/generate-content',                 // General AI content generation
        '/api/social/instagram/create-post',        // Instagram post creation
        '/api/social/facebook/create-post',         // Facebook post creation
        '/api/social/instagram/post-carousel',      // Instagram carousel posting
        '/api/social/instagram/post',               // Instagram post endpoint
        '/api/social/facebook/post',                // Facebook post endpoint
        '/api/ai/',                                 // All AI endpoints
        '/generate',                                // Any generation endpoint
        '/carousel',                                // Carousel operations
        '/upload'                                   // Upload operations
      ];
      
      // Check for specific high-load operations
      const isAIGeneration = endpoint.includes('generate') || endpoint.includes('ai/');
      const isCarouselOperation = endpoint.includes('carousel');
      const isUploadOperation = endpoint.includes('upload');
      
      if (longRunningEndpoints.some(ep => endpoint.includes(ep))) {
        if (isAIGeneration || isCarouselOperation) {
          timeoutMs = 300000; // 5 minutes for AI generation and carousel operations
        } else if (isUploadOperation) {
          timeoutMs = 180000; // 3 minutes for upload operations
        } else {
          timeoutMs = 120000; // 2 minutes for other long-running operations
        }
      }

      console.log(`⏱ Using timeout ${timeoutMs/1000}s for this request`);
      console.log(`🔍 Endpoint: ${endpoint}`);
      console.log(`🔍 Is AI Generation: ${isAIGeneration}`);
      console.log(`🔍 Is Carousel Operation: ${isCarouselOperation}`);
      console.log(`🔍 Is Upload Operation: ${isUploadOperation}`);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        console.error(`⏰ Timeout after ${timeoutMs/1000}s for endpoint: ${endpoint}`);
        controller.abort();
      }, timeoutMs);
      
      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (e) {
          console.warn('Failed to parse error response as JSON');
        }
        
        // Handle 401 Unauthorized specifically
        if (response.status === 401) {
          console.warn('Authentication failed - token may be expired');
          this.setToken(null); // Clear invalid token
          throw new Error('Could not validate credentials - please log in again');
        }
        
        // Handle validation errors (422)
        if (response.status === 422 && errorData.detail) {
          // Handle Pydantic validation errors
          if (Array.isArray(errorData.detail)) {
            const validationErrors = errorData.detail.map(err => 
              `${err.loc.join('.')}: ${err.msg}`
            ).join(', ');
            throw new Error(`Validation Error: ${validationErrors}`);
          } else {
            throw new Error(errorData.detail);
          }
        }
        
        // Extract error message properly
        let errorMessage = 'Unknown error occurred';
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        throw new Error(errorMessage);
      }

      const responseData = await response.json();
      console.log(`API response from ${endpoint}:`, responseData);
      return responseData;
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error(`API request timeout for ${endpoint}`);
        throw new Error('Request timed out - backend server may not be responding');
      }
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Test connection to backend
  async testConnection() {
    try {
      const response = await fetch(`${this.baseURL.replace('/api', '')}/health`);
      return response.ok;
    } catch (error) {
      console.error('Backend connection test failed:', error);
      return false;
    }
  }

  // Authentication endpoints
  async register(userData) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async login(email, password) {
    const response = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }

  async getCurrentUser() {
    return this.request('/api/auth/me');
  }

  async logout() {
    this.setToken(null);
  }

  // Social Media endpoints (Replace Make.com webhooks)
  async getFacebookStatus() {
    return this.request('/api/social/facebook/status');
  }

  async connectFacebook(accessToken, userId, pages = []) {
    return this.request('/api/social/facebook/connect', {
      method: 'POST',
      body: JSON.stringify({
        access_token: accessToken,
        user_id: userId,
        pages: pages,
      }),
    });
  }

  async refreshFacebookTokens() {
    return this.request('/api/social/facebook/refresh-tokens', {
      method: 'POST',
    });
  }

  async logoutFacebook() {
    return this.request('/api/social/facebook/logout', {
      method: 'POST',
    });
  }

  // (No scheduled post methods here anymore)

  async getSocialPosts(platform = null, limit = 50) {
    const params = new URLSearchParams();
    if (platform) params.append('platform', platform);
    params.append('limit', limit.toString());
    
    return this.request(`/api/social/posts?${params.toString()}`);
  }

  async connectInstagram(accessToken) {
    return this.request('/api/social/instagram/connect', {
      method: 'POST',
      body: JSON.stringify({
        access_token: accessToken
      }),
    });
  }

  // REPLACE Make.com auto-post webhook
  async createFacebookPost(pageId, message, postType = 'post-auto', image = null) {
    return this.request('/api/social/facebook/post', {
      method: 'POST',
      body: JSON.stringify({
        page_id: pageId,
        message: message,
        post_type: postType,
        image: image,
      }),
    });
  }

  // Instagram post creation
  async createInstagramPost(data) {
    // Accept either FormData or an object for flexibility
    if (data instanceof FormData) {
      // FormData for file uploads - use custom headers to avoid CORS issues
      const url = `${this.baseURL}/api/social/instagram/post`;
      const config = {
        method: 'POST',
        body: data,
      };

      // Add authorization header manually for FormData
      if (this.token) {
        config.headers = {
          'Authorization': `Bearer ${this.token}`
        };
      }

      try {
        console.log(`🔍 DEBUG: FormData upload to ${url}`);
        const response = await fetch(url, config);
        
        if (!response.ok) {
          let errorData = {};
          try {
            errorData = await response.json();
          } catch (e) {
            console.warn('Failed to parse error response as JSON');
          }
          
          let errorMessage = 'Unknown error occurred';
          if (typeof errorData === 'string') {
            errorMessage = errorData;
          } else if (errorData.error) {
            errorMessage = errorData.error;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          } else {
            errorMessage = `HTTP ${response.status}: ${response.statusText}`;
          }
          
          throw new Error(errorMessage);
        }

        const responseData = await response.json();
        console.log(`FormData upload response:`, responseData);
        return responseData;
      } catch (error) {
        console.error(`FormData upload error:`, error);
        throw error;
      }
    } else {
      // JSON for text-only posts or AI generation
      return this.request('/api/social/instagram/post', {
        method: 'POST',
        body: JSON.stringify({
          instagram_user_id: data.instagram_user_id,
          caption: data.caption,
          image_url: data.image_url,
          post_type: data.post_type || 'manual',
          use_ai: data.use_ai || false,
          prompt: data.prompt
        }),
      });
    }
  }

  // Get Instagram media
  async getInstagramMedia(instagramUserId, limit = 25) {
    return this.request(`/api/social/instagram/media/${instagramUserId}?limit=${limit}`);
  }

  // Upload image to Cloudinary for Instagram
  async uploadImageToCloudinary(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Use custom FormData upload method
    const url = `${this.baseURL}/api/social/instagram/upload-image`;
    const config = {
      method: 'POST',
      body: formData,
    };

    // Add authorization header manually for FormData
    if (this.token) {
      config.headers = {
        'Authorization': `Bearer ${this.token}`
      };
      console.log('🔍 DEBUG: Token found, adding Authorization header');
    } else {
      console.log('🔍 DEBUG: No token found!');
      console.log('🔍 DEBUG: this.token:', this.token);
      console.log('🔍 DEBUG: localStorage authToken:', localStorage.getItem('authToken'));
    }

    try {
      console.log(`🔍 DEBUG: Uploading image to Cloudinary via ${url}`);
      console.log(`🔍 DEBUG: Request config:`, config);
      const response = await fetch(url, config);
      
      console.log(`🔍 DEBUG: Response status:`, response.status);
      console.log(`🔍 DEBUG: Response headers:`, Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
          console.log(`🔍 DEBUG: Error response data:`, errorData);
        } catch (e) {
          console.warn('Failed to parse error response as JSON');
        }
        
        let errorMessage = 'Unknown error occurred';
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        throw new Error(errorMessage);
      }

      const responseData = await response.json();
      console.log(`FormData upload response:`, responseData);
      return responseData;
    } catch (error) {
      console.error(`FormData upload error:`, error);
      throw error;
    }
  }

  // Upload video to Cloudinary for Instagram
  async uploadVideoToCloudinary(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Use custom FormData upload method
    const url = `${this.baseURL}/api/social/instagram/upload-video`;
    const config = {
      method: 'POST',
      body: formData,
    };

    // Add authorization header manually for FormData
    if (this.token) {
      config.headers = {
        'Authorization': `Bearer ${this.token}`
      };
    }

    try {
      console.log(`🔍 DEBUG: Uploading video to Cloudinary via ${url}`);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (e) {
          console.warn('Failed to parse error response as JSON');
        }
        
        let errorMessage = 'Unknown error occurred';
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        throw new Error(errorMessage);
      }

      const responseData = await response.json();
      console.log(`FormData upload response:`, responseData);
      return responseData;
    } catch (error) {
      console.error(`FormData upload error:`, error);
      throw error;
    }
  }

  // Google Drive integration for Instagram
  async getGoogleDriveFiles(mimeType = null) {
    const params = mimeType ? `?mime_type=${mimeType}` : '';
    return this.request(`/api/google-drive/files${params}`);
  }

  async downloadGoogleDriveFile(fileId) {
    return this.request(`/api/google-drive/download/${fileId}`);
  }

  async getGoogleDriveAuth() {
    return this.request('/api/google-drive/auth');
  }

  async getGoogleDriveStatus() {
    return this.request('/api/google-drive/status');
  }

  async getGoogleDriveAuthorizeUrl() {
    return this.request('/api/google-drive/authorize');
  }

  async getGoogleDriveToken() {
    const response = await this.request('/api/google-drive/token');
    return {
      access_token: response.access_token
    };
  }

  async disconnectGoogleDrive() {
    return this.request('/api/google-drive/disconnect', {
      method: 'POST'
    });
  }

  // Generate Instagram image using Stability AI
  async generateInstagramImage(imagePrompt, postType = 'feed') {
    return this.request('/api/social/instagram/generate-image', {
      method: 'POST',
      body: JSON.stringify({
        image_prompt: imagePrompt,
        post_type: postType
      }),
    });
  }

  // Unified Instagram post creation endpoint
  async createUnifiedInstagramPost(instagramUserId, options = {}) {
    const {
      caption = null,
      content_prompt = null,
      image_prompt = null,
      image_url = null,
      image_filename = null,
      video_url = null,
      video_filename = null,
      post_type = 'feed',
      use_ai_text = false,
      use_ai_image = false,
      media_type = 'image'
    } = options;

    return this.request('/api/social/instagram/create-post', {
      method: 'POST',
      body: JSON.stringify({
        instagram_user_id: instagramUserId,
        caption: caption,
        content_prompt: content_prompt,
        image_prompt: image_prompt,
        image_url: image_url,
        image_filename: image_filename,
        video_url: video_url,
        video_filename: video_filename,
        post_type: post_type,
        use_ai_text: use_ai_text,
        use_ai_image: use_ai_image,
        media_type: media_type
      }),
    });
  }

  // REPLACE Make.com auto-reply webhook
  async toggleAutoReply(pageId, enabled, responseTemplate = 'Thank you for your comment!', selectedPostIds = []) {
    return this.request('/api/social/facebook/auto-reply', {
      method: 'POST',
      body: JSON.stringify({
        enabled: enabled,
        page_id: pageId,
        response_template: responseTemplate,
        selected_post_ids: selectedPostIds,
      }),
    });
  }

  // Get posts for auto-reply selection
  async getPostsForAutoReply(pageId) {
    return this.request(`/social/facebook/posts-for-auto-reply/${pageId}`);
  }

  // Instagram Auto-Reply Methods
  async toggleInstagramAutoReply(instagramUserId, enabled, responseTemplate = 'Thank you for your comment!', selectedPostIds = []) {
    return this.request('/api/social/instagram/auto-reply', {
      method: 'POST',
      body: JSON.stringify({
        enabled,
        instagram_user_id: instagramUserId,
        response_template: responseTemplate,
        selected_post_ids: selectedPostIds
      }),
    });
  }

  async getInstagramPostsForAutoReply(instagramUserId) {
    return this.request(`/api/social/instagram/posts-for-auto-reply/${instagramUserId}`);
  }

  async syncInstagramPosts(instagramUserId) {
    return this.request(`/api/social/instagram/sync-posts/${instagramUserId}`, {
      method: 'POST',
    });
  }

  // Get connected social accounts
  async getSocialAccounts() {
    return this.request('/api/social/accounts');
  }

  // Get posts
  async getPosts(platform = null, status = null, limit = 50) {
    const params = new URLSearchParams();
    if (platform) params.append('platform', platform);
    if (status) params.append('status', status);
    if (limit) params.append('limit', limit.toString());
    
    const query = params.toString();
    return this.request(`/api/social/posts${query ? `?${query}` : ''}`);
  }

  // Get automation rules
  async getAutomationRules(platform = null, ruleType = null) {
    const params = new URLSearchParams();
    if (platform) params.append('platform', platform);
    if (ruleType) params.append('rule_type', ruleType);
    
    const query = params.toString();
    return this.request(`/api/social/automation-rules${query ? `?${query}` : ''}`);
  }

  // Generate content using Groq API
  async generateContent(prompt) {
    return this.request('/api/ai/generate-content', {
      method: 'POST',
      body: JSON.stringify({
        prompt: prompt,
        platform: 'instagram',
        content_type: 'caption'
      }),
    });
  }

  async generateInstagramCaption(prompt) {
    try {
      console.log('Generating Instagram caption with prompt:', prompt);
      
      const response = await this.request('/api/social/instagram/generate-caption', {
        method: 'POST',
        body: JSON.stringify({ prompt })
      });
      
      console.log('Instagram caption generation response:', response);
      return response;
    } catch (error) {
      console.error('Error generating Instagram caption:', error);
      throw error;
    }
  }

  async generateCaptionWithStrategy(customStrategy, context = "", maxLength = 2000) {
    try {
      console.log('Generating caption with custom strategy:', { customStrategy, context, maxLength });
      
      const response = await this.request('/api/social/generate-caption-with-strategy', {
        method: 'POST',
        body: JSON.stringify({ 
          custom_strategy: customStrategy,
          context: context,
          max_length: maxLength
        })
      });
      
      console.log('Custom strategy caption generation response:', response);
      return response;
    } catch (error) {
      console.error('Error generating caption with custom strategy:', error);
      throw error;
    }
  }

  async generateBulkCaptions(customStrategy, contexts, maxLength = 2000) {
    try {
      console.log('Generating bulk captions with custom strategy:', { customStrategy, contexts, maxLength });
      
      const response = await this.request('/api/social/generate-bulk-captions', {
        method: 'POST',
        body: JSON.stringify({ 
          custom_strategy: customStrategy,
          contexts: contexts,
          max_length: maxLength
        })
      });
      
      console.log('Bulk caption generation response:', response);
      return response;
    } catch (error) {
      console.error('Error generating bulk captions:', error);
      throw error;
    }
  }

  // Generate Instagram carousel
  async generateInstagramCarousel(prompt, count = 3) {
    try {
      const response = await this.request('/api/social/instagram/generate-carousel', {
        method: 'POST',
        body: JSON.stringify({ 
          image_prompt: prompt,
          count: count,
          post_type: 'feed'
        })
      });
      return response;
    } catch (error) {
      console.error('Error generating Instagram carousel:', error);
      throw error;
    }
  }

  // Post Instagram carousel
  async postInstagramCarousel(instagramUserId, caption, imageUrls) {
    try {
      const response = await this.request('/api/social/instagram/post-carousel', {
        method: 'POST',
        body: JSON.stringify({
          instagram_user_id: instagramUserId,
          caption: caption,
          image_urls: imageUrls
        })
      });
      return response;
    } catch (error) {
      console.error('Error posting Instagram carousel:', error);
      throw error;
    }
  }

  // Unified Facebook post creation endpoint
  async createFacebookPost(pageId, options = {}) {
    const {
      textContent = null,
      contentPrompt = null,
      imagePrompt = null,
      imageUrl = null,
      imageFilename = null,
      videoUrl = null,
      videoFilename = null,
      postType = 'feed',
      useAIText = false,
      useAIImage = false
    } = options;

    return this.request('/api/social/facebook/create-post', {
      method: 'POST',
      body: JSON.stringify({
        page_id: pageId,
        text_content: textContent,
        content_prompt: contentPrompt,
        image_prompt: imagePrompt,
        image_url: imageUrl,
        image_filename: imageFilename,
        video_url: videoUrl,
        video_filename: videoFilename,
        post_type: postType,
        use_ai_text: useAIText,
        use_ai_image: useAIImage
      }),
    });
  }

  // Stability AI Image Generation endpoint (standalone)
  async generateFacebookImage(imagePrompt, postType = 'feed') {
    return this.request('/api/social/facebook/generate-image', {
      method: 'POST',
      body: JSON.stringify({
        image_prompt: imagePrompt,
        post_type: postType
      }),
    });
  }

  // Get AI service status including Stability AI
  async getAIServiceStatus() {
    return this.request('/api/ai/status');
  }

  // Debug endpoint for Stability AI troubleshooting
  async debugStabilityAI() {
    return this.request('/api/social/debug/stability-ai-status');
  }

  // Debug endpoint for testing Facebook image posts
  async debugFacebookImagePost(pageId, message = "Test post from debug") {
    return this.request('/api/social/facebook/debug-image-post', {
      method: 'POST',
      body: JSON.stringify({
        page_id: pageId,
        message: message
      }),
    });
  }

  // Bulk Composer - Schedule multiple posts
  async bulkSchedulePosts(requestData) {
    try {
      console.log('Scheduling bulk posts:', requestData);
      
      const response = await this.request('/api/social/bulk-composer/schedule', {
        method: 'POST',
        body: JSON.stringify(requestData)
      });
      
      console.log('Bulk schedule response:', response);
      return response;
    } catch (error) {
      console.error('Error scheduling bulk posts:', error);
      throw error;
    }
  }

  // Bulk Composer - Get scheduled posts
  async getBulkComposerContent() {
    try {
      console.log('Getting bulk composer content...');
      
      const response = await this.request('/api/social/bulk-composer/content');
      
      console.log('Bulk composer content response:', response);
      return response;
    } catch (error) {
      console.error('Error getting bulk composer content:', error);
      throw error;
    }
  }

  // Bulk Composer - Update post caption
  async updateBulkComposerPost(postId, caption) {
    try {
      console.log('Updating bulk composer post:', postId, caption);
      
      const response = await this.request(`/api/social/bulk-composer/content/${postId}`, {
        method: 'PUT',
        body: JSON.stringify({ caption })
      });
      
      console.log('Update post response:', response);
      return response;
    } catch (error) {
      console.error('Error updating bulk composer post:', error);
      throw error;
    }
  }

  // Bulk Composer - Cancel/delete scheduled post
  async cancelBulkComposerPost(postId) {
    try {
      console.log('Canceling bulk composer post:', postId);
      
      const response = await this.request(`/api/social/bulk-composer/content/${postId}`, {
        method: 'DELETE'
      });
      
      console.log('Cancel post response:', response);
      return response;
    } catch (error) {
      console.error('Error canceling bulk composer post:', error);
      throw error;
    }
  }
}

const apiClient = new ApiClient();
export default apiClient;