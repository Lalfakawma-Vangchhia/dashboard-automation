import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  const navigate = useNavigate();
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    
    // Add timeout to prevent infinite hanging
    const timeout = setTimeout(() => {
      setMessage('Error: Request timed out. Please check if the backend server is running.');
      setLoading(false);
    }, 10000); // 10 second timeout
    
    try {
      if (isRegister) {
        console.log('Attempting registration...');
        await register({
          email,
          password,
          username,
          full_name: fullName,
        });
        setMessage('Registration successful! Please login.');
        setIsRegister(false);
      } else {
        console.log('Attempting login with:', { email });
        console.log('API URL:', process.env.REACT_APP_API_URL || 'http://localhost:8000/api');
        
        const response = await login(email, password);
        console.log('Login response:', response);
        
        setMessage('Login successful!');
        // Clear the timeout on success
        clearTimeout(timeout);
        
        // Navigate to dashboard after successful login
        navigate('/');
      }
    } catch (error) {
      console.error('Login/Register error:', error);
      setMessage(`Error: ${error.message}`);
      
      // Log more details for debugging
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setMessage('Error: Cannot connect to backend server. Please ensure the backend is running on http://localhost:8000');
      }
    } finally {
      clearTimeout(timeout);
      setLoading(false);
    }
  };

  const containerStyle = {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
  };

  const glassCardStyle = {
    background: 'rgba(255, 255, 255, 0.25)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    boxShadow: '0 25px 45px rgba(0, 0, 0, 0.1)',
    padding: '40px',
    width: '100%',
    maxWidth: '420px',
    position: 'relative',
    overflow: 'hidden'
  };

  const titleStyle = {
    fontSize: '2rem',
    fontWeight: '600',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: '30px',
    textShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
  };

  const formGroupStyle = {
    marginBottom: '20px',
    position: 'relative'
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#ffffff',
    marginBottom: '8px',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
  };

  const inputStyle = {
    width: '100%',
    padding: '14px 16px',
    fontSize: '1rem',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '12px',
    background: 'rgba(255, 255, 255, 0.2)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    color: '#ffffff',
    transition: 'all 0.3s ease',
    boxSizing: 'border-box',
    outline: 'none'
  };

  const inputFocusStyle = {
    ...inputStyle,
    border: '1px solid rgba(255, 255, 255, 0.6)',
    background: 'rgba(255, 255, 255, 0.3)',
    transform: 'translateY(-1px)',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
  };

  const buttonStyle = {
    width: '100%',
    padding: '16px',
    fontSize: '1rem',
    fontWeight: '600',
    color: '#ffffff',
    background: loading 
      ? 'rgba(255, 255, 255, 0.2)' 
      : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '12px',
    cursor: loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.3s ease',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    opacity: loading ? 0.7 : 1
  };

  const switchButtonStyle = {
    background: 'none',
    border: 'none',
    color: '#ffffff',
    cursor: 'pointer',
    textDecoration: 'underline',
    fontSize: '0.9rem',
    fontWeight: '500',
    transition: 'all 0.3s ease',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
  };

  const messageStyle = {
    marginTop: '20px',
    padding: '16px',
    borderRadius: '12px',
    fontSize: '0.9rem',
    fontWeight: '500',
    textAlign: 'center',
    background: message.includes('Error') 
      ? 'rgba(239, 68, 68, 0.2)' 
      : 'rgba(34, 197, 94, 0.2)',
    color: '#ffffff',
    border: `1px solid ${message.includes('Error') 
      ? 'rgba(239, 68, 68, 0.3)' 
      : 'rgba(34, 197, 94, 0.3)'}`,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
  };

  const switchTextStyle = {
    textAlign: 'center',
    marginTop: '24px',
    color: '#ffffff',
    fontSize: '0.9rem',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
  };

  return (
    <div style={containerStyle}>
      <div style={glassCardStyle}>
        <h2 style={titleStyle}>
          {isRegister ? 'Create Account' : 'Welcome Back'}
        </h2>
        
        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => Object.assign(e.target.style, inputStyle)}
                  placeholder="Enter your full name"
                  required
                />
              </div>
              
              <div style={formGroupStyle}>
                <label style={labelStyle}>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => Object.assign(e.target.style, inputStyle)}
                  placeholder="Choose a username"
                  required
                />
              </div>
            </>
          )}
          
          <div style={formGroupStyle}>
            <label style={labelStyle}>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputStyle}
              onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
              onBlur={(e) => Object.assign(e.target.style, inputStyle)}
              placeholder="Enter your email"
              required
            />
          </div>
          
          <div style={formGroupStyle}>
            <label style={labelStyle}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={inputStyle}
              onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
              onBlur={(e) => Object.assign(e.target.style, inputStyle)}
              placeholder="Enter your password"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            style={buttonStyle}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.3)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
              }
            }}
          >
            {loading ? 'Processing...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>
        
        <div style={switchTextStyle}>
          {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setMessage('');
            }}
            style={switchButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.color = '#f0f8ff';
              e.target.style.textShadow = '0 0 8px rgba(255, 255, 255, 0.5)';
            }}
            onMouseLeave={(e) => {
              e.target.style.color = '#ffffff';
              e.target.style.textShadow = '0 1px 2px rgba(0, 0, 0, 0.1)';
            }}
          >
            {isRegister ? 'Sign In' : 'Create Account'}
          </button>
        </div>
        
        {message && (
          <div style={messageStyle}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

export default Login; 