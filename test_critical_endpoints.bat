@echo off
echo Testing Critical SlyWriter API Endpoints
echo ==========================================
echo.

echo [1/4] Testing /api/health...
curl -s -w "\nHTTP Status: %%{http_code}\n" https://slywriterapp.onrender.com/api/health
echo.
echo.

echo [2/4] Testing /healthz...
curl -s -w "\nHTTP Status: %%{http_code}\n" https://slywriterapp.onrender.com/healthz
echo.
echo.

echo [3/4] Testing root /...
curl -s -w "\nHTTP Status: %%{http_code}\n" https://slywriterapp.onrender.com/
echo.
echo.

echo [4/4] Testing /api/license/verify with sample data...
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST https://slywriterapp.onrender.com/api/license/verify -H "Content-Type: application/json" -d "{\"license_key\":\"test_key\"}"
echo.
echo.

echo ==========================================
echo Test Complete!
