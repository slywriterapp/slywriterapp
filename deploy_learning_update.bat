@echo off
echo ========================================
echo SLYWRITER LEARNING MODE DEPLOYMENT
echo ========================================
echo.
echo This will deploy the learning mode endpoints to Render
echo.
echo Step 1: Checking git status...
git status

echo.
echo Step 2: Adding modified files...
git add slywriter_server.py

echo.
echo Step 3: Committing changes...
git commit -m "Add learning mode endpoints - save and retrieve AI lessons"

echo.
echo Step 4: Pushing to GitHub (Render will auto-deploy)...
git push origin main

echo.
echo ========================================
echo DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Render will automatically deploy these changes.
echo The server will be available in about 2-3 minutes.
echo.
echo Learning mode features:
echo - /api/learning/create-lesson - Saves AI lessons
echo - /api/learning/get-lessons - Retrieves saved lessons
echo.
pause