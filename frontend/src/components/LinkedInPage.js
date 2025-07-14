import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../services/apiClient';
import './LinkedInPage.css';

const LinkedInPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuth();
  
  // State management
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [linkedInConnected, setLinkedInConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Ready to connect LinkedIn');
  const [linkedInAccounts, setLinkedInAccounts] = useState([]);
  const [linkedInConfig, setLinkedInConfig] = useState(null);

  // LinkedIn configuration - will be fetched from backend
  const LINKEDIN_REDIRECT_URI = process.env.REACT_APP_LINKEDIN_REDIRECT_URI || 'http://localhost:3000/linkedin';

  // Check authentication on component mount
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    checkLinkedInStatus();
    handleOAuthCallback();
    fetchLinkedInConfig();
  }, [isAuthenticated, navigate]);

  // Fetch LinkedIn configuration from backend
  const fetchLinkedInConfig = async () => {
    try {
      const response = await apiClient.getLinkedInConfig();
      setLinkedInConfig(response);
    } catch (error) {
      console.error('Error fetching LinkedIn config:', error);
      setMessage('Failed to load LinkedIn configuration');
    }
  };

  // Handle OAuth callback from LinkedIn
  const handleOAuthCallback = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');
    
    if (error) {
      setMessage(`LinkedIn authorization failed: ${error}`);
      return;
    }
    
    if (code && state) {
      const storedState = localStorage.getItem('linkedin_oauth_state');
      if (state === storedState) {
        setLoading(true);
        setMessage('Processing LinkedIn authorization...');
        
        // Exchange code for access token via backend
        exchangeCodeForToken(code);
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
        localStorage.removeItem('linkedin_oauth_state');
      } else {
        setMessage('LinkedIn authorization state mismatch');
      }
    }
  };

  // Exchange authorization code for access token
  const exchangeCodeForToken = async (code) => {
    try {
      const response = await apiClient.exchangeLinkedInCode(code);
      if (response.success) {
        setLinkedInConnected(true);
        setLinkedInAccounts([{
          id: response.profile.id,
          name: `${response.profile.firstName} ${response.profile.lastName}`,
          profilePicture: response.profile.profilePicture
        }]);
        setConnectionStatus('LinkedIn account connected successfully!');
        setMessage('LinkedIn account connected successfully!');
      }
    } catch (error) {
      console.error('Error exchanging code for token:', error);
      setMessage(`Failed to connect LinkedIn: ${error.message}`);
      setConnectionStatus('Connection failed');
    } finally {
      setLoading(false);
    }
  };

  // Check LinkedIn connection status
  const checkLinkedInStatus = async () => {
    try {
      const response = await apiClient.getLinkedInStatus();
      if (response.connected) {
        setLinkedInConnected(true);
        setLinkedInAccounts(response.accounts || []);
        setConnectionStatus('LinkedIn account already connected');
      }
    } catch (error) {
      console.log('LinkedIn not connected yet:', error.message);
    }
  };

  // Handle LinkedIn login
  const handleLinkedInLogin = () => {
    if (!linkedInConfig || !linkedInConfig.client_id) {
      setMessage('LinkedIn Client ID not configured');
      return;
    }
    
    setLoading(true);
    setMessage('Redirecting to LinkedIn...');
    
    try {
      // Use direct OAuth 2.0 flow instead of SDK
      const state = Math.random().toString(36).substring(7);
      const scope = 'r_liteprofile r_emailaddress w_member_social';
      
      const authUrl = `https://www.linkedin.com/oauth/v2/authorization?` +
        `response_type=code&` +
        `client_id=${linkedInConfig.client_id}&` +
        `redirect_uri=${encodeURIComponent(LINKEDIN_REDIRECT_URI)}&` +
        `state=${state}&` +
        `scope=${encodeURIComponent(scope)}`;
      
      // Store state for verification
      localStorage.setItem('linkedin_oauth_state', state);
      
      // Redirect to LinkedIn
      window.location.href = authUrl;
    } catch (error) {
      console.error('Error in LinkedIn login:', error);
      setMessage('LinkedIn login error occurred');
      setLoading(false);
    }
  };

  // Connect LinkedIn account to backend
  const handleConnectLinkedIn = async () => {
    try {
      setConnectionStatus('Connecting to backend...');
      
      const response = await apiClient.connectLinkedIn({
        access_token: null, // No access token in this simplified flow
        user_id: null, // No user_id in this simplified flow
        profile: null // No profile in this simplified flow
      });

      if (response.success) {
        setLinkedInConnected(true);
        setLinkedInAccounts([{
          id: null, // No user_id in this simplified flow
          name: null, // No profile name in this simplified flow
          profilePicture: null // No profile picture in this simplified flow
        }]);
        setConnectionStatus('LinkedIn account connected successfully!');
        setMessage('LinkedIn account connected successfully!');
      }
    } catch (error) {
      console.error('Backend connection error:', error);
      setMessage(`Failed to connect LinkedIn account: ${error.message}`);
      setConnectionStatus('Connection failed');
    } finally {
      setLoading(false);
    }
  };

  // Disconnect LinkedIn account
  const disconnectLinkedIn = async () => {
    try {
      setLoading(true);
      await apiClient.disconnectLinkedIn();
      setLinkedInConnected(false);
      setLinkedInAccounts([]);
      setConnectionStatus('LinkedIn account disconnected');
      setMessage('LinkedIn account disconnected successfully!');
      
      // Logout from LinkedIn SDK
      // No SDK logout in this simplified flow
    } catch (error) {
      console.error('Error disconnecting LinkedIn:', error);
      setMessage(`Failed to disconnect LinkedIn: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Get status card class based on connection status
  const getStatusCardClass = () => {
    if (connectionStatus.includes('Failed') || connectionStatus.includes('error') || connectionStatus.includes('Error')) {
      return 'status-card error';
    } else if (connectionStatus.includes('successful') || connectionStatus.includes('Connected') || connectionStatus.includes('completed')) {
      return 'status-card success';
    } else {
      return 'status-card info';
    }
  };

  // Show login form if not authenticated with our system
  if (!isAuthenticated) {
    return (
      <div className="page-container">
        <div className="auth-required">
          <h1>Please login to continue</h1>
          <p>You need to be logged in to use LinkedIn automation features.</p>
          <button onClick={() => navigate('/')} className="btn primary">
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="linkedin-page">
      <div className="page-header">
        <div className="header-content">
          <div className="platform-info">
            <div className="platform-icon linkedin">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
              </svg>
            </div>
            <div className="platform-details">
              <h1>LinkedIn Integration</h1>
              <p>Connect your LinkedIn account to automate posts and engagement</p>
            </div>
          </div>
        </div>
      </div>

      <div className="page-content">
        <div className="connection-section">
          <div className={getStatusCardClass()}>
            <div className="status-content">
              <div className="status-icon">
                {linkedInConnected ? (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                ) : (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                )}
              </div>
              <div className="status-text">
                <h3>{linkedInConnected ? 'LinkedIn Connected' : 'LinkedIn Not Connected'}</h3>
                <p>{connectionStatus}</p>
              </div>
            </div>
          </div>

          {!linkedInConnected ? (
            <div className="connection-actions">
              <button
                onClick={handleLinkedInLogin}
                disabled={loading || !linkedInConfig}
                className="btn primary linkedin-btn"
              >
                {loading ? (
                  <>
                    <div className="spinner"></div>
                    Connecting...
                  </>
                ) : !linkedInConfig ? (
                  <>
                    <div className="spinner"></div>
                    Loading...
                  </>
                ) : (
                  <>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                    Connect LinkedIn
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="connected-accounts">
              <h3>Connected Accounts</h3>
              {linkedInAccounts.map((account) => (
                <div key={account.id} className="account-card">
                  <div className="account-info">
                    {account.profilePicture && (
                      <img 
                        src={account.profilePicture} 
                        alt={account.name}
                        className="profile-picture"
                      />
                    )}
                    <div className="account-details">
                      <h4>{account.name}</h4>
                      <p>LinkedIn Profile</p>
                    </div>
                  </div>
                  <button
                    onClick={disconnectLinkedIn}
                    disabled={loading}
                    className="btn secondary disconnect-btn"
                  >
                    {loading ? 'Disconnecting...' : 'Disconnect'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {message && (
            <div className={`message ${message.includes('Error') || message.includes('Failed') ? 'error' : 'success'}`}>
              {message}
            </div>
          )}
        </div>

        <div className="features-section">
          <h3>LinkedIn Features</h3>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
              </div>
              <h4>Auto-Posting</h4>
              <p>Schedule and automate LinkedIn posts</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
                </svg>
              </div>
              <h4>Comment Management</h4>
              <p>Automatically respond to comments</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <h4>Analytics</h4>
              <p>Track post performance and engagement</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LinkedInPage; 