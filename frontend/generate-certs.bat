@echo off
echo Generating SSL certificates for Express HTTPS server...

:: Check if OpenSSL is available
where openssl >nul 2>nul
if %errorlevel% neq 0 (
    echo OpenSSL not found in PATH.
    echo Please install OpenSSL or use the alternative method in the guide.
    pause
    exit /b 1
)

:: Generate private key
echo Generating private key...
openssl genrsa -out localhost-key.pem 2048

:: Generate certificate
echo Generating certificate...
openssl req -new -x509 -key localhost-key.pem -out localhost.pem -days 365 -subj "/C=US/ST=State/L=City/O=Development/OU=IT/CN=localhost"

echo.
echo ✅ SSL certificates generated successfully!
echo Files created:
echo   - localhost-key.pem (private key)
echo   - localhost.pem (certificate)
echo.
echo You can now run:
echo   npm run start-server (HTTPS with build)
echo   npm run start-server-http (HTTP with build)
echo.
pause 