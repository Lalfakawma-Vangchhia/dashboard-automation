import React, { useEffect, useState } from 'react';
import apiClient from '../services/apiClient';
import './ScheduledPostHistory.css';

function ScheduledPostHistory() {
  const [posts, setPosts] = useState([]);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('scheduled_datetime');
  const [loading, setLoading] = useState(true);
  const [editPost, setEditPost] = useState(null);
  const [deletePost, setDeletePost] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getScheduledPosts();
      setPosts(data);
    } catch (err) {
      setMessage('Failed to fetch scheduled posts.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (post) => {
    setEditPost(post);
  };

  const handleDelete = (post) => {
    setDeletePost(post);
    setShowConfirm(true);
  };

  const confirmDelete = async () => {
    try {
      await apiClient.deleteScheduledPost(deletePost.id);
      setPosts(posts.filter(p => p.id !== deletePost.id));
      setMessage('Post deleted.');
    } catch (err) {
      setMessage('Failed to delete post.');
    } finally {
      setShowConfirm(false);
      setDeletePost(null);
    }
  };

  const handleSaveEdit = async (updated) => {
    try {
      await apiClient.updateScheduledPost(updated.id, updated);
      setPosts(posts.map(p => p.id === updated.id ? updated : p));
      setMessage('Post updated.');
    } catch (err) {
      setMessage('Failed to update post.');
    } finally {
      setEditPost(null);
    }
  };

  // Format date to DD MMM YYYY, hh:mm A format
  const formatDateTime = (dateTimeString) => {
    if (!dateTimeString) return 'N/A';
    const date = new Date(dateTimeString);
    return date.toLocaleDateString('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }) + ', ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  // Get post type display with icon
  const getPostTypeDisplay = (postType) => {
    if (!postType) return { icon: '📄', label: 'Unknown', class: 'sph-post-type-unknown' };
    
    const type = postType.toLowerCase();
    switch (type) {
      case 'photo':
        return { icon: '📸', label: 'Photo', class: 'sph-post-type-photo' };
      case 'carousel':
        return { icon: '🖼️', label: 'Carousel', class: 'sph-post-type-carousel' };
      case 'reel':
        return { icon: '🎬', label: 'Reel', class: 'sph-post-type-reel' };
      default:
        return { icon: '📄', label: type.charAt(0).toUpperCase() + type.slice(1), class: 'sph-post-type-unknown' };
    }
  };

  const filtered = posts.filter(post =>
    post.prompt.toLowerCase().includes(search.toLowerCase()) ||
    (post.status && post.status.toLowerCase().includes(search.toLowerCase())) ||
    (post.post_type && post.post_type.toLowerCase().includes(search.toLowerCase()))
  );

  const sorted = [...filtered].sort((a, b) => {
    let valA = a[sortBy];
    let valB = b[sortBy];
    if (sortBy === 'scheduled_datetime') {
      valA = new Date(valA);
      valB = new Date(valB);
    }
    if (valA < valB) return -1;
    if (valA > valB) return 1;
    return 0;
  });

  return (
    <div className="scheduled-post-history">
      <h2>Scheduled Post History</h2>
      <div className="sph-controls">
        <input
          type="text"
          placeholder="Search by caption, status, or post type..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>
      <table className="sph-table">
        <thead>
          <tr>
            <th onClick={() => setSortBy('prompt')}>Caption</th>
            <th onClick={() => setSortBy('post_type')}>Post Type</th>
            <th onClick={() => setSortBy('scheduled_datetime')}>Date & Time</th>
            <th onClick={() => setSortBy('status')}>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr><td colSpan={5}>Loading...</td></tr>
          ) : sorted.length === 0 ? (
            <tr><td colSpan={5}>No scheduled posts found.</td></tr>
          ) : sorted.map(post => {
            const postTypeDisplay = getPostTypeDisplay(post.post_type);
            return (
              <tr key={post.id}>
                <td title={post.prompt}>{post.prompt.length > 40 ? post.prompt.slice(0, 40) + '...' : post.prompt}</td>
                <td>
                  <span className={`sph-post-type ${postTypeDisplay.class}`}>
                    <span className="sph-post-type-icon">{postTypeDisplay.icon}</span>
                    <span className="sph-post-type-label">{postTypeDisplay.label}</span>
                  </span>
                </td>
                <td>{formatDateTime(post.scheduled_datetime)}</td>
                <td><span className={`sph-status sph-status-${post.status}`}>{post.status}</span></td>
                <td>
                  {post.status === 'scheduled' ? (
                    <>
                      <button className="sph-action-btn sph-edit" onClick={() => handleEdit(post)} title="Edit">
                        <span role="img" aria-label="edit">✏️</span>
                      </button>
                      <button className="sph-action-btn sph-delete" onClick={() => handleDelete(post)} title="Delete">
                        <span role="img" aria-label="delete">🗑️</span>
                      </button>
                    </>
                  ) : (
                    <span className="sph-no-actions">No actions available</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {message && <div className="sph-message">{message}</div>}
      {showConfirm && (
        <div className="sph-modal">
          <div className="sph-modal-content">
            <p>Are you sure you want to delete this post?</p>
            <button onClick={confirmDelete}>Yes, Delete</button>
            <button onClick={() => setShowConfirm(false)}>Cancel</button>
          </div>
        </div>
      )}
      {editPost && (
        <EditPostModal post={editPost} onSave={handleSaveEdit} onClose={() => setEditPost(null)} />
      )}
    </div>
  );
}

function EditPostModal({ post, onSave, onClose }) {
  const [form, setForm] = useState({ ...post });
  
  // Only allow editing if status is 'scheduled'
  if (post.status !== 'scheduled') {
    return null;
  }
  
  return (
    <div className="sph-modal">
      <div className="sph-modal-content">
        <h3>Edit Scheduled Post</h3>
        <label>Caption</label>
        <textarea 
          value={form.prompt} 
          onChange={e => setForm({ ...form, prompt: e.target.value })}
          placeholder="Enter post caption..."
        />
        <label>Post Type</label>
        <select 
          value={form.post_type || 'photo'} 
          onChange={e => setForm({ ...form, post_type: e.target.value })}
        >
          <option value="photo">Photo</option>
          <option value="carousel">Carousel</option>
          <option value="reel">Reel</option>
        </select>
        <label>Date & Time</label>
        <input 
          type="datetime-local" 
          value={form.scheduled_datetime?.slice(0, 16)} 
          onChange={e => setForm({ ...form, scheduled_datetime: e.target.value })}
        />
        <div className="sph-modal-actions">
          <button onClick={() => onSave(form)}>Save</button>
          <button onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default ScheduledPostHistory; 