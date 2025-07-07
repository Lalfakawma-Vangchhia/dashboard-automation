import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './SocialMediaPage.css';

function SocialMediaPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated: authIsAuthenticated } = useAuth();
  const [hoveredCard, setHoveredCard] = useState(null);

  const handleFacebookConnect = () => {
    navigate('/facebook');
  };

  const handleInstagramConnect = () => {
    navigate('/instagram');
  };

  // Show login form if not authenticated with our system
  if (!authIsAuthenticated) {
    return (
      <div className="page-container">
        <div className="auth-required">
          <h1>Please login to continue</h1>
          <p>You need to be logged in to use social media automation features.</p>
          <button onClick={() => navigate('/')} className="btn primary">
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  const platforms = [
    {
      id: 'facebook',
      name: 'Facebook',
      description: 'Automate your Facebook posts and engagement',
      icon: (
        <svg width="64" height="64" viewBox="0 0 24 24" fill="#1877F2">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      ),
      connectHandler: handleFacebookConnect,
      gradient: 'linear-gradient(135deg, #1877F2 0%, #42a5f5 100%)',
      borderColor: '#1877F2'
    },
    {
      id: 'instagram',
      name: 'Instagram',
      description: 'Automate your Instagram posts and stories',
      icon: (
        <svg width="64" height="64" viewBox="0 0 24 24" fill="url(#instagram-gradient)">
          <defs>
            <linearGradient id="instagram-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#405DE6"/>
              <stop offset="25%" stopColor="#5851DB"/>
              <stop offset="50%" stopColor="#833AB4"/>
              <stop offset="75%" stopColor="#C13584"/>
              <stop offset="100%" stopColor="#E1306C"/>
            </linearGradient>
          </defs>
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.40z"/>
        </svg>
      ),
      connectHandler: handleInstagramConnect,
      gradient: 'linear-gradient(135deg, #405DE6 0%, #5851DB 25%, #833AB4 50%, #C13584 75%, #E1306C 100%)',
      borderColor: '#E1306C'
    }
  ];

  return (
    <div className="page-container">
      <header className="page-header">
        <button onClick={() => navigate('/')} className="back-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15,18 9,12 15,6"></polyline>
          </svg>
          Back to Dashboard
        </button>
        <div className="page-title-section">
          <h1 className="page-title">Social Media Automation</h1>
          <p className="page-subtitle">Connected to FastAPI Backend • User: {user?.full_name || user?.username}</p>
        </div>
      </header>

      <main className="page-main">
        <div className="platforms-container">
          <div className="platforms-grid">
            {platforms.map((platform) => (
              <div
                key={platform.id}
                className={`platform-card ${hoveredCard === platform.id ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredCard(platform.id)}
                onMouseLeave={() => setHoveredCard(null)}
                style={{
                  '--platform-gradient': platform.gradient,
                  '--platform-border': platform.borderColor
                }}
              >
                <div className="platform-icon">
                  {platform.icon}
                </div>
                
                <div className="platform-content">
                  <h3 className="platform-name">{platform.name}</h3>
                  <p className="platform-description">{platform.description}</p>
                </div>

                <div className="platform-actions">
                  <button 
                    className="connect-btn"
                    onClick={platform.connectHandler}
                  >
                    Open {platform.name}
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="9,18 15,12 9,6"></polyline>
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Backend Status Indicator */}
        <div className="backend-status-footer">
          <div className="backend-indicator">
            <span className="status-dot"></span>
            <span>Connected to FastAPI Backend</span>
          </div>
        </div>
      </main>
    </div>
  );
}

export default SocialMediaPage; 