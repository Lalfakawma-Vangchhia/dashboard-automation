// Facebook utility functions extracted from FacebookPage.js

// Convert file to base64
export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
};

// Media icon component
export const MediaIcon = ({ type }) => {
  switch(type) {
    case 'photo':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21,15 16,10 5,21"/>
        </svg>
      );
    case 'ai_image':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"/>
        </svg>
      );
    case 'video':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="23 7 16 12 23 17 23 7"/>
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
        </svg>
      );
    default:
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      );
  }
};

// Facebook SDK utilities
export const cleanupFacebookSDK = () => {
  try {
    if (window.FB) {
      try {
        if (window.FB.getLoginStatus) {
          window.FB.logout();
        }
      } catch (e) {
        // Ignore errors during cleanup
      }
      delete window.FB;
    }
    
    if (window.fbAsyncInit) {
      delete window.fbAsyncInit;
    }
  } catch (e) {
    // Ignore cleanup errors
  }
};

export const loadFacebookSDK = (FACEBOOK_APP_ID) => {
  return new Promise((resolve, reject) => {
    cleanupFacebookSDK();
    
    const versions = ['v21.0', 'v20.0', 'v19.0', 'v18.0'];
    let currentVersionIndex = 0;
    
    const tryInitialization = () => {
      const version = versions[currentVersionIndex];
      
      window.fbAsyncInit = function () {
        try {
          window.FB.init({
            appId: FACEBOOK_APP_ID,
            cookie: true,
            xfbml: true,
            version: version,
            status: true
          });
          
          console.log(`Facebook SDK initialized successfully with ${version}`);
          
          window.FB.getLoginStatus(function(response) {
            console.log('Facebook SDK test successful:', response.status);
            resolve();
          }, true);
          
        } catch (error) {
          console.error(`Facebook SDK initialization failed with ${version}:`, error);
          
          currentVersionIndex++;
          if (currentVersionIndex < versions.length) {
            console.log(`Trying Facebook SDK version ${versions[currentVersionIndex]}...`);
            setTimeout(tryInitialization, 500);
          } else {
            reject(new Error('All Facebook SDK versions failed to initialize'));
          }
        }
      };

      if (!document.getElementById('facebook-jssdk')) {
        const script = document.createElement('script');
        script.id = 'facebook-jssdk';
        script.src = 'https://connect.facebook.net/en_US/sdk.js';
        script.async = true;
        script.defer = true;
        script.crossOrigin = 'anonymous';
        script.onerror = () => {
          console.error(`Failed to load Facebook SDK script for ${version}`);
          
          currentVersionIndex++;
          if (currentVersionIndex < versions.length) {
            console.log(`Trying Facebook SDK version ${versions[currentVersionIndex]}...`);
            setTimeout(tryInitialization, 500);
          } else {
            reject(new Error('Failed to load Facebook SDK script'));
          }
        };
        
        document.body.appendChild(script);
      }
    };

    tryInitialization();
  });
};

// Post utilities
export const postTextOnly = async (selectedPage, message) => {
  return new Promise((resolve, reject) => {
    window.FB.api(`/${selectedPage.id}/feed`, 'POST', {
      message: message,
      access_token: selectedPage.access_token
    }, (response) => {
      if (response.error) {
        reject(new Error(`${response.error.message} (Code: ${response.error.code})`));
      } else {
        resolve(response);
      }
    });
  });
};

export const postWithMedia = async (selectedPage, message, file, mediaType) => {
  const fileData = await fileToBase64(file);
  
  if (mediaType === 'photo') {
    return new Promise((resolve, reject) => {
      window.FB.api(`/${selectedPage.id}/photos`, 'POST', {
        caption: message,
        source: fileData,
        access_token: selectedPage.access_token
      }, (response) => {
        if (response.error) {
          reject(new Error(`${response.error.message} (Code: ${response.error.code})`));
        } else {
          resolve(response);
        }
      });
    });
  } else if (mediaType === 'video') {
    return new Promise((resolve, reject) => {
      window.FB.api(`/${selectedPage.id}/videos`, 'POST', {
        description: message,
        source: fileData,
        access_token: selectedPage.access_token
      }, (response) => {
        if (response.error) {
          reject(new Error(`${response.error.message} (Code: ${response.error.code})`));
        } else {
          resolve(response);
        }
      });
    });
  }
}; 