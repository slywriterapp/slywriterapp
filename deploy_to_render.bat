@echo off
echo ========================================
echo SLYWRITER RENDER DEPLOYMENT SCRIPT
echo ========================================
echo.
echo This script will deploy telemetry updates to your Render server
echo.
echo Step 1: Backing up current server file...
copy slywriter_server.py slywriter_server_backup.py

echo Step 2: Replacing with updated server file...
copy /Y slywriter_server_updated.py slywriter_server.py

echo Step 3: Staging changes for Git...
git add slywriter_server.py requirements.txt

echo Step 4: Committing changes...
git commit -m "Add cloud telemetry system for beta testing"

echo Step 5: Pushing to GitHub (Render will auto-deploy)...
git push origin main

echo.
echo ========================================
echo DEPLOYMENT INITIATED!
echo ========================================
echo.
echo Render will automatically deploy these changes.
echo Check your Render dashboard for deployment status.
echo.
echo After deployment completes (usually 2-3 minutes), test with:
echo curl https://slywriterapp.onrender.com/api/admin/telemetry/health
echo.
pause