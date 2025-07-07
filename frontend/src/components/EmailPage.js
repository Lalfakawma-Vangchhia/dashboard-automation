import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function EmailPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    campaignName: '',
    subject: '',
    emailTemplate: '',
    recipients: '',
    schedule: 'immediately',
    customDate: '',
    customTime: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Email campaign data:', formData);
    alert('Email campaign created successfully!');
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
          <h1 className="page-title">Email Automation</h1>
          <p className="page-subtitle">Create and schedule your email campaigns</p>
        </div>
      </header>

      <main className="page-main">
        <div className="email-form-container">
          <div className="form-header">
            <div className="form-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </div>
            <div>
              <h2>New Email Campaign</h2>
              <p>Configure your email automation settings</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="email-form">
            <div className="form-section">
              <h3>Campaign Details</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="campaignName">Campaign Name *</label>
                  <input
                    type="text"
                    id="campaignName"
                    name="campaignName"
                    value={formData.campaignName}
                    onChange={handleInputChange}
                    placeholder="Enter campaign name"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="subject">Email Subject *</label>
                  <input
                    type="text"
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleInputChange}
                    placeholder="Enter email subject"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="form-section">
              <h3>Email Content</h3>
              <div className="form-group">
                <label htmlFor="emailTemplate">Email Template *</label>
                <textarea
                  id="emailTemplate"
                  name="emailTemplate"
                  value={formData.emailTemplate}
                  onChange={handleInputChange}
                  placeholder="Enter your email content here..."
                  rows="8"
                  required
                />
              </div>
            </div>

            <div className="form-section">
              <h3>Recipients</h3>
              <div className="form-group">
                <label htmlFor="recipients">Email Addresses *</label>
                <textarea
                  id="recipients"
                  name="recipients"
                  value={formData.recipients}
                  onChange={handleInputChange}
                  placeholder="Enter email addresses separated by commas"
                  rows="4"
                  required
                />
                <small>Enter multiple email addresses separated by commas</small>
              </div>
            </div>

            <div className="form-section">
              <h3>Schedule</h3>
              <div className="form-group">
                <label>When to send?</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="schedule"
                      value="immediately"
                      checked={formData.schedule === 'immediately'}
                      onChange={handleInputChange}
                    />
                    Send immediately
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="schedule"
                      value="custom"
                      checked={formData.schedule === 'custom'}
                      onChange={handleInputChange}
                    />
                    Schedule for later
                  </label>
                </div>
              </div>

              {formData.schedule === 'custom' && (
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="customDate">Date</label>
                    <input
                      type="date"
                      id="customDate"
                      name="customDate"
                      value={formData.customDate}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="customTime">Time</label>
                    <input
                      type="time"
                      id="customTime"
                      name="customTime"
                      value={formData.customTime}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="form-actions">
              <button type="button" className="btn-secondary" onClick={() => navigate('/')}>
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Create Campaign
              </button>
            </div>
          </form>
        </div>

        <div className="email-tips">
          <h3>Email Tips</h3>
          <ul>
            <li>Keep your subject line under 50 characters for better open rates</li>
            <li>Personalize your emails with recipient names when possible</li>
            <li>Test your emails before sending to large lists</li>
            <li>Include a clear call-to-action in your email content</li>
            <li>Monitor your campaign performance and adjust accordingly</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export default EmailPage; 