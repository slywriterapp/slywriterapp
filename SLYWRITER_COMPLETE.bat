@echo off
title SlyWriter Complete - Full Stack Application
color 0A

echo ============================================
echo      SlyWriter Complete - Starting All Services
echo ============================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Kill ALL old instances
echo [1/6] Cleaning up previous instances...
taskkill /F /IM electron.exe 2>nul >nul
taskkill /F /IM node.exe 2>nul >nul
taskkill /F /IM python.exe 2>nul >nul

:: Kill processes on all ports
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%i 2>nul >nul
)
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%i 2>nul >nul
)
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%i 2>nul >nul
)
timeout /t 2 /nobreak >nul

:: Start Authentication Server with SMTP
echo [2/6] Starting Authentication Server (with email)...
echo.
echo SMTP Configuration:
echo   - Email sending: ENABLED
echo   - From: support@slywriter.ai
echo   - Verification links: Webflow branded page
echo.
start /B cmd /c python run_auth_server.py
timeout /t 3 /nobreak >nul

:: Start Backend API for typing
echo [3/6] Starting Typing Backend API...
start /B cmd /c python backend_api.py
timeout /t 2 /nobreak >nul

:: Start typing engine
echo [4/6] Starting Typing Engine...
start /B cmd /c python typing_engine.py
timeout /t 1 /nobreak >nul

:: Start Next.js development server
echo [5/6] Starting Web Interface...
cd slywriter-ui
start /B cmd /c npm run dev
cd ..
echo     Waiting for web interface to initialize...
timeout /t 8 /nobreak >nul

:: Start Electron app
echo [6/6] Launching SlyWriter Desktop App...
cd slywriter-electron
start "" npm run dev
cd ..

echo.
echo ============================================
echo     SlyWriter is now running!
echo ============================================
echo.
echo Services running:
echo   - Auth Server: http://localhost:5000 (with SMTP)
echo   - Backend API: http://localhost:8000
echo   - Web UI: http://localhost:3000
echo   - Desktop App: Launching...
echo.
echo Authentication features:
echo   - Email registration with verification
echo   - Duplicate email detection
echo   - Google Sign-In (requires Google Cloud setup)
echo.
echo Note: For Google Sign-In to work locally:
echo   1. Go to https://console.cloud.google.com/
echo   2. Add http://localhost:3000 to authorized origins
echo.
echo Press any key to exit and stop all services...
pause >nul

:: Cleanup on exit
echo.
echo Stopping all services...
taskkill /F /IM electron.exe 2>nul >nul
taskkill /F /IM node.exe 2>nul >nul
taskkill /F /IM python.exe 2>nul >nul
echo All services stopped.
exit