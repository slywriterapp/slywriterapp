@echo off
REM Release script for SlyWriter
REM Publishes to both private and public repositories

if "%1"=="" (
    echo Usage: release.bat VERSION
    echo Example: release.bat 2.1.9
    exit /b 1
)

set VERSION=%1
set NOTES_FILE=release-notes.txt

echo.
echo ========================================
echo Building SlyWriter v%VERSION%
echo ========================================
echo.

REM Build the installer
call npm run dist:nsis

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo.
echo ========================================
echo Creating GitHub Releases
echo ========================================
echo.

REM Create release in PUBLIC repository (for auto-updates)
echo Publishing to public releases repository...
gh release create v%VERSION% ^
    --repo slywriterapp/slywriter-releases ^
    --title "v%VERSION%" ^
    --notes-file "%NOTES_FILE%" ^
    "dist\SlyWriter-Setup-%VERSION%.exe" ^
    "dist\latest.yml"

if errorlevel 1 (
    echo Failed to publish to public repository!
    exit /b 1
)

REM Create release in PRIVATE repository (for tracking)
echo Publishing to private repository...
gh release create v%VERSION% ^
    --repo slywriterapp/slywriterapp ^
    --title "v%VERSION%" ^
    --notes-file "%NOTES_FILE%" ^
    "dist\SlyWriter-Setup-%VERSION%.exe" ^
    "dist\latest.yml"

if errorlevel 1 (
    echo Failed to publish to private repository!
    exit /b 1
)

echo.
echo ========================================
echo Release v%VERSION% published successfully!
echo ========================================
echo.
echo Public: https://github.com/slywriterapp/slywriter-releases/releases/tag/v%VERSION%
echo Private: https://github.com/slywriterapp/slywriterapp/releases/tag/v%VERSION%
echo.
