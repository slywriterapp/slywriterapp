@echo off
echo Starting Authentication Server with SMTP...

:: Set SMTP environment variables
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USERNAME=support@slywriter.ai
set SMTP_PASSWORD=icvvvhygzkccpuzg

:: Kill any existing processes on port 5000
for /f "tokens=5" %%i in ('netstat -ano 2^>nul ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%i 2>nul >nul
)

echo SMTP Configuration:
echo   Server: %SMTP_SERVER%
echo   Port: %SMTP_PORT%
echo   Username: %SMTP_USERNAME%
echo   Password: [CONFIGURED]
echo.

:: Start the Flask server
python slywriter_server.py