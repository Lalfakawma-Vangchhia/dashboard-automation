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
  // Check if SSL certificates exist
  const keyPath = path.join(__dirname, 'localhost-key.pem');
  const certPath = path.join(__dirname, 'localhost.pem');
  
  if (!fs.existsSync(keyPath) || !fs.existsSync(certPath)) {
    console.error('❌ SSL certificates not found!');
    console.log('🔐 Please generate SSL certificates first:');
    console.log('   node generate-certificates.js');
    console.log('   or run: npm run generate-certs');
    console.log('\n🌐 Falling back to HTTP server...');
    
    // Fall back to HTTP
    http.createServer(app).listen(PORT, () => {
      console.log(`🌐 HTTP Server running on http://localhost:${PORT}`);
      console.log('⚠️  Note: Facebook login requires HTTPS');
    });
  } else {
    // HTTPS Server Configuration
    const httpsOptions = {
      key: fs.readFileSync(keyPath),
      cert: fs.readFileSync(certPath)
    };

    https.createServer(httpsOptions, app).listen(PORT, () => {
      console.log(`🔒 HTTPS Server running on https://localhost:${PORT}`);
      console.log('✅ Secure connection established');
      console.log('🎉 Facebook login should now work!');
    });
  }
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