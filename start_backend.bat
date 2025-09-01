@echo off
echo Starting SlyWriter Backend API...
cd /d "C:\Typing Project"
echo.
echo Installing/checking dependencies...
pip install fastapi uvicorn python-multipart websockets
echo.
echo Starting server...
python -m uvicorn backend_api:app --host 127.0.0.1 --port 8000 --reload
pause