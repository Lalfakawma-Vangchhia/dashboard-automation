# HTTPS Setup Guide

This guide will help you set up HTTPS for your IGAuth project to enable Facebook login.

## Why HTTPS?

Facebook requires HTTPS for OAuth login flows. Without HTTPS, you'll see the error:
> "Facebook has detected that IGAuth isn't using a secure connection to transfer information."

## Quick Setup

### Option 1: One-command setup (Recommended)
```bash
npm run setup-https
```

This will:
1. Generate SSL certificates for localhost
2. Copy them to both frontend and backend directories

### Option 2: Manual setup

1. **Generate certificates:**
   ```bash
   cd frontend
   npm run generate-certs
   ```

2. **Copy certificates to backend:**
   ```bash
   node copy-certificates.js
   ```

## Running with HTTPS

### Frontend only (with HTTPS):
```bash
cd frontend
npm run start-dev-https
```

### Backend only (with HTTPS):
```bash
cd backend
python run_https.py
```

### Both frontend and backend (with HTTPS):
```bash
npm run dev-https
```

## URLs

After setup, your application will be available at:
- **Frontend:** https://localhost:3000
- **Backend API:** https://localhost:8000
- **API Docs:** https://localhost:8000/docs

## Browser Security Warning

When you first visit the HTTPS URLs, your browser will show a security warning because we're using self-signed certificates. This is normal for local development.

**To proceed:**
1. Click "Advanced" or "Show Details"
2. Click "Proceed to localhost (unsafe)" or similar
3. The warning will disappear for future visits

## Troubleshooting

### "SSL certificates not found"
Run the setup command again:
```bash
npm run setup-https
```

### "OpenSSL not found"
Install OpenSSL:
- **Windows:** Download from https://slproweb.com/products/Win32OpenSSL.html
- **macOS:** `brew install openssl`
- **Linux:** `sudo apt-get install openssl`

### "Permission denied"
Make sure you have write permissions in the project directory.

## Production

For production deployment, you'll need:
1. A real SSL certificate from a certificate authority
2. A domain name
3. Proper server configuration

This setup is for **development only**. 