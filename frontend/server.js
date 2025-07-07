const https = require('https');
const http = require('http');
const fs = require('fs');
const express = require('express');
const path = require('path');

const app = express();

// Serve static files from the React app build directory
app.use(express.static(path.join(__dirname, 'build')));

// API proxy middleware (optional - if you want to proxy API calls)
app.use('/api', (req, res) => {
  // Proxy to backend - you can implement this if needed
  res.status(404).json({ error: 'API proxy not implemented' });
});

// Catch all handler: send back React's index.html file for client-side routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

const PORT = process.env.PORT || 3000;
const USE_HTTPS = process.env.HTTPS === 'true' || process.env.USE_HTTPS === 'true';

if (USE_HTTPS) {
  // HTTPS Server Configuration
  const httpsOptions = {
    key: fs.readFileSync(path.join(__dirname, 'localhost-key.pem')),
    cert: fs.readFileSync(path.join(__dirname, 'localhost.pem'))
  };

  https.createServer(httpsOptions, app).listen(PORT, () => {
    console.log(`🔒 HTTPS Server running on https://localhost:${PORT}`);
    console.log('✅ Secure connection established');
  });
} else {
  // HTTP Server for development
  http.createServer(app).listen(PORT, () => {
    console.log(`🌐 HTTP Server running on http://localhost:${PORT}`);
  });
}

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  process.exit(0);
}); 