const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔐 Generating SSL certificates for localhost...');

const certDir = __dirname;
const keyPath = path.join(certDir, 'localhost-key.pem');
const certPath = path.join(certDir, 'localhost.pem');

// Check if certificates already exist
if (fs.existsSync(keyPath) && fs.existsSync(certPath)) {
  console.log('✅ SSL certificates already exist');
  process.exit(0);
}

try {
  // Generate private key
  console.log('📝 Generating private key...');
  execSync(`openssl genrsa -out "${keyPath}" 2048`, { stdio: 'inherit' });
  
  // Generate certificate signing request
  console.log('📋 Generating certificate signing request...');
  const csrPath = path.join(certDir, 'localhost.csr');
  execSync(`openssl req -new -key "${keyPath}" -out "${csrPath}" -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"`, { stdio: 'inherit' });
  
  // Generate self-signed certificate
  console.log('🔒 Generating self-signed certificate...');
  execSync(`openssl x509 -req -in "${csrPath}" -signkey "${keyPath}" -out "${certPath}" -days 365`, { stdio: 'inherit' });
  
  // Clean up CSR file
  fs.unlinkSync(csrPath);
  
  console.log('✅ SSL certificates generated successfully!');
  console.log(`   Key: ${keyPath}`);
  console.log(`   Cert: ${certPath}`);
  console.log('🚀 You can now run your server with HTTPS');
  
} catch (error) {
  console.error('❌ Error generating certificates:', error.message);
  console.log('\n💡 Alternative: You can manually generate certificates using:');
  console.log('   openssl req -x509 -newkey rsa:2048 -keyout localhost-key.pem -out localhost.pem -days 365 -nodes -subj "/CN=localhost"');
  process.exit(1);
} 