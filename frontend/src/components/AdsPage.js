import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function AdsPage() {
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState('campaigns');
  const [selectedPlatform, setSelectedPlatform] = useState('Facebook');
  const [campaigns] = useState([
    {
      id: 1,
      name: 'Summer Sale Campaign',
      status: 'Active',
      platform: 'Facebook',
      budget: '$500',
      clicks: '1,234',
      impressions: '15,678',
      ctr: '7.87%'
    },
    {
      id: 2,
      name: 'Product Launch',
      status: 'Paused',
      platform: 'Instagram',
      budget: '$300',
      clicks: '892',
      impressions: '12,456',
      ctr: '7.16%'
    }
  ]);

  const adPlatforms = [
    {
      name: 'Facebook',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      ),
      color: '#1877F2',
      gradient: 'linear-gradient(135deg, #1877F2 0%, #42A5F5 100%)'
    },
    {
      name: 'Instagram',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
        </svg>
      ),
      color: '#E4405F',
      gradient: 'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)'
    }
  ];

  // Mock data for line chart based on selected platform
  const getChartData = (platform) => {
    const baseData = {
      Facebook: {
        impressions: [8500, 9200, 7800, 9500, 8800, 7200, 6800],
        clicks: [450, 520, 380, 580, 480, 350, 320],
        conversions: [25, 32, 22, 35, 28, 18, 15]
      },
      Instagram: {
        impressions: [6200, 7100, 5900, 7800, 6500, 5100, 4900],
        clicks: [380, 420, 340, 480, 390, 280, 260],
        conversions: [22, 28, 19, 31, 24, 16, 13]
      }
    };
    return baseData[platform] || baseData.Facebook;
  };

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
          <h1 className="page-title">Campaign Automation</h1>
          <p className="page-subtitle">Manage and optimize your advertising campaigns</p>
        </div>
      </header>

      <main className="page-main">
        <div className="ads-tabs">
          <button
            className={`tab-btn ${selectedTab === 'campaigns' ? 'active' : ''}`}
            onClick={() => setSelectedTab('campaigns')}
          >
            Active Campaigns
          </button>
          <button
            className={`tab-btn ${selectedTab === 'platforms' ? 'active' : ''}`}
            onClick={() => setSelectedTab('platforms')}
          >
            Ad Platforms
          </button>
          <button
            className={`tab-btn ${selectedTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setSelectedTab('analytics')}
          >
            Analytics
          </button>
        </div>

        {selectedTab === 'campaigns' && (
          <div className="campaigns-section">
            <div className="section-header">
              <h2>Your Active Campaigns</h2>
              <button className="btn-primary">Create New Campaign</button>
            </div>

            <div className="campaigns-grid">
              {campaigns.map((campaign) => (
                <div key={campaign.id} className="campaign-card">
                  <div className="campaign-header">
                    <h3>{campaign.name}</h3>
                    <span className={`status ${campaign.status.toLowerCase()}`}>
                      {campaign.status}
                    </span>
                  </div>
                  <div className="campaign-platform">
                    <span>{campaign.platform}</span>
                  </div>
                  <div className="campaign-stats">
                    <div className="stat">
                      <label>Budget</label>
                      <value>{campaign.budget}</value>
                    </div>
                    <div className="stat">
                      <label>Clicks</label>
                      <value>{campaign.clicks}</value>
                    </div>
                    <div className="stat">
                      <label>Impressions</label>
                      <value>{campaign.impressions}</value>
                    </div>
                    <div className="stat">
                      <label>CTR</label>
                      <value>{campaign.ctr}</value>
                    </div>
                  </div>
                  <div className="campaign-actions">
                    <button className="btn-secondary">Edit</button>
                    <button className="btn-secondary">View Details</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'platforms' && (
          <div className="platforms-section">
            <div className="section-header">
              <h2>Advertising Platforms</h2>
              <p>Connect and manage your advertising accounts</p>
            </div>

            <div className="platforms-grid">
              {adPlatforms.map((platform, index) => (
                <div key={index} className="platform-card">
                  <div className="platform-icon" style={{ color: platform.color }}>
                    {platform.icon}
                  </div>
                  <h3>{platform.name}</h3>
                  <div className="platform-actions">
                    <button className="connect-btn">
                      Connect Account
                    </button>
                    <button className="btn-secondary">Learn More</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'analytics' && (
          <div className="analytics-section">
            <div className="section-header">
              <h2>Campaign Analytics</h2>
              <p>Track performance and optimize your campaigns</p>
            </div>

            <div className="analytics-grid">
              <div className="analytics-card">
                <div className="analytics-header">
                  <h3>Total Impressions</h3>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                </div>
                <div className="analytics-value">
                  {selectedPlatform === 'Facebook' ? '28,134' : '21,890'}
                </div>
                <div className="analytics-change positive">
                  {selectedPlatform === 'Facebook' ? '+12.5%' : '+9.8%'}
                </div>
              </div>

              <div className="analytics-card">
                <div className="analytics-header">
                  <h3>Total Clicks</h3>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 12l2 2 4-4"/>
                    <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"/>
                    <path d="M3 12c1 0 3-1-3-3s-2-3-3-3-3 1-3 3 2 3 3 3"/>
                  </svg>
                </div>
                <div className="analytics-value">
                  {selectedPlatform === 'Facebook' ? '2,126' : '1,687'}
                </div>
                <div className="analytics-change positive">
                  {selectedPlatform === 'Facebook' ? '+8.3%' : '+6.7%'}
                </div>
              </div>

              <div className="analytics-card">
                <div className="analytics-header">
                  <h3>Average CTR</h3>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                </div>
                <div className="analytics-value">
                  {selectedPlatform === 'Facebook' ? '7.55%' : '7.71%'}
                </div>
                <div className="analytics-change positive">
                  {selectedPlatform === 'Facebook' ? '+2.1%' : '+3.2%'}
                </div>
              </div>

              <div className="analytics-card">
                <div className="analytics-header">
                  <h3>Total Spend</h3>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                  </svg>
                </div>
                <div className="analytics-value">
                  {selectedPlatform === 'Facebook' ? '$800' : '$620'}
                </div>
                <div className="analytics-change negative">
                  {selectedPlatform === 'Facebook' ? '-5.2%' : '-3.1%'}
                </div>
              </div>
            </div>

            <div className="chart-section">
              <div className="chart-header">
                <h3>Performance Over Time</h3>
                <div className="platform-selector">
                  <label>Platform:</label>
                  <select 
                    value={selectedPlatform} 
                    onChange={(e) => setSelectedPlatform(e.target.value)}
                    className="platform-dropdown"
                  >
                    <option value="Facebook">Facebook</option>
                    <option value="Instagram">Instagram</option>
                  </select>
                </div>
              </div>
              <div className="chart-container">
                <div className="chart-demo">
                  <div className="chart-legend">
                    <div className="legend-item">
                      <div className="legend-color impressions"></div>
                      <span>Impressions</span>
                    </div>
                    <div className="legend-item">
                      <div className="legend-color clicks"></div>
                      <span>Clicks</span>
                    </div>
                    <div className="legend-item">
                      <div className="legend-color conversions"></div>
                      <span>Conversions</span>
                    </div>
                  </div>
                  <div className="line-chart-area">
                    <div className="chart-y-axis">
                      <span>10K</span>
                      <span>8K</span>
                      <span>6K</span>
                      <span>4K</span>
                      <span>2K</span>
                      <span>0</span>
                    </div>
                    <div className="line-chart-content">
                      <svg className="line-chart-svg" viewBox="0 0 400 280" preserveAspectRatio="none">
                        {/* Grid lines */}
                        <defs>
                          <pattern id="grid" width="57.14" height="56" patternUnits="userSpaceOnUse">
                            <path d="M 57.14 0 L 0 0 0 56" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
                          </pattern>
                          <linearGradient id="impressionsGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#3b82f6" />
                            <stop offset="100%" stopColor="#1d4ed8" />
                          </linearGradient>
                          <linearGradient id="clicksGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#8b5cf6" />
                            <stop offset="100%" stopColor="#7c3aed" />
                          </linearGradient>
                          <linearGradient id="conversionsGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#ec4899" />
                            <stop offset="100%" stopColor="#be185d" />
                          </linearGradient>
                        </defs>
                        <rect width="100%" height="100%" fill="url(#grid)" />
                        
                        {/* Impressions Line */}
                        <polyline
                          fill="none"
                          stroke="url(#impressionsGradient)"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          points={getChartData(selectedPlatform).impressions.map((value, index) => 
                            `${index * 57.14 + 28.57},${280 - (value / 10000) * 240}`
                          ).join(' ')}
                        />
                        
                        {/* Clicks Line */}
                        <polyline
                          fill="none"
                          stroke="url(#clicksGradient)"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          points={getChartData(selectedPlatform).clicks.map((value, index) => 
                            `${index * 57.14 + 28.57},${280 - (value / 10000) * 240}`
                          ).join(' ')}
                        />
                        
                        {/* Conversions Line */}
                        <polyline
                          fill="none"
                          stroke="url(#conversionsGradient)"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          points={getChartData(selectedPlatform).conversions.map((value, index) => 
                            `${index * 57.14 + 28.57},${280 - (value / 10000) * 240}`
                          ).join(' ')}
                        />
                        
                        {/* Data points for impressions */}
                        {getChartData(selectedPlatform).impressions.map((value, index) => (
                          <circle
                            key={`imp-${index}`}
                            cx={index * 57.14 + 28.57}
                            cy={280 - (value / 10000) * 240}
                            r="4"
                            fill="#3b82f6"
                            stroke="#ffffff"
                            strokeWidth="2"
                            className="data-point impressions-point"
                          />
                        ))}
                        
                        {/* Data points for clicks */}
                        {getChartData(selectedPlatform).clicks.map((value, index) => (
                          <circle
                            key={`click-${index}`}
                            cx={index * 57.14 + 28.57}
                            cy={280 - (value / 10000) * 240}
                            r="4"
                            fill="#8b5cf6"
                            stroke="#ffffff"
                            strokeWidth="2"
                            className="data-point clicks-point"
                          />
                        ))}
                        
                        {/* Data points for conversions */}
                        {getChartData(selectedPlatform).conversions.map((value, index) => (
                          <circle
                            key={`conv-${index}`}
                            cx={index * 57.14 + 28.57}
                            cy={280 - (value / 10000) * 240}
                            r="4"
                            fill="#ec4899"
                            stroke="#ffffff"
                            strokeWidth="2"
                            className="data-point conversions-point"
                          />
                        ))}
                      </svg>
                      <div className="chart-x-axis">
                        <span>Mon</span>
                        <span>Tue</span>
                        <span>Wed</span>
                        <span>Thu</span>
                        <span>Fri</span>
                        <span>Sat</span>
                        <span>Sun</span>
                      </div>
                    </div>
                  </div>
                  <div className="chart-insights">
                    <div className="insight">
                      <div className="insight-icon">📈</div>
                      <div className="insight-text">
                        <strong>Peak Performance:</strong> {selectedPlatform === 'Facebook' ? 'Thursday showed highest engagement' : 'Thursday performed best overall'}
                      </div>
                    </div>
                    <div className="insight">
                      <div className="insight-icon">🎯</div>
                      <div className="insight-text">
                        <strong>Optimization Tip:</strong> {selectedPlatform === 'Facebook' ? 'Increase budget on weekdays for better ROI' : 'Focus on visual content during peak hours'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default AdsPage; 