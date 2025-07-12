import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../services/apiClient';
import { fileToBase64 } from './FacebookUtils';
import './BulkComposer.css';

function BulkComposer({ selectedPage, onClose }) {

  const { user, isAuthenticated } = useAuth();
  
  // Strategy step state
  const [strategyData, setStrategyData] = useState({
    promptTemplate: '',
    customStrategyTemplate: '',
    startDate: '',
    endDate: '',
    frequency: 'daily',
    customCron: '',
    timeSlot: '09:00'
  });

  // Composer grid state
  const [composerRows, setComposerRows] = useState([]);
  const [selectedRows, setSelectedRows] = useState([]);
  const [editingCell, setEditingCell] = useState(null);
  const [dragStartRow, setDragStartRow] = useState(null);

  // Calendar preview state
  const [calendarView, setCalendarView] = useState('month');
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedCalendarDate, setSelectedCalendarDate] = useState(null);

  // Queue state
  const [isScheduling, setIsScheduling] = useState(false);
  const [scheduleProgress, setScheduleProgress] = useState(0);

  // Expanded view state
  const [expandedCaption, setExpandedCaption] = useState(null);
  const [mediaPreviewModal, setMediaPreviewModal] = useState(null);

  // Scheduled posts state
  const [scheduledPosts, setScheduledPosts] = useState([]);
  const [loadingScheduledPosts, setLoadingScheduledPosts] = useState(false);
  const [showScheduledPosts, setShowScheduledPosts] = useState(true);
  const [expandedSchedules, setExpandedSchedules] = useState(new Set());
  const [editingPost, setEditingPost] = useState(null);

  // Group scheduled posts by date
  const groupedSchedules = scheduledPosts.reduce((groups, post) => {
    const dateKey = post.scheduled_date;
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(post);
    return groups;
  }, {});

  // Sort dates in ascending order
  const sortedScheduleDates = Object.keys(groupedSchedules).sort();

  // Prompt templates
  const [promptTemplates, setPromptTemplates] = useState([
    { id: 1, name: 'Daily Motivation', prompt: 'Share an inspiring quote or motivational message for your audience' },
    { id: 2, name: 'Product Showcase', prompt: 'Highlight your best products with engaging descriptions' },
    { id: 3, name: 'Behind the Scenes', prompt: 'Share behind-the-scenes content about your business or team' },
    { id: 4, name: 'Customer Spotlight', prompt: 'Feature customer testimonials or success stories' },
    { id: 5, name: 'Industry Tips', prompt: 'Share valuable tips and insights related to your industry' },
    { id: 6, name: 'Custom', prompt: 'custom' }
  ]);

  const gridRef = useRef(null);

  // Initialize composer with default rows
  useEffect(() => {
    if (strategyData.startDate && strategyData.frequency) {
      generateInitialRows();
    }
  }, [strategyData.startDate, strategyData.endDate, strategyData.frequency, strategyData.timeSlot]);

  // Load scheduled posts
  const loadScheduledPosts = async () => {
    setLoadingScheduledPosts(true);
    try {
      const response = await apiClient.getBulkComposerContent();
      if (response && response.data) {
        setScheduledPosts(response.data);
      }
    } catch (error) {
      console.error('Error loading scheduled posts:', error);
      alert('Failed to load scheduled posts. Please try again.');
    } finally {
      setLoadingScheduledPosts(false);
    }
  };

  // Load scheduled posts when component mounts or when page is selected
  useEffect(() => {
    if (selectedPage && selectedPage.internalId) {
      loadScheduledPosts();
    }
  }, [selectedPage?.internalId]);

  // Auto-expand today's schedule and recent schedules
  useEffect(() => {
    if (scheduledPosts.length > 0) {
      const today = new Date().toISOString().split('T')[0];
      const recentDates = sortedScheduleDates.slice(0, 3); // Show first 3 dates
      const autoExpandDates = new Set();
      
      // Always expand today if it exists
      if (groupedSchedules[today]) {
        autoExpandDates.add(today);
      }
      
      // Expand first few dates
      recentDates.forEach(date => autoExpandDates.add(date));
      
      setExpandedSchedules(autoExpandDates);
    }
  }, [scheduledPosts, sortedScheduleDates]);


  const generateInitialRows = useCallback(() => {
    if (!strategyData.startDate) return;
    
    // Create dates in local timezone to avoid timezone issues
    const startDateParts = strategyData.startDate.split('-');
    const startDate = new Date(parseInt(startDateParts[0]), parseInt(startDateParts[1]) - 1, parseInt(startDateParts[2]));
    
    let endDate = null;
    if (strategyData.endDate) {
      const endDateParts = strategyData.endDate.split('-');
      endDate = new Date(parseInt(endDateParts[0]), parseInt(endDateParts[1]) - 1, parseInt(endDateParts[2]));
    }
    
    const rows = [];
    const maxDays = 75; // Facebook's 75-day limit
    let currentDate = new Date(startDate);
    let dayCount = 0;
    let rowCount = 0;

    // If no end date is provided, only schedule the start date (single day)
    if (!endDate) {
      const formattedDate = startDate.getFullYear() + '-' + 
        String(startDate.getMonth() + 1).padStart(2, '0') + '-' + 
        String(startDate.getDate()).padStart(2, '0');
      
      rows.push({
        id: `row-0`,
        caption: '',
        mediaFile: null,
        mediaPreview: null,
        scheduledDate: formattedDate,
        scheduledTime: strategyData.timeSlot,
        status: 'draft',
        isSelected: false
      });
    } else {
      // Multiple day scheduling with end date
      while (dayCount < maxDays && rowCount < 50) { // Limit to 50 rows max
        // Stop if we have an end date and current date exceeds it
        if (endDate && currentDate > endDate) {
          break;
        }

        // Stop if beyond 75 days from now
        const maxAllowedDate = new Date(Date.now() + 75 * 24 * 60 * 60 * 1000);
        if (currentDate > maxAllowedDate) {
          break;
        }

        // Apply frequency logic
        let shouldInclude = false;
        switch (strategyData.frequency) {
          case 'daily':
            shouldInclude = true;
            break;
          case 'weekly':
            // Check if it's the same day of the week as start date
            shouldInclude = currentDate.getDay() === startDate.getDay();
            break;
          case 'monthly':
            // Check if it's the same day of the month as start date
            shouldInclude = currentDate.getDate() === startDate.getDate();
            break;
          case 'custom':
            // For custom cron, include every day for now
            shouldInclude = true;
            break;
          default:
            shouldInclude = true;
        }

        if (shouldInclude) {
          // Format date consistently in YYYY-MM-DD format
          const formattedDate = currentDate.getFullYear() + '-' + 
            String(currentDate.getMonth() + 1).padStart(2, '0') + '-' + 
            String(currentDate.getDate()).padStart(2, '0');
          
          rows.push({
            id: `row-${rowCount}`,
            caption: '',
            mediaFile: null,
            mediaPreview: null,
            scheduledDate: formattedDate,
            scheduledTime: strategyData.timeSlot,
            status: 'draft',
            isSelected: false
          });
          rowCount++;
        }

        // Move to next day
        currentDate.setDate(currentDate.getDate() + 1);
        dayCount++;
      }
    }

    setComposerRows(rows);
  }, [strategyData.startDate, strategyData.endDate, strategyData.frequency, strategyData.timeSlot]);

  const handleStrategyChange = useCallback((field, value) => {
    setStrategyData(prev => {
      const newData = { ...prev, [field]: value };
      return newData;
    });
    
    // If prompt template is selected, apply it to all rows
    if (field === 'promptTemplate' && value) {
      setComposerRows(prev => 
        prev.map(row => ({
          ...row,
          caption: value
        }))
      );
    }
    
    // Validate end date is not the same as start date (only if end date is provided)
    if (field === 'endDate' && value && value === strategyData.startDate) {
      alert('End date cannot be the same as start date. Please select a different end date or leave it empty.');
      return;
    }
    
    // If start date is changed and end date is before it, clear end date
    if (field === 'startDate' && strategyData.endDate && value > strategyData.endDate) {
      setStrategyData(prev => ({ ...prev, endDate: '' }));
    }
  }, [strategyData.startDate, strategyData.endDate]);

  const handleRowSelect = (rowId) => {
    setSelectedRows(prev => {
      if (prev.includes(rowId)) {
        return prev.filter(id => id !== rowId);
      } else {
        return [...prev, rowId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedRows.length === composerRows.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(composerRows.map(row => row.id));
    }
  };

  const handleCellEdit = (rowId, field, value) => {
    setComposerRows(prev => 
      prev.map(row => {
        if (row.id === rowId) {
          const updatedRow = { ...row, [field]: value };
          // If caption is being edited and has content, set status to ready
          if (field === 'caption' && value.trim()) {
            updatedRow.status = 'ready';
          }
          return updatedRow;
        }
        return row;
      })
    );
  };

  const handleMediaUpload = (rowId, event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setComposerRows(prev => 
          prev.map(row => 
            row.id === rowId ? { 
              ...row, 
              mediaFile: file, 
              mediaPreview: e.target.result 
            } : row
          )
        );
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateMedia = async (rowId) => {
    try {
      // Get the row to use its caption as image prompt
      const row = composerRows.find(r => r.id === rowId);
      if (!row) {
        alert('Row not found.');
        return;
      }

      // Use the caption as the image prompt
      const imagePrompt = row.caption.trim();
      if (!imagePrompt) {
        alert('Please add a caption first to generate an image.');
        return;
      }

      // Generate image using Stability AI with the caption as prompt
      const response = await apiClient.generateFacebookImage(imagePrompt, 'feed');
      
              if (response.success && response.data && response.data.image_url) {
          console.log(`Successfully generated image for row ${rowId}:`, response.data.image_url);
          setComposerRows(prev => {
            const updatedRows = prev.map(r => 
              r.id === rowId ? { 
                ...r, 
                mediaFile: null, // No file object for generated images
                mediaPreview: response.data.image_url,
                mediaGenerated: true,
                status: r.status === 'ready' ? 'ready' : 'draft' // Keep status as ready if it was ready
              } : r
            );
            console.log('Updated rows after image generation:', updatedRows);
            console.log('Updated row:', updatedRows.find(r => r.id === rowId));
            return updatedRows;
          });
        } else {
          console.log(`Failed to generate image for row ${rowId}:`, response);
          alert('Failed to generate image. Please try again.');
        }
    } catch (error) {
      console.error('Error generating media:', error);
      alert('Failed to generate image. Please try again.');
    }
  };

  const handleGenerateAllCaptions = async () => {
    console.log('=== Starting Generate Captions for Selected Rows ===');
    console.log('Strategy Data:', strategyData);
    console.log('Selected Rows:', selectedRows);
    
    if (selectedRows.length === 0) {
      alert('Please select at least one row to generate captions for.');
      return;
    }

    // Check if we have a strategy template selected
    if (!strategyData.promptTemplate) {
      alert('Please select a strategy template first.');
      return;
    }

    try {
      // Get only the selected rows
      const selectedComposerRows = composerRows.filter(row => selectedRows.includes(row.id));
      
      // Create contexts for each selected row (using dates as context)
      const contexts = selectedComposerRows.map(row => {
        const date = new Date(row.scheduledDate);
        return `Post for ${date.toLocaleDateString('en-US', { 
          weekday: 'long', 
          month: 'long', 
          day: 'numeric' 
        })}`;
      });
      
      console.log('Generated contexts for selected rows:', contexts);

      let response;
      
      if (strategyData.promptTemplate === 'custom') {
        console.log('Using custom strategy template');
        // Use custom strategy template
        if (!strategyData.customStrategyTemplate.trim()) {
          alert('Please enter a custom strategy template first.');
          return;
        }
        
        console.log('Calling generateBulkCaptions with:', {
          customStrategy: strategyData.customStrategyTemplate,
          contexts: contexts,
          maxLength: 2000
        });
        
        response = await apiClient.generateBulkCaptions(
          strategyData.customStrategyTemplate,
          contexts,
          2000
        );
      } else {
        console.log('Using predefined strategy template');
        // Use predefined strategy template
        const selectedTemplate = promptTemplates.find(t => t.prompt === strategyData.promptTemplate);
        console.log('Selected template:', selectedTemplate);
        
        if (!selectedTemplate) {
          alert('Invalid strategy template selected.');
          return;
        }
        
        // Generate captions using the predefined template for selected rows only
        const captions = [];
        for (let i = 0; i < contexts.length; i++) {
          try {
            console.log(`Generating caption ${i + 1}/${contexts.length} for context:`, contexts[i]);
            const context = contexts[i];
            const captionResponse = await apiClient.generateCaptionWithStrategy(
              selectedTemplate.prompt,
              context,
              2000
            );
            
            console.log(`Caption ${i + 1} response:`, captionResponse);
            
            if (captionResponse.success) {
              captions.push({
                content: captionResponse.content,
                context: context,
                success: true
              });
            } else {
              captions.push({
                content: `Failed to generate caption for: ${context}`,
                context: context,
                success: false,
                error: captionResponse.error || 'Unknown error'
              });
            }
          } catch (error) {
            console.error(`Error generating caption for context ${contexts[i]}:`, error);
            captions.push({
              content: `Failed to generate caption for: ${contexts[i]}`,
              context: contexts[i],
              success: false,
              error: error.message
            });
          }
        }
        
        response = {
          success: true,
          captions: captions,
          total_generated: captions.filter(c => c.success).length
        };
      }

      console.log('Final response:', response);

      if (response.success && response.captions) {
        // Update only selected rows with generated captions
        setComposerRows(prev => 
          prev.map(row => {
            if (selectedRows.includes(row.id)) {
              // Find the corresponding caption for this selected row
              const selectedIndex = selectedComposerRows.findIndex(selectedRow => selectedRow.id === row.id);
              const generatedCaption = response.captions[selectedIndex];
              if (generatedCaption && generatedCaption.success) {
                return {
                  ...row,
                  caption: generatedCaption.content,
                  status: 'ready' // Update status to ready
                };
              }
            }
            return row;
          })
        );

        alert(`Successfully generated ${response.total_generated} captions for selected rows!`);
      } else {
        alert('Failed to generate captions. Please try again.');
      }
    } catch (error) {
      console.error('Error generating captions:', error);
      alert('Failed to generate captions. Please try again.');
    }
  };

  // Generate images for all selected rows
  const handleGenerateAllImages = async () => {
    if (selectedRows.length === 0) {
      alert('Please select at least one row to generate images.');
      return;
    }

    try {
      const selectedComposerRows = composerRows.filter(row => selectedRows.includes(row.id));
      
      for (let i = 0; i < selectedComposerRows.length; i++) {
        const row = selectedComposerRows[i];
        
        if (!row.caption || !row.caption.trim()) {
          console.log(`Skipping image generation for row ${row.id} - no caption available`);
          continue;
        }

        console.log(`Generating image for row ${row.id} with caption: ${row.caption}`);
        
        // Use the caption as the image prompt
        const imagePrompt = row.caption.trim();
        
        // Generate image using Stability AI with the caption as prompt
        const response = await apiClient.generateFacebookImage(imagePrompt, 'feed');
        
        if (response.success && response.data && response.data.image_url) {
          console.log(`Successfully generated image for row ${row.id}:`, response.data.image_url);
          setComposerRows(prev => {
            const updatedRows = prev.map(r => 
              r.id === row.id ? { 
                ...r, 
                mediaFile: null, // No file object for generated images
                mediaPreview: response.data.image_url,
                mediaGenerated: true,
                status: r.status === 'ready' ? 'ready' : 'draft' // Keep status as ready if it was ready
              } : r
            );
            console.log('Updated rows:', updatedRows);
            console.log('Row after update:', updatedRows.find(r => r.id === row.id));
            return updatedRows;
          });
        } else {
          console.log(`Failed to generate image for row ${row.id}:`, response);
        }
      }
      
      alert('Image generation completed!');
    } catch (error) {
      console.error('Error generating images:', error);
      alert('Failed to generate images. Please try again.');
    }
  };

  const handleExpandCaption = (rowId) => {
    const row = composerRows.find(r => r.id === rowId);
    if (row) {
      setExpandedCaption({
        rowId,
        caption: row.caption,
        scheduledDate: row.scheduledDate,
        scheduledTime: row.scheduledTime
      });
    }
  };

  const handleViewMedia = (rowId) => {
    const row = composerRows.find(r => r.id === rowId);
    if (row && row.mediaPreview) {
      setMediaPreviewModal({
        rowId,
        mediaUrl: row.mediaPreview,
        mediaType: (row.mediaFile?.type?.startsWith('image/') || (row.mediaPreview && !row.mediaFile)) ? 'image' : 'video',
        caption: row.caption
      });
    }
  };

  const handleSaveExpandedCaption = (newCaption) => {
    if (expandedCaption) {
      setComposerRows(prev => 
        prev.map(row => 
          row.id === expandedCaption.rowId ? { 
            ...row, 
            caption: newCaption 
          } : row
        )
      );
      setExpandedCaption(null);
    }
  };

  const handleDuplicateRow = (rowId) => {
    const rowToDuplicate = composerRows.find(row => row.id === rowId);
    if (rowToDuplicate) {
      const newRow = {
        ...rowToDuplicate,
        id: `row-${Date.now()}-${Math.random()}`,
        scheduledDate: new Date(rowToDuplicate.scheduledDate).toISOString().split('T')[0]
      };
      setComposerRows(prev => [...prev, newRow]);
    }
  };

  const handleDeleteRow = (rowId) => {
    setComposerRows(prev => prev.filter(row => row.id !== rowId));
    setSelectedRows(prev => prev.filter(id => id !== rowId));
  };

  const handleBulkDelete = () => {
    setComposerRows(prev => prev.filter(row => !selectedRows.includes(row.id)));
    setSelectedRows([]);
  };

  const handleTimeShift = (direction) => {
    setComposerRows(prev => 
      prev.map(row => {
        if (selectedRows.includes(row.id)) {
          const [hours, minutes] = row.scheduledTime.split(':');
          let newHours = parseInt(hours) + (direction === 'forward' ? 1 : -1);
          if (newHours < 0) newHours = 23;
          if (newHours > 23) newHours = 0;
          return {
            ...row,
            scheduledTime: `${newHours.toString().padStart(2, '0')}:${minutes}`
          };
        }
        return row;
      })
    );
  };

  const handleDragStart = (rowId) => {
    setDragStartRow(rowId);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (targetRowId) => {
    if (dragStartRow && dragStartRow !== targetRowId) {
      const rows = [...composerRows];
      const sourceIndex = rows.findIndex(row => row.id === dragStartRow);
      const targetIndex = rows.findIndex(row => row.id === targetRowId);
      
      const [movedRow] = rows.splice(sourceIndex, 1);
      rows.splice(targetIndex, 0, movedRow);
      
      setComposerRows(rows);
    }
    setDragStartRow(null);
  };

  const handleScheduleAll = async () => {
    // More robust checking for selectedPage and its database ID
    if (!selectedPage || !selectedPage.internalId || composerRows.length === 0) {
      console.log('Selected Page Debug:', selectedPage);
      
      if (!selectedPage) {
        alert('Please select a page first before scheduling posts.');
        return;
      }
      
      if (!selectedPage.internalId) {
        alert(`The selected page "${selectedPage.name}" is not properly synced with the database. Please try the following:\n\n1. Disconnect and reconnect Facebook\n2. Wait a few seconds after reconnecting\n3. Select the page again\n\nIf this still doesn't work, check the browser console for more details.`);
        
        // Try to sync the page automatically
        console.log('Attempting to sync page with database...');
        console.log('Current user from auth context:', user);
        console.log('Looking for platform_user_id:', selectedPage.id);
        
        try {
          const socialAccounts = await apiClient.getSocialAccounts();
          console.log('Available social accounts (all):', socialAccounts);
          
          const facebookAccounts = socialAccounts.filter(acc => 
            acc.platform === 'facebook' && acc.is_connected
          );
          console.log('Facebook accounts (filtered by platform and connected):', facebookAccounts);
          console.log('Facebook account platform_user_ids:', facebookAccounts.map(acc => ({
            id: acc.id,
            user_id: acc.user_id,
            platform_user_id: acc.platform_user_id,
            username: acc.username,
            display_name: acc.display_name
          })));
          
          const matchingAccount = facebookAccounts.find(acc => 
            acc.platform_user_id === selectedPage.id
          );
          console.log('Matching account for selected page:', matchingAccount);
          
          if (matchingAccount) {
            console.log('Found matching account! Details:', {
              internal_id: matchingAccount.id,
              user_id: matchingAccount.user_id,
              platform_user_id: matchingAccount.platform_user_id,
              display_name: matchingAccount.display_name,
              current_user_id: user?.id
            });
            
            // Check if this account belongs to the current user
            if (user && matchingAccount.user_id !== user.id) {
              console.error('USER ID MISMATCH! Account belongs to user', matchingAccount.user_id, 'but current user is', user.id);
              alert(`Account mismatch detected. The page "${selectedPage.name}" belongs to a different user account. Please log out and log in with the correct account, or disconnect and reconnect Facebook.`);
            } else {
              console.log('User ID matches! Account should work.');
              // We can't directly update selectedPage here since it's passed as a prop
              // The user needs to trigger a refresh in the parent component
              alert(`Found database record for "${selectedPage.name}"! Internal ID: ${matchingAccount.id}. Please try selecting the page again or refresh the page.`);
            }
          } else {
            console.log('No matching account found. Available platform_user_ids:', 
              facebookAccounts.map(acc => acc.platform_user_id));
            console.log('Searching for platform_user_id:', selectedPage.id);
            console.log('Available accounts detail:', facebookAccounts.map(acc => ({
              id: acc.id,
              platform_user_id: acc.platform_user_id,
              display_name: acc.display_name,
              user_id: acc.user_id
            })));
            alert(`No database record found for page "${selectedPage.name}" (ID: ${selectedPage.id}). Please disconnect and reconnect Facebook.`);
          }
        } catch (error) {
          console.error('Error checking social accounts:', error);
          alert('Failed to check page sync status. Please disconnect and reconnect Facebook.');
        }
        return;
      }
      
      if (composerRows.length === 0) {
        alert('No posts to schedule. Please create some posts first.');
        return;
      }
    }

    // Check authentication
    if (!isAuthenticated) {
      alert('Please log in to schedule posts.');
      return;
    }

    // Filter only ready posts
    const readyPosts = composerRows.filter(row => row.status === 'ready' && row.caption.trim());
    
    console.log('=== Bulk Schedule Debug Info ===');
    console.log('Selected Page:', selectedPage);
    console.log('Using Database ID (internalId):', selectedPage.internalId);
    console.log('Facebook Page ID (for reference):', selectedPage.id);
    console.log('Total Composer Rows:', composerRows.length);
    console.log('Ready Posts:', readyPosts.length);
    console.log('Ready Posts Data:', readyPosts);
    
    if (readyPosts.length === 0) {
      alert('No posts are ready to be scheduled. Please generate captions first.');
      return;
    }

    setIsScheduling(true);
    setScheduleProgress(0);

    try {
      // Use the database ID (internalId) not the Facebook page ID
      const pageId = selectedPage.internalId;
      
      console.log('Using database social_account_id:', pageId);
      
      // Prepare bulk data with media files
      const postsWithMedia = await Promise.all(
        readyPosts.map(async (row) => {
          let mediaFile = null;
          
          // Handle uploaded files
          if (row.mediaFile) {
            try {
              mediaFile = await fileToBase64(row.mediaFile);
              console.log('Converted uploaded file to base64 for row:', row.id);
            } catch (error) {
              console.error('Error converting uploaded file to base64:', error);
            }
          }
          // Handle generated images
          else if (row.mediaPreview && !row.mediaFile) {
            // For generated images, we need to fetch the image and convert to base64
            try {
              console.log('Fetching generated image for row:', row.id, 'URL:', row.mediaPreview);
              const response = await fetch(row.mediaPreview);
              if (!response.ok) {
                throw new Error(`Failed to fetch image: ${response.status}`);
              }
              const blob = await response.blob();
              mediaFile = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = () => resolve(null);
                reader.readAsDataURL(blob);
              });
              console.log('Converted generated image to base64 for row:', row.id);
            } catch (error) {
              console.error('Error converting generated image to base64:', error);
            }
          }
          
          const postData = {
            caption: row.caption,
            scheduled_date: row.scheduledDate,
            scheduled_time: row.scheduledTime,
            media_file: mediaFile,
            media_filename: row.mediaFile ? row.mediaFile.name : (row.mediaPreview ? 'generated_image.jpg' : null)
          };
          
          console.log('Prepared post data for row:', row.id, {
            caption: postData.caption?.substring(0, 50) + '...',
            scheduled_date: postData.scheduled_date,
            scheduled_time: postData.scheduled_time,
            has_media: !!postData.media_file,
            media_filename: postData.media_filename
          });
          
          return postData;
        })
      );

      const requestPayload = { 
        social_account_id: pageId, 
        posts: postsWithMedia 
      };
      
      console.log('=== Sending to Backend ===');
      console.log('Database Page ID (social_account_id):', pageId);
      console.log('Number of posts:', postsWithMedia.length);
      console.log('Request payload structure:', {
        social_account_id: requestPayload.social_account_id,
        posts_count: requestPayload.posts.length,
        first_post_sample: requestPayload.posts[0] ? {
          caption: requestPayload.posts[0].caption?.substring(0, 50) + '...',
          scheduled_date: requestPayload.posts[0].scheduled_date,
          scheduled_time: requestPayload.posts[0].scheduled_time,
          has_media: !!requestPayload.posts[0].media_file,
          media_filename: requestPayload.posts[0].media_filename
        } : 'No posts'
      });

      // Send the bulk schedule request
      const response = await apiClient.bulkSchedulePosts(requestPayload);
      
      console.log('=== Backend Response ===');
      console.log('Full response:', response);
      
      // Update status of scheduled posts
      setComposerRows(prev => 
        prev.map(row => {
          if (readyPosts.some(readyPost => readyPost.id === row.id)) {
            return { ...row, status: 'scheduled' };
          }
          return row;
        })
      );
      
      setScheduleProgress(100);

      // Show success message with details
      const successCount = Array.isArray(response.results) ? response.results.filter(r => r.success).length : readyPosts.length;
      const failedCount = Array.isArray(response.results) ? response.results.filter(r => !r.success).length : 0;
      
      console.log('=== Results Summary ===');
      console.log('Success count:', successCount);
      console.log('Failed count:', failedCount);
      
      if (response.results && Array.isArray(response.results)) {
        console.log('Detailed results:', response.results);
        response.results.forEach((result, index) => {
          if (!result.success) {
            console.error(`Post ${index + 1} failed:`, result.error || result.message || 'Unknown error');
          }
        });
      }
      
      if (failedCount > 0) {
        alert(`Scheduled ${successCount} posts successfully. ${failedCount} posts failed. Check console for details.`);
      } else {
        alert(`Successfully scheduled ${successCount} posts!`);
      }
      
      // Reload scheduled posts to show the newly scheduled content
      await loadScheduledPosts();
      
      // Don't auto-close the modal anymore - let user choose when to close
      // onClose();
    } catch (error) {
      console.error('=== Frontend Error ===');
      console.error('Error scheduling posts:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      alert(`Error scheduling posts: ${error.message || 'Please try again.'}`);
    } finally {
      setIsScheduling(false);
      setScheduleProgress(0);
    }
  };

  const handleRemoveMedia = (rowId) => {
    setComposerRows(prev => 
      prev.map(row => 
        row.id === rowId ? { 
          ...row, 
          mediaFile: null, 
          mediaPreview: null,
          mediaGenerated: false // Reset generated status
        } : row
      )
    );
  };

  // Calendar helper functions
  const getDaysInMonth = (year, month) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year, month) => {
    return new Date(year, month, 1).getDay();
  };

  const generateCalendarDays = (year, month) => {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDayOfMonth = getFirstDayOfMonth(year, month);
    const days = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push({ day: null, date: null });
    }

    // Add days of the month
    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(year, month, i);
      days.push({ day: i, date: date });
    }

    return days;
  };

  const handleCalendarDateSelect = (date) => {
    setSelectedCalendarDate(date);
    // Auto-populate Step 2 with the selected date
    setStrategyData(prev => ({
      ...prev,
      startDate: date.toISOString().split('T')[0]
    }));
  };

  const getPostsForDate = (date) => {
    // Format date consistently to avoid timezone issues
    const dateString = date.getFullYear() + '-' + 
      String(date.getMonth() + 1).padStart(2, '0') + '-' + 
      String(date.getDate()).padStart(2, '0');
    const postsForDate = composerRows.filter(row => row.scheduledDate === dateString);
    if (postsForDate.length > 0) {
      console.log('Found posts for date:', dateString, 'Count:', postsForDate.length);
    }
    return postsForDate;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'published':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
        );
      case 'failed':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        );
      case 'scheduled':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12,6 12,12 16,14"/>
          </svg>
        );
      case 'ready':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 12l2 2 4-4"/>
            <circle cx="12" cy="12" r="10"/>
          </svg>
        );
      default:
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        );
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'published':
        return 'status-published';
      case 'failed':
        return 'status-failed';
      case 'scheduled':
        return 'status-scheduled';
      case 'ready':
        return 'status-ready';
      default:
        return 'status-draft';
    }
  };

  // Handle schedule expansion
  const toggleScheduleExpansion = (dateKey) => {
    setExpandedSchedules(prev => {
      const newSet = new Set(prev);
      if (newSet.has(dateKey)) {
        newSet.delete(dateKey);
      } else {
        newSet.add(dateKey);
      }
      return newSet;
    });
  };

  // Handle post editing
  const startEditingPost = (post) => {
    setEditingPost({
      id: post.id,
      caption: post.caption,
      original: post
    });
  };

  const savePostEdit = async () => {
    if (!editingPost) return;
    
    try {
      // Call API to update post caption
      await apiClient.updateBulkComposerPost(editingPost.id, editingPost.caption);
      
      // Update local state
      setScheduledPosts(prev => 
        prev.map(post => 
          post.id === editingPost.id 
            ? { ...post, caption: editingPost.caption }
            : post
        )
      );
      
      setEditingPost(null);
      alert('Post updated successfully!');
    } catch (error) {
      console.error('Error updating post:', error);
      alert('Failed to update post. Please try again.');
    }
  };

  const cancelPostEdit = () => {
    setEditingPost(null);
  };

  const cancelScheduledPost = async (postId, postCaption) => {
    if (!window.confirm(`Are you sure you want to cancel this scheduled post?\n\n"${postCaption.substring(0, 100)}..."`)) {
      return;
    }
    
    try {
      await apiClient.cancelBulkComposerPost(postId);
      
      // Remove from local state
      setScheduledPosts(prev => prev.filter(post => post.id !== postId));
      
      alert('Scheduled post canceled successfully!');
    } catch (error) {
      console.error('Error canceling post:', error);
      alert('Failed to cancel post. Please try again.');
    }
  };

  return (
    <div className="bulk-composer">
      {/* Only keep the header and content, no card or extra wrapper */}
      <div className="bulk-composer-header">
        <h2>Bulk Composer</h2>
        {!isAuthenticated && (
          <div className="auth-warning">
            <span style={{ color: '#ff6b6b', fontSize: '14px' }}>
              ⚠️ Please log in to schedule posts
            </span>
          </div>
        )}
      </div>
      <div className="bulk-composer-content">
        {/* Strategy and Calendar Combined */}
        <div className="strategy-calendar-section">
          <div className="strategy-step">
            <h3>Step 1: Strategy & Schedule</h3>
            <div className="strategy-form">
              <div className="form-group">
                <label>Strategy Template</label>
                <select
                  value={strategyData.promptTemplate}
                  onChange={(e) => handleStrategyChange('promptTemplate', e.target.value)}
                  className="form-select"
                >
                  <option value="">Select a template...</option>
                  {promptTemplates.map(template => (
                    <option key={template.id} value={template.prompt}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>

              {strategyData.promptTemplate === 'custom' && (
                <div className="form-group">
                  <label>Custom Strategy Template</label>
                  <textarea
                    value={strategyData.customStrategyTemplate}
                    onChange={(e) => handleStrategyChange('customStrategyTemplate', e.target.value)}
                    placeholder="Enter your custom strategy template. This will be used by AI to generate captions that follow your specific style and approach..."
                    className="form-textarea"
                    rows="3"
                  />
                  <small className="form-help">
                    Describe your content strategy, tone, style, and any specific requirements for your posts.
                  </small>
                </div>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={strategyData.startDate}
                    onChange={(e) => handleStrategyChange('startDate', e.target.value)}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>End Date (Optional)</label>
                  <div className="end-date-container">
                    <input
                      type="date"
                      value={strategyData.endDate}
                      onChange={(e) => handleStrategyChange('endDate', e.target.value)}
                      className="form-input"
                      min={strategyData.startDate}
                      disabled={!strategyData.startDate}
                    />
                    <button
                      type="button"
                      onClick={() => handleStrategyChange('endDate', '')}
                      className="btn btn-secondary btn-small"
                      disabled={!strategyData.endDate}
                      title="Clear end date (single day schedule)"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                      Clear
                    </button>
                  </div>
                  <small className="form-help">
                    Leave empty for single day schedule
                  </small>
                </div>

                <div className="form-group">
                  <label>Frequency</label>
                  <select
                    value={strategyData.frequency}
                    onChange={(e) => handleStrategyChange('frequency', e.target.value)}
                    className="form-select"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="custom">Custom Cron</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Time Slot</label>
                  <input
                    type="time"
                    value={strategyData.timeSlot}
                    onChange={(e) => handleStrategyChange('timeSlot', e.target.value)}
                    className="form-input"
                  />
                </div>
              </div>

              {strategyData.frequency === 'custom' && (
                <div className="form-group">
                  <label>Custom Cron Expression</label>
                  <input
                    type="text"
                    value={strategyData.customCron}
                    onChange={(e) => handleStrategyChange('customCron', e.target.value)}
                    placeholder="0 9 * * * (daily at 9 AM)"
                    className="form-input"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Calendar Preview */}
          <div className="calendar-preview-section">
            <h3>Calendar Preview</h3>
            <div className="calendar-container">
              <div className="calendar-header">
                <button
                  onClick={() => setCurrentMonth(prev => new Date(prev.getFullYear(), prev.getMonth() - 1))}
                  className="btn btn-secondary btn-small"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="15,18 9,12 15,6"/>
                  </svg>
                </button>
                <h4>{currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h4>
                <button
                  onClick={() => setCurrentMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + 1))}
                  className="btn btn-secondary btn-small"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9,18 15,12 9,6"/>
                  </svg>
                </button>
              </div>
              <div className="calendar-grid">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="calendar-day-header">{day}</div>
                ))}
                {generateCalendarDays(currentMonth.getFullYear(), currentMonth.getMonth()).map((day, index) => (
                  <div 
                    key={index} 
                    className={`calendar-day ${day.date ? 'clickable' : ''} ${day.date && getPostsForDate(day.date).length > 0 ? 'has-posts' : ''}`}
                  >
                    <span className="day-number">{day.day}</span>
                    {day.date && getPostsForDate(day.date).length > 0 && (
                      <div className="post-indicators">
                        {getPostsForDate(day.date).map((post, postIndex) => (
                          <div
                            key={postIndex}
                            className="post-dot"
                            title={`${post.scheduledTime} - ${post.caption.substring(0, 30)}...`}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Composer Grid */}
        <div className="composer-grid-section">
          <div className="composer-header">
            <h3>Step 2: Content Grid</h3>
            <div className="composer-controls">
              <button
                onClick={() => {
                  const newRow = {
                    id: `row-${Date.now()}-${Math.random()}`,
                    caption: '',
                    mediaFile: null,
                    mediaPreview: null,
                    scheduledDate: new Date().toISOString().split('T')[0],
                    scheduledTime: strategyData.timeSlot,
                    status: 'draft',
                    isSelected: false
                  };
                  setComposerRows(prev => [...prev, newRow]);
                }}
                className="btn btn-primary btn-small"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Add Row
              </button>
              <button
                onClick={handleSelectAll}
                className="btn btn-secondary btn-small"
              >
                {selectedRows.length === composerRows.length ? 'Deselect All' : 'Select All'}
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={selectedRows.length === 0}
                className="btn btn-danger btn-small"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3,6 5,6 21,6"/>
                  <path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6m3,0V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"/>
                </svg>
                Delete Selected
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleGenerateAllCaptions}
                disabled={composerRows.length === 0 || selectedRows.length === 0}
              >
                Generate Captions
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={handleGenerateAllImages}
                disabled={composerRows.length === 0 || selectedRows.length === 0}
              >
                Generate Images
              </button>
            </div>
          </div>

          <div className="composer-grid-container">
            <div className="composer-grid" ref={gridRef}>
              <div className="grid-header grid-row">
                <div className="grid-cell header-cell"></div>
                <div className="grid-cell header-cell">Caption</div>
                <div className="grid-cell header-cell">Media</div>
                <div className="grid-cell header-cell">Date</div>
                <div className="grid-cell header-cell">Time</div>
                <div className="grid-cell header-cell">Status</div>
              </div>

              <div className="grid-body">
                {composerRows.map((row, index) => (
                  <div
                    key={row.id}
                    className={`grid-row ${row.isSelected ? 'selected' : ''}`}
                    draggable
                    onDragStart={() => handleDragStart(row.id)}
                    onDragOver={handleDragOver}
                    onDrop={() => handleDrop(row.id)}
                  >
                    <div className="grid-cell">
                      <input
                        type="checkbox"
                        checked={selectedRows.includes(row.id)}
                        onChange={() => handleRowSelect(row.id)}
                      />
                    </div>
                    
                    <div className="grid-cell caption-cell">
                      <div className="caption-container">
                        <textarea
                          value={row.caption}
                          onChange={(e) => handleCellEdit(row.id, 'caption', e.target.value)}
                          placeholder="Enter your post caption..."
                          className="caption-input"
                          rows="3"
                          style={{ resize: 'none' }}
                        />
                        <button
                          onClick={() => handleExpandCaption(row.id)}
                          className="expand-btn"
                          title="Expand caption"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M15 3h6v6"/>
                            <path d="M9 21H3v-6"/>
                            <path d="M21 3l-7 7"/>
                            <path d="M3 21l7-7"/>
                          </svg>
                        </button>
                      </div>
                    </div>
                    
                    <div className="grid-cell media-cell">
                      <div className="media-options">
                        {!row.mediaPreview && !row.mediaFile ? (
                          <div className="media-option-group">
                            <input
                              type="file"
                              accept="image/*,video/*"
                              onChange={(e) => handleMediaUpload(row.id, e)}
                              className="media-input"
                              id={`media-upload-${row.id}`}
                            />
                            <label htmlFor={`media-upload-${row.id}`} className="media-option-btn upload-btn">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7,10 12,15 17,10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                              </svg>
                              Upload
                            </label>
                            <button
                              onClick={() => handleGenerateMedia(row.id)}
                              className="media-option-btn generate-btn"
                            >
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                              </svg>
                              Generate
                            </button>
                          </div>
                        ) : (
                          <div className="media-preview">
                            {(() => {
                              console.log(`Rendering media for row ${row.id}:`, {
                                mediaFile: row.mediaFile,
                                mediaPreview: row.mediaPreview,
                                mediaGenerated: row.mediaGenerated,
                                hasMediaPreview: !!row.mediaPreview,
                                hasMediaFile: !!row.mediaFile
                              });
                              
                              // For generated images (no mediaFile, but has mediaPreview)
                              if (row.mediaPreview && !row.mediaFile) {
                                console.log(`Rendering generated image for row ${row.id}:`, row.mediaPreview);
                                return <img src={row.mediaPreview} alt="Generated Preview" />;
                              }
                              
                              // For uploaded files
                              if (row.mediaFile?.type?.startsWith('image/')) {
                                console.log(`Rendering uploaded image for row ${row.id}:`, row.mediaPreview);
                                return <img src={row.mediaPreview} alt="Uploaded Preview" />;
                              }
                              
                              // For videos
                              console.log(`Rendering video for row ${row.id}:`, row.mediaPreview);
                              return <video src={row.mediaPreview} controls />;
                            })()}
                            <button
                              onClick={() => handleViewMedia(row.id)}
                              className="view-media-btn"
                              title="View media"
                            >
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                              </svg>
                            </button>
                            <button
                              onClick={() => handleRemoveMedia(row.id)}
                              className="remove-media-btn"
                              title="Remove media"
                            >
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                              </svg>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="grid-cell date-cell">
                      <input
                        type="date"
                        value={row.scheduledDate}
                        onChange={(e) => handleCellEdit(row.id, 'scheduledDate', e.target.value)}
                        className="date-input"
                      />
                    </div>
                    
                    <div className="grid-cell time-cell">
                      <input
                        type="time"
                        value={row.scheduledTime}
                        onChange={(e) => handleCellEdit(row.id, 'scheduledTime', e.target.value)}
                        className="time-input"
                      />
                    </div>
                    
                    <div className="grid-cell status-cell">
                      <span className={`status-badge ${getStatusClass(row.status)}`}>
                        {getStatusIcon(row.status)} {row.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Queue Confirmation */}
        <div className="queue-confirmation">
          <h3>Step 3: Schedule & Publish</h3>
          <div className="confirmation-stats">
            <div className="stat-item">
              <span className="stat-label">Total Posts:</span>
              <span className="stat-value">{composerRows.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">With Captions:</span>
              <span className="stat-value">{composerRows.filter(row => row.caption.trim()).length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Ready to Schedule:</span>
              <span className="stat-value">{composerRows.filter(row => row.status === 'ready').length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">With Media:</span>
              <span className="stat-value">{composerRows.filter(row => row.mediaFile || row.mediaPreview).length}</span>
            </div>
          </div>

          {isScheduling && (
            <div className="schedule-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${scheduleProgress}%` }}
                />
              </div>
              <span className="progress-text">Scheduling posts... {Math.round(scheduleProgress)}%</span>
            </div>
          )}

          <div className="confirmation-actions">
            <button
              onClick={handleScheduleAll}
              disabled={isScheduling || composerRows.filter(row => row.status === 'ready').length === 0 || !isAuthenticated}
              className="btn btn-primary btn-large"
            >
              {isScheduling ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                  </svg>
                  Scheduling...
                </>
              ) : !isAuthenticated ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                    <polyline points="10,17 15,12 10,7"/>
                    <line x1="15" y1="12" x2="3" y2="12"/>
                  </svg>
                  Please Log In to Schedule
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12,6 12,12 16,14"/>
                  </svg>
                  Schedule Ready Posts ({composerRows.filter(row => row.status === 'ready').length})
                </>
              )}
            </button>
          </div>
        </div>

        {/* Scheduled Posts View */}
        <div className="scheduled-posts-section">
          <div className="scheduled-posts-header">
            <h3>Scheduled Posts</h3>
            <div className="scheduled-posts-controls">
              <button
                onClick={() => setShowScheduledPosts(!showScheduledPosts)}
                className="btn btn-secondary btn-small"
              >
                {showScheduledPosts ? 'Hide' : 'Show'} Scheduled Posts ({scheduledPosts.length})
              </button>
              <button
                onClick={loadScheduledPosts}
                disabled={loadingScheduledPosts}
                className="btn btn-secondary btn-small"
              >
                {loadingScheduledPosts ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M23 4v6h-6"/>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                  </svg>
                )}
                Refresh
              </button>
            </div>
          </div>

          {showScheduledPosts && (
            <div className="scheduled-posts-container">
              {loadingScheduledPosts ? (
                <div className="loading-scheduled-posts">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                  </svg>
                  Loading scheduled posts...
                </div>
              ) : sortedScheduleDates.length > 0 ? (
                <div className="scheduled-posts-list">
                  {sortedScheduleDates.map(dateKey => (
                    <div key={dateKey} className="scheduled-post-group">
                      <div 
                        className="schedule-group-header"
                        onClick={() => toggleScheduleExpansion(dateKey)}
                      >
                        <div className="schedule-info">
                          <h4 className="schedule-date">
                            {new Date(dateKey).toLocaleDateString('en-US', { 
                              weekday: 'long',
                              month: 'long', 
                              day: 'numeric',
                              year: 'numeric'
                            })}
                          </h4>
                          <div className="schedule-stats">
                            <span className="post-count">{groupedSchedules[dateKey].length} post{groupedSchedules[dateKey].length !== 1 ? 's' : ''}</span>
                            <span className="status-breakdown">
                              {(() => {
                                const statuses = groupedSchedules[dateKey].reduce((acc, post) => {
                                  acc[post.status] = (acc[post.status] || 0) + 1;
                                  return acc;
                                }, {});
                                return Object.entries(statuses).map(([status, count]) => (
                                  <span key={status} className={`status-chip ${status.toLowerCase()}`}>
                                    {count} {status}
                                  </span>
                                ));
                              })()}
                            </span>
                          </div>
                        </div>
                        <div className="expand-controls">
                          <button
                            className={`expand-btn ${expandedSchedules.has(dateKey) ? 'expanded' : ''}`}
                            title={expandedSchedules.has(dateKey) ? 'Collapse' : 'Expand'}
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="6,9 12,15 18,9"/>
                            </svg>
                          </button>
                        </div>
                      </div>
                      
                      {expandedSchedules.has(dateKey) && (
                        <div className="schedule-content-grid">
                          <div className="content-grid-header">
                            <div className="grid-header-cell">Status</div>
                            <div className="grid-header-cell">Caption</div>
                            <div className="grid-header-cell">Time</div>
                            <div className="grid-header-cell">Media</div>
                            <div className="grid-header-cell">Actions</div>
                          </div>
                          
                          {groupedSchedules[dateKey]
                            .sort((a, b) => a.scheduled_time.localeCompare(b.scheduled_time))
                            .map((post) => (
                            <div key={post.id} className="content-grid-row">
                              <div className="grid-cell status-cell">
                                <span className={`post-status-badge ${post.status.toLowerCase()}`}>
                                  {getStatusIcon(post.status)} {post.status}
                                </span>
                              </div>
                              
                              <div className="grid-cell caption-cell">
                                {editingPost && editingPost.id === post.id ? (
                                  <textarea
                                    value={editingPost.caption}
                                    onChange={(e) => setEditingPost(prev => ({ ...prev, caption: e.target.value }))}
                                    className="inline-caption-editor"
                                    rows="4"
                                    placeholder="Enter your caption..."
                                  />
                                ) : (
                                  <div className="caption-preview" onClick={() => startEditingPost(post)}>
                                    {post.caption.length > 100 
                                      ? `${post.caption.substring(0, 100)}...` 
                                      : post.caption
                                    }
                                  </div>
                                )}
                              </div>
                              
                              <div className="grid-cell time-cell">
                                <span className="schedule-time">{post.scheduled_time}</span>
                              </div>
                              
                              <div className="grid-cell media-cell">
                                {post.media_filename ? (
                                  <div className="media-indicator">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                      <circle cx="8.5" cy="8.5" r="1.5"/>
                                      <polyline points="21,15 16,10 5,21"/>
                                    </svg>
                                    {post.media_filename}
                                  </div>
                                ) : (
                                  <span className="no-media">Text only</span>
                                )}
                              </div>
                              
                              <div className="grid-cell actions-cell">
                                {editingPost && editingPost.id === post.id ? (
                                  <div className="edit-actions">
                                    <button
                                      onClick={savePostEdit}
                                      className="btn btn-success btn-small"
                                    >
                                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                                        <polyline points="17,21 17,13 7,13 7,21"/>
                                        <polyline points="7,3 7,8 15,8"/>
                                      </svg>
                                      Save
                                    </button>
                                    <button
                                      onClick={cancelPostEdit}
                                      className="btn btn-secondary btn-small"
                                    >
                                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                      </svg>
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <div className="post-actions">
                                    <button
                                      onClick={() => startEditingPost(post)}
                                      className="btn btn-primary btn-small"
                                      title="Edit caption"
                                    >
                                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                        <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                      </svg>
                                      Edit
                                    </button>
                                    {post.status === 'scheduled' && (
                                      <button
                                        onClick={() => cancelScheduledPost(post.id, post.caption)}
                                        className="btn btn-danger btn-small"
                                        title="Cancel scheduled post"
                                      >
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                          <circle cx="12" cy="12" r="10"/>
                                          <line x1="15" y1="9" x2="9" y2="15"/>
                                          <line x1="9" y1="9" x2="15" y2="15"/>
                                        </svg>
                                        Cancel
                                      </button>
                                    )}
                                  </div>
                                )}
                              </div>
                              
                              {post.error_message && (
                                <div className="grid-cell error-cell full-width">
                                  <div className="error-message">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      <circle cx="12" cy="12" r="10"/>
                                      <line x1="15" y1="9" x2="9" y2="15"/>
                                      <line x1="9" y1="9" x2="15" y2="15"/>
                                    </svg>
                                    {post.error_message}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-scheduled-posts">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12,6 12,12 16,14"/>
                  </svg>
                  <p>No scheduled posts yet. Create and schedule some posts above!</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Expanded Caption Modal */}
      {expandedCaption && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Edit Caption</h3>
              <button 
                onClick={() => setExpandedCaption(null)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="caption-info">
                <p><strong>Scheduled:</strong> {expandedCaption.scheduledDate} at {expandedCaption.scheduledTime}</p>
              </div>
              <textarea
                value={expandedCaption.caption}
                onChange={(e) => setExpandedCaption(prev => ({ ...prev, caption: e.target.value }))}
                className="expanded-caption-textarea"
                rows="10"
                placeholder="Enter your caption..."
              />
            </div>
            <div className="modal-footer">
              <button 
                onClick={() => setExpandedCaption(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={() => handleSaveExpandedCaption(expandedCaption.caption)}
                className="btn btn-primary"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Media Preview Modal */}
      {mediaPreviewModal && (
        <div className="modal-overlay">
          <div className="modal-content media-preview-modal">
            <div className="modal-header">
              <h3>Media Preview</h3>
              <button 
                onClick={() => setMediaPreviewModal(null)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              {mediaPreviewModal.mediaType === 'image' ? (
                <img 
                  src={mediaPreviewModal.mediaUrl} 
                  alt="Media preview" 
                  className="modal-media"
                />
              ) : (
                <video 
                  src={mediaPreviewModal.mediaUrl} 
                  controls 
                  className="modal-media"
                />
              )}
              {mediaPreviewModal.caption && (
                <div className="modal-caption">
                  <h4>Caption:</h4>
                  <p>{mediaPreviewModal.caption}</p>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                onClick={() => setMediaPreviewModal(null)}
                className="btn btn-primary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BulkComposer; 