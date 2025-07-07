import React from 'react';

const ActivityLog = ({ activityLog }) => {
  if (activityLog.length === 0) return null;

  return (
    <div className="activity-log">
      <h3>Recent Activity</h3>
      <div className="activity-list">
        {activityLog.slice(-5).reverse().map((activity, index) => (
          <div key={index} className={`activity-item ${activity.status}`}>
            <div className="activity-time">{activity.time}</div>
            <div className="activity-action">{activity.action}</div>
            <div className={`activity-status ${activity.status}`}>
              <div className="status-dot"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityLog; 