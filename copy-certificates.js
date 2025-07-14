const fs = require('fs');
const path = require('path');

console.log('📋 Copying SSL certificates from frontend to backend...');

const frontendDir = path.join(__dirname, 'frontend');
const backendDir = path.join(__dirname, 'backend');

const keySource = path.join(frontendDir, 'localhost-key.pem');
const certSource = path.join(frontendDir, 'localhost.pem');
const keyDest = path.join(backendDir, 'localhost-key.pem');
const certDest = path.join(backendDir, 'localhost.pem');

// Check if source files exist
if (!fs.existsSync(keySource) || !fs.existsSync(certSource)) {
  console.error('❌ SSL certificates not found in frontend directory!');
  console.log('🔐 Please generate certificates first:');
  console.log('   cd frontend && npm run generate-certs');
  process.exit(1);
}

try {
  // Copy files
  fs.copyFileSync(keySource, keyDest);
  fs.copyFileSync(certSource, certDest);
  
  console.log('✅ SSL certificates copied successfully!');
  console.log(`   From: ${frontendDir}`);
  console.log(`   To: ${backendDir}`);
  console.log('🚀 Backend can now run with HTTPS');
  
} catch (error) {
  console.error('❌ Error copying certificates:', error.message);
  process.exit(1);
} 