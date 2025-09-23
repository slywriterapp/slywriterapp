@echo off
echo Testing Update Server...

echo.
echo 1. Testing health check:
curl https://slywriter-update-server.onrender.com/health

echo.
echo 2. Testing latest version:
curl https://slywriter-update-server.onrender.com/updates/latest

echo.
echo 3. Testing RELEASES file (Squirrel endpoint):
curl https://slywriter-update-server.onrender.com/updates/RELEASES

echo.
echo Done! If you see data above, the proxy is working!