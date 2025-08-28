@echo off
REM SlyWriter Backend Deployment Script for Windows

echo ================================
echo SlyWriter Backend Deployment
echo ================================

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo [OK] Python is installed

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Run startup checks
echo Running startup checks...
python startup.py
if %errorlevel% neq 0 (
    echo Startup checks failed!
    exit /b 1
)

REM Create Windows service (requires admin rights)
if "%1"=="--service" (
    echo Creating Windows service...
    echo This requires administrator privileges
    nssm install SlyWriterBackend "%cd%\venv\Scripts\python.exe" "%cd%\main_complete.py"
    nssm set SlyWriterBackend AppDirectory "%cd%"
    nssm set SlyWriterBackend DisplayName "SlyWriter Backend API"
    nssm set SlyWriterBackend Description "SlyWriter typing automation backend service"
    echo [OK] Service created. Use 'nssm start SlyWriterBackend' to start
    goto :end
)

REM Start the application
if "%1"=="--start" (
    echo Starting SlyWriter Backend...
    start /B python main_complete.py > slywriter.log 2>&1
    echo [OK] Backend started in background
    goto :end
)

echo.
echo Deployment complete! To start the backend:
echo   deploy.bat --start    (Run in background)
echo   deploy.bat --service  (Create Windows service - requires NSSM)
echo   python main_complete.py (Run in foreground)

:end