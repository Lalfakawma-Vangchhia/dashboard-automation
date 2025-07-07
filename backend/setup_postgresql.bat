@echo off
echo ========================================
echo PostgreSQL Setup for Automation Dashboard
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Checking if virtual environment exists...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Running PostgreSQL setup...
python scripts\setup_postgresql.py
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL setup failed
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo PostgreSQL setup completed!
echo You can test the connection manually by running:
echo   python scripts\setup_postgresql.py

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Start the application: python run.py
echo 2. Open http://localhost:8000/docs in your browser
echo 3. Use pgAdmin to manage your database
echo.
pause 