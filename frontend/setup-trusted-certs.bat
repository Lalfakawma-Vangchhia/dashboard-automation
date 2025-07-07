@echo off
echo Setting up TRUSTED SSL certificates for Express HTTPS server...
echo.

:: Check if mkcert is installed
where mkcert >nul 2>nul
if %errorlevel% neq 0 (
    echo mkcert not found. Installing mkcert...
    
    :: Check if Chocolatey is installed
    where choco >nul 2>nul
    if %errorlevel% neq 0 (
        echo Installing Chocolatey first...
        echo Please run as Administrator if needed...
        powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    )
    
    :: Install mkcert
    echo Installing mkcert via Chocolatey...
    choco install mkcert -y
    
    :: Refresh environment variables
    echo Refreshing environment...
    call refreshenv
) else (
    echo mkcert is already installed.
)

echo.
echo Installing local Certificate Authority...
mkcert -install

echo.
echo Generating TRUSTED certificates for localhost...
mkcert localhost 127.0.0.1 ::1

echo.
echo Renaming certificates for Express server...
if exist localhost+2.pem (
    copy localhost+2.pem localhost.pem
    copy localhost+2-key.pem localhost-key.pem
    del localhost+2.pem
    del localhost+2-key.pem
)

echo.
echo ✅ TRUSTED SSL certificates generated successfully!
echo Files created:
echo   - localhost-key.pem (private key)
echo   - localhost.pem (certificate)
echo.
echo These certificates are now TRUSTED by your browser!
echo You can now run:
echo   npm run start-server
echo.
echo Your site will show as 🔒 SECURE in the browser!
pause 