@echo off
echo ===== SlyWriter Clean Reinstall =====
echo.
echo Step 1: Killing all SlyWriter processes...
echo Killing main SlyWriter.exe process...
taskkill /F /IM SlyWriter.exe 2>nul
echo Killing any remaining node/python processes...
taskkill /F /FI "WINDOWTITLE eq SlyWriter*" 2>nul
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr "PID"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%SlyWriter%%'" call terminate >nul 2>&1
)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%SlyWriter%%'" call terminate >nul 2>&1
)
echo All SlyWriter processes terminated
timeout /t 3 /nobreak >nul

echo.
echo Step 2: Running uninstaller...
if exist "%LOCALAPPDATA%\Programs\SlyWriter\Uninstall SlyWriter.exe" (
    start /wait "" "%LOCALAPPDATA%\Programs\SlyWriter\Uninstall SlyWriter.exe" /S
    echo Uninstaller completed
    timeout /t 3 /nobreak >nul
) else (
    echo No uninstaller found, will proceed to delete files
)

echo.
echo Step 3: Removing installation directory...
if exist "%LOCALAPPDATA%\Programs\SlyWriter" (
    rmdir /s /q "%LOCALAPPDATA%\Programs\SlyWriter" 2>nul
    if %errorlevel%==0 (
        echo Directory removed successfully
    ) else (
        echo Warning: Some files may still be in use
    )
) else (
    echo Directory already removed
)

echo.
echo Step 4: Installing v2.1.11...
if exist "dist\SlyWriter-Setup-2.1.11.exe" (
    start "" "dist\SlyWriter-Setup-2.1.11.exe"
    echo Installer launched
) else (
    echo ERROR: Installer not found at dist\SlyWriter-Setup-2.1.11.exe
    pause
    exit /b 1
)

echo.
echo ===== Clean reinstall initiated =====
echo Please complete the installation wizard.
pause
