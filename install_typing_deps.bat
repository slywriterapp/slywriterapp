@echo off
echo ========================================
echo Installing SlyWriter Typing Dependencies
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please download and install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Install required packages
pip install fastapi uvicorn python-multipart keyboard pyautogui openai python-dotenv

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies.
    echo Try running this script as Administrator.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Dependencies installed successfully!
echo Typing features should now work.
echo ========================================
pause