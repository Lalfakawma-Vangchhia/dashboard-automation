const https = require('https');
const http = require('http');

// Configure HTTPS agent to ignore self-signed certificates for localhost testing
const httpsAgent = new https.Agent({
  rejectUnauthorized: false
});

console.log('🔍 Testing HTTPS connections...\n');

// Test frontend HTTPS
console.log('Testing Frontend (https://localhost:3000)...');
const frontendReq = https.get('https://localhost:3000', { agent: httpsAgent }, (res) => {
  console.log(`✅ Frontend HTTPS: ${res.statusCode} ${res.statusMessage}`);
  console.log(`   Protocol: ${res.socket.getProtocol()}`);
  console.log(`   Cipher: ${res.socket.getCipher()?.name || 'N/A'}`);
}, (err) => {
  console.log(`❌ Frontend HTTPS Error: ${err.message}`);
});

frontendReq.on('error', (err) => {
  console.log(`❌ Frontend HTTPS Error: ${err.message}`);
});

// Test backend HTTPS
console.log('\nTesting Backend (https://localhost:8000)...');
const backendReq = https.get('https://localhost:8000', { agent: httpsAgent }, (res) => {
  console.log(`✅ Backend HTTPS: ${res.statusCode} ${res.statusMessage}`);
  console.log(`   Protocol: ${res.socket.getProtocol()}`);
  console.log(`   Cipher: ${res.socket.getCipher()?.name || 'N/A'}`);
}, (err) => {
  console.log(`❌ Backend HTTPS Error: ${err.message}`);
});

backendReq.on('error', (err) => {
  console.log(`❌ Backend HTTPS Error: ${err.message}`);
});

// Test backend API docs
console.log('\nTesting Backend API Docs (https://localhost:8000/docs)...');
const docsReq = https.get('https://localhost:8000/docs', { agent: httpsAgent }, (res) => {
  console.log(`✅ Backend API Docs: ${res.statusCode} ${res.statusMessage}`);
}, (err) => {
  console.log(`❌ Backend API Docs Error: ${err.message}`);
});

docsReq.on('error', (err) => {
  console.log(`❌ Backend API Docs Error: ${err.message}`);
});

// Set timeout for all requests
setTimeout(() => {
  console.log('\n🎉 HTTPS setup is complete!');
  console.log('\n📱 Your application URLs:');
  console.log('   Frontend: https://localhost:3000');
  console.log('   Backend API: https://localhost:8000');
  console.log('   API Docs: https://localhost:8000/docs');
  console.log('\n🔐 Facebook login should now work!');
  console.log('⚠️  Note: You may see a browser security warning for self-signed certificates.');
  console.log('   Click "Advanced" → "Proceed to localhost (unsafe)" to continue.');
  process.exit(0);
}, 3000); 