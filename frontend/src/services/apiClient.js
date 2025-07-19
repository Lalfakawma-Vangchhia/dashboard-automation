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
      let timeoutMs = 300000; // default  s
      const longRunningEndpoints = [
        '/facebook/generate-image',
        '/facebook/post-with-image',
        '/facebook/ai-post-with-image',
        '/facebook/post-with-pre-generated-image',
        '/facebook/create-post',  // Add the unified Facebook post endpoint
        '/instagram/post-carousel',  // Add Instagram carousel endpoint
        '/social/instagram/upload-video',  // Add video upload endpoint
        '/social/instagram/upload-image',  // Add image upload endpoint
        '/social/instagram/upload-video',  // Alternative video upload path
        '/social/instagram/upload-image',   // Alternative image upload path
        '/social/instagram/generate-carousel',  // AI carousel generation
        '/social/instagram/generate-image',     // AI image generation
        '/social/instagram/generate-caption',   // AI caption generation
        '/social/facebook/generate-image',      // Facebook AI image generation
        '/ai/generate-content',                 // General AI content generation
        '/social/instagram/create-post',        // Instagram post creation
        '/social/facebook/create-post',         // Facebook post creation
        '/social/instagram/post-carousel',      // Instagram carousel posting
        '/social/instagram/post',               // Instagram post endpoint
        '/social/facebook/post',                // Facebook post endpoint
        '/ai/',                                 // All AI endpoints
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
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  async logout() {
    this.setToken(null);
  }

  // Facebook endpoints
  async getFacebookStatus() {
    return this.request('/social/facebook/status');
  }

  async connectFacebook(accessToken, userId, pages = []) {
    return this.request('/social/facebook/connect', {
      method: 'POST',
      body: JSON.stringify({
        access_token: accessToken,
        user_id: userId,
        pages: pages
      }),
    });
  }

  async refreshFacebookTokens() {
    return this.request('/social/facebook/refresh-tokens', {
      method: 'POST',
    });
  }

  async logoutFacebook() {
    return this.request('/social/facebook/logout', {
      method: 'POST',
    });
  }

  // (No scheduled post methods here anymore)

  async getSocialPosts(platform = null, limit = 50, socialAccountId = null) {
    const params = new URLSearchParams();
    if (platform) params.append('platform', platform);
    params.append('limit', limit.toString());
    if (socialAccountId) params.append('social_account_id', socialAccountId);
    
    return this.request(`/api/social/posts?${params.toString()}`);
  }

  async connectInstagram(accessToken) {
    return this.request('/social/instagram/connect', {
      method: 'POST',
      body: JSON.stringify({
        access_token: accessToken
      }),
    });
  }

  async createInstagramPost(data) {
    return this.request('/social/instagram/post', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Get Instagram media
  async getInstagramMedia(instagramUserId, limit = 25) {
    return this.request(`/social/instagram/media/${instagramUserId}?limit=${limit}`);
  }

  // Upload image to Cloudinary for Instagram
  async uploadImageToCloudinary(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Use custom FormData upload method
    const url = `${this.baseURL}/social/instagram/upload-image`;
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
    const url = `${this.baseURL}/social/instagram/upload-video`;
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
    return this.request('/google-drive/auth');
  }

  async getGoogleDriveStatus() {
    return this.request('/google-drive/status');
  }

  async getGoogleDriveAuthorizeUrl() {
    return this.request('/google-drive/authorize');
  }

  async getGoogleDriveToken() {
    const response = await this.request('/google-drive/token');
    return response;
  }

  async disconnectGoogleDrive() {
    return this.request('/google-drive/disconnect', {
      method: 'POST',
    });
  }

  // Generate Instagram image using Stability AI
  async generateInstagramImage(imagePrompt, postType = 'feed') {
    return this.request('/social/instagram/generate-image', {
      method: 'POST',
      body: JSON.stringify({
        prompt: imagePrompt,
        post_type: postType
      }),
    });
  }

  // Unified Instagram post creation endpoint
  async createUnifiedInstagramPost(instagramUserId, options = {}) {
    // Only include image_url and video_url if 
    const payload = {
      instagram_user_id: instagramUserId,
      caption: options.caption,
      post_type: options.post_type || 'manual',
      use_ai: options.use_ai || false,
      prompt: options.prompt,
      carousel_images: options.carousel_images || [],
      location: options.location,
      hashtags: options.hashtags
    };
    if (options.image_url) payload.image_url = options.image_url;
    if (options.video_url) payload.video_url = options.video_url;
    return this.request('/social/instagram/create-post', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // REPLACE Make.com auto-reply webhook
  async toggleAutoReply(pageId, enabled, responseTemplate = 'Thank you for your comment!', selectedPostIds = []) {
    return this.request('/social/facebook/auto-reply', {
      method: 'POST',
      body: JSON.stringify({
        page_id: pageId,
        enabled: enabled,
        response_template: responseTemplate,
        selected_post_ids: selectedPostIds
      }),
    });
  }

  // Get posts for auto-reply selection
  async getPostsForAutoReply(pageId) {
    return this.request(`/social/facebook/posts-for-auto-reply?page_id=${pageId}`);
  }

  // Instagram Auto-Reply Methods
  async toggleInstagramAutoReply(instagramUserId, enabled, responseTemplate = 'Thank you for your comment!', selectedPostIds = []) {
    return this.request('/social/instagram/auto-reply', {
      method: 'POST',
      body: JSON.stringify({
        instagram_user_id: instagramUserId,
        enabled: enabled,
        response_template: responseTemplate,
        selected_post_ids: selectedPostIds
      }),
    });
  }

  async getInstagramPostsForAutoReply(instagramUserId) {
    return this.request(`/social/instagram/posts-for-auto-reply?instagram_user_id=${instagramUserId}`);
  }

  async syncInstagramPosts(instagramUserId) {
    return this.request('/social/instagram/sync-posts', {
      method: 'POST',
      body: JSON.stringify({
        instagram_user_id: instagramUserId
      }),
    });
  }

  // Get connected social accounts
  async getSocialAccounts() {
    return this.request('/social/accounts');
  }

  async getInstagramAccounts() {
    // This assumes your backend endpoint is /api/social/accounts and returns only Instagram accounts
    const response = await this.request('/social/accounts', {
      method: 'GET',
    });
    return response;
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
    return this.request(`/social/automation-rules${query ? `?${query}` : ''}`);
  }

  // Generate content using Groq API
  async generateContent(prompt) {
    return this.request('/ai/generate-content', {
      method: 'POST',
      body: JSON.stringify({
        prompt: prompt
      }),
    });
  }

  async generateInstagramCaption(prompt) {
    const response = await this.request('/social/instagram/generate-caption', {
      method: 'POST',
      body: JSON.stringify({
        prompt: prompt
      }),
    });
    return response;
  }

  async generateCaptionWithStrategy(customStrategy, context = "", maxLength = 2000) {
    const response = await this.request('/social/generate-caption-with-strategy', {
      method: 'POST',
      body: JSON.stringify({
        custom_strategy: customStrategy,
        context: context,
        max_length: maxLength
      }),
    });
    return response;
  }

  async generateBulkCaptions(customStrategy, contexts, maxLength = 2000) {
    const response = await this.request('/social/generate-bulk-captions', {
      method: 'POST',
      body: JSON.stringify({
        custom_strategy: customStrategy,
        contexts: contexts,
        max_length: maxLength
      }),
    });
    return response;
  }

  // Generate Instagram carousel
  async generateInstagramCarousel(prompt, count = 3) {
    const response = await this.request('/social/instagram/generate-carousel', {
      method: 'POST',
      body: JSON.stringify({
        prompt: prompt,
        count: count
      }),
    });
    return response;
  }

  // Post Instagram carousel
  async postInstagramCarousel(instagramUserId, caption, imageUrls) {
    const response = await this.request('/social/instagram/post-carousel', {
      method: 'POST',
      body: JSON.stringify({
        instagram_user_id: instagramUserId,
        caption: caption,
        image_urls: imageUrls
      }),
    });
    return response;
  }

  // Unified Facebook post creation endpoint
  async createFacebookPost(pageId, options = {}) {
    return this.request('/social/facebook/create-post', {
      method: 'POST',
      body: JSON.stringify({
        page_id: pageId,
        message: options.message,
        image_url: options.image_url,
        post_type: options.post_type || 'feed',
        use_ai: options.use_ai || false,
        prompt: options.prompt,
        scheduled_time: options.scheduled_time,
        carousel_images: options.carousel_images || [],
        video_url: options.video_url,
        location: options.location,
        hashtags: options.hashtags
      }),
    });
  }

  // Stability AI Image Generation endpoint (standalone)
  async generateFacebookImage(imagePrompt, postType = 'feed') {
    return this.request('/social/facebook/generate-image', {
      method: 'POST',
      body: JSON.stringify({
        prompt: imagePrompt,
        post_type: postType
      }),
    });
  }

  // Get AI service status including Stability AI
  async getAIServiceStatus() {
    return this.request('/ai/status');
  }

  // Debug endpoint for Stability AI troubleshooting
  async debugStabilityAI() {
    return this.request('/social/debug/stability-ai-status');
  }

  // Debug endpoint for testing Facebook image posts
  async debugFacebookImagePost(pageId, message = "Test post from debug") {
    return this.request('/social/facebook/debug-image-post', {
      method: 'POST',
      body: JSON.stringify({
        page_id: pageId,
        message: message
      }),
    });
  }

  // Bulk Composer - Schedule multiple posts
  async bulkSchedulePosts(requestData) {
    const response = await this.request('/social/bulk-composer/schedule', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
    return response;
  }

  // Bulk Composer - Schedule multiple posts for Instagram
  async bulkScheduleInstagramPosts({ social_account_id, posts }) {
    // Send social_account_id as a query param, posts as the body
    return this.request(`/social/instagram/bulk-schedule?social_account_id=${encodeURIComponent(social_account_id)}`, {
      method: 'POST',
      body: JSON.stringify(posts),
    });
  }

  // Bulk Composer - Get scheduled posts
  async getBulkComposerContent(socialAccountId = null) {
    let endpoint = '/social/bulk-composer/content';
    if (socialAccountId) {
      endpoint += `?social_account_id=${socialAccountId}`;
    }
    return this.request(endpoint);
  }

  // Bulk Composer - Update post caption
  async updateBulkComposerPost(postId, caption) {
    return this.request(`/social/bulk-composer/content/${postId}`, {
      method: 'PUT',
      body: JSON.stringify({
        caption: caption
      }),
    });
  }

  // Bulk Composer - Cancel/delete scheduled post
  async cancelBulkComposerPost(postId) {
    return this.request(`/social/bulk-composer/content/${postId}`, {
      method: 'DELETE',
    });
  }

  // LinkedIn endpoints
  async getLinkedInStatus() {
    return this.request('/social/linkedin/status');
  }

  async getLinkedInConfig() {
    return this.request('/social/linkedin/config');
  }

  async connectLinkedIn(data) {
    return this.request('/social/linkedin/connect', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async exchangeLinkedInCode(code) {
    return this.request('/social/linkedin/exchange-code', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  }

  async disconnectLinkedIn() {
    return this.request('/social/linkedin/disconnect', {
      method: 'POST',
    });
  }

  async refreshLinkedInTokens() {
    return this.request('/social/linkedin/refresh-tokens', {
      method: 'POST',
    });
  }

  // Get Instagram DM auto-reply status
  async getInstagramDmAutoReplyStatus(instagramUserId) {
    return this.request(`/social/instagram/dm-auto-reply/status/${instagramUserId}`);
  }

  // Enable global Instagram auto-reply
  async enableGlobalInstagramAutoReply(instagramUserId) {
    return this.request(`/social/instagram/auto_reply/global/enable?instagram_user_id=${instagramUserId}`, {
      method: 'POST'
    });
  }

  // Disable global Instagram auto-reply
  async disableGlobalInstagramAutoReply(instagramUserId) {
    return this.request(`/social/instagram/auto_reply/global/disable?instagram_user_id=${instagramUserId}`, {
      method: 'POST'
    });
  }

  // Get global auto-reply status
  async getGlobalInstagramAutoReplyStatus(instagramUserId) {
    return this.request(`/social/instagram/auto_reply/global/status?instagram_user_id=${instagramUserId}`);
  }

  // Get global auto-reply progress
  async getGlobalInstagramAutoReplyProgress(instagramUserId) {
    return this.request(`/social/instagram/auto_reply/global/progress?instagram_user_id=${instagramUserId}`);
  }

  async getScheduledPosts() {
    // Adjust the endpoint if your backend uses a different path
    return this.request('/social/scheduled-posts');
  }
}

const apiClient = new ApiClient();
export default apiClient;