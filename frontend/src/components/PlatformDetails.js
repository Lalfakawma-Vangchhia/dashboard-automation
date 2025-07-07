import React from 'react';

const PlatformDetails = ({ platform, onClose }) => {
  return (
    <div className="platform-details">
      <div className="details-content">
        <div className="details-header">
          <h3>Configure {platform.name} Automation</h3>
          <button className="close-details" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div className="config-form">
          <FormSection title="Auto-Posting Settings">
            <div className="form-group">
              <label>Posting Schedule</label>
              <select>
                <option>Daily at 9:00 AM</option>
                <option>3 times per week</option>
                <option>Weekdays only</option>
                <option>Custom schedule</option>
              </select>
            </div>
            <div className="form-group">
              <label>Content Type</label>
              <div className="checkbox-group">
                <label><input type="checkbox" defaultChecked /> Images</label>
                <label><input type="checkbox" defaultChecked /> Videos</label>
                <label><input type="checkbox" /> Stories</label>
                <label><input type="checkbox" /> Reels</label>
              </div>
            </div>
          </FormSection>

          <FormSection title="Auto Reply Settings">
            <div className="form-group">
              <label>Reply Speed</label>
              <select>
                <option>Instant (0-1 min)</option>
                <option>Quick (1-5 min)</option>
                <option>Normal (5-15 min)</option>
                <option>Delayed (15-60 min)</option>
              </select>
            </div>
            <div className="form-group">
              <label>Reply Types</label>
              <div className="checkbox-group">
                <label><input type="checkbox" defaultChecked /> Thank you messages</label>
                <label><input type="checkbox" defaultChecked /> FAQ responses</label>
                <label><input type="checkbox" /> Custom keywords</label>
              </div>
            </div>
          </FormSection>

          <FormSection title="DM Response Settings">
            <div className="form-group">
              <label>Auto-reply to DMs</label>
              <div className="toggle-group">
                <label className="toggle">
                  <input type="checkbox" />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
            <div className="form-group">
              <label>Welcome Message</label>
              <textarea placeholder="Hi! Thanks for reaching out. I'll get back to you soon!" rows="3"></textarea>
            </div>
          </FormSection>

          <div className="form-actions">
            <button className="save-config-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20,6 9,17 4,12"></polyline>
              </svg>
              Save Configuration
            </button>
            <button className="test-config-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polygon points="10,8 16,12 10,16 10,8"></polygon>
              </svg>
              Test Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const FormSection = ({ title, children }) => (
  <div className="form-section">
    <h4>{title}</h4>
    {children}
  </div>
);

export default PlatformDetails; 