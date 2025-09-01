@echo off
title SlyWriter - Professional Typing Automation
color 0D

echo ============================================
echo            SlyWriter v2.0.0 Pro
echo            Professional Typing Automation
echo ============================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Kill only old Electron/SlyWriter instances
echo [1/5] Cleaning up previous SlyWriter instances...
taskkill /F /IM electron.exe 2>nul >nul

:: Kill processes on specific ports only
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%i 2>nul >nul
)
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%i 2>nul >nul
)
timeout /t 1 /nobreak >nul

:: Start Python backend
echo [2/5] Starting backend server...
start /B cmd /c "python backend_api.py"
timeout /t 2 /nobreak >nul

:: Start typing engine
echo [3/5] Starting typing engine...
start /B cmd /c "python typing_engine.py"
timeout /t 1 /nobreak >nul

:: Start Next.js development server
echo [4/5] Starting web interface...
cd slywriter-ui
start /B cmd /c "npm run dev"
cd ..
echo     Waiting for web interface to initialize...
timeout /t 8 /nobreak >nul

:: Start Electron app in dev mode
echo [5/5] Launching SlyWriter desktop app...
cd slywriter-electron
start "" npm run dev

echo.
echo ============================================
echo    SlyWriter is running!
echo.
echo    Global Hotkeys:
echo    - Ctrl+Alt+S : Start typing
echo    - Ctrl+Alt+Q : Emergency stop
echo    - Ctrl+Alt+P : Pause/Resume
echo    - Ctrl+Alt+G : AI Generation
echo    - Ctrl+Alt+O : Toggle overlay
echo.
echo    To stop: Close this window
echo    If high CPU: Close Node.js in Task Manager
echo ============================================
echo.
pause >nul

:: Simple cleanup when closing
echo.
echo Shutting down SlyWriter...
taskkill /F /IM electron.exe 2>nul >nul

:: Kill processes on our ports
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :8000') do (
    taskkill /F /PID %%i 2>nul >nul
)
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :3000') do (
    taskkill /F /PID %%i 2>nul >nul
)

echo Done!
timeout /t 2 /nobreak >nul
exit