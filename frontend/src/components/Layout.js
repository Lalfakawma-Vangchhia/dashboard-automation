import React from 'react';

function Layout({ children }) {
  return (
    <div className="App">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="brand-section">
            <h1 className="company-name">ThorSignia</h1>
            <p className="company-tagline">Enterprise Automation Platform</p>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}

export default Layout; 