@echo off
echo ========================================
echo Testing SlyWriter Backend Endpoints
echo ========================================
echo.

set BASE_URL=https://slywriterapp.onrender.com

echo [1/11] Testing Root Endpoint...
curl -s %BASE_URL%/ | findstr "ok"
echo.

echo [2/11] Testing Health Check /healthz...
curl -s %BASE_URL%/healthz | findstr "healthy"
echo.

echo [3/11] Testing Health Check /api/health...
curl -s %BASE_URL%/api/health | findstr "healthy"
echo.

echo [4/11] Testing Auth Status /api/auth/status...
curl -s %BASE_URL%/api/auth/status
echo.

echo [5/11] Testing Config /api/config...
curl -s %BASE_URL%/api/config
echo.

echo [6/11] Testing Global Stats /api/stats/global...
curl -s %BASE_URL%/api/stats/global
echo.

echo [7/11] Testing Google Login /auth/google/login (expect 400 - no credential)...
curl -s -X POST %BASE_URL%/auth/google/login -H "Content-Type: application/json" -d "{}"
echo.

echo [8/11] Testing Desktop Google Auth /api/auth/google...
curl -s -X POST %BASE_URL%/api/auth/google
echo.

echo [9/11] Testing Register /api/auth/register (expect 400 - no email)...
curl -s -X POST %BASE_URL%/api/auth/register -H "Content-Type: application/json" -d "{}"
echo.

echo [10/11] Testing Login /api/auth/login (expect 400 - no email)...
curl -s -X POST %BASE_URL%/api/auth/login -H "Content-Type: application/json" -d "{}"
echo.

echo [11/11] Testing Profile /auth/profile (expect 401 - no token)...
curl -s %BASE_URL%/auth/profile
echo.

echo.
echo ========================================
echo Test Complete
echo ========================================
