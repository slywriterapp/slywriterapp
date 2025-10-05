# PowerShell script to replace hardcoded URLs with environment variable
# Replaces 'https://slywriterapp.onrender.com' with ${RENDER_API_URL}

$files = @(
    "slywriter-ui\app\components\AIHubTab.tsx",
    "slywriter-ui\app\components\EnhancedLearningTab.tsx",
    "slywriter-ui\app\components\ErrorBoundary.tsx",
    "slywriter-ui\app\components\GoogleLoginEnhanced.tsx",
    "slywriter-ui\app\components\HotkeysTabEnhanced.tsx",
    "slywriter-ui\app\components\HumanizerTab.tsx",
    "slywriter-ui\app\components\HumanizerTabSimple.tsx",
    "slywriter-ui\app\components\LearningHub.tsx",
    "slywriter-ui\app\components\LearningTabEnhanced.tsx",
    "slywriter-ui\app\components\UserDashboard.tsx"
)

foreach ($file in $files) {
    $fullPath = Join-Path "C:\Typing Project" $file

    if (Test-Path $fullPath) {
        Write-Host "Processing: $file"

        # Read file content
        $content = Get-Content $fullPath -Raw

        # Check if import already exists
        if ($content -notmatch "import.*RENDER_API_URL.*from.*config/api") {
            Write-Host "  -> Adding import statement"
            # Add import after other imports
            $content = $content -replace "(import.*from 'lucide-react')", "`$1`nimport { RENDER_API_URL } from '../config/api'"
            $content = $content -replace "(import.*from 'framer-motion')", "`$1`nimport { RENDER_API_URL } from '../config/api'"
            if ($content -notmatch "import.*RENDER_API_URL") {
                # If no lucide or framer-motion, add after first import
                $content = $content -replace "(import.*\n)", "`$1import { RENDER_API_URL } from '../config/api'`n"
            }
        }

        # Replace hardcoded URL with template literal
        $oldPattern = "'https://slywriterapp\.onrender\.com"
        $newPattern = "`${RENDER_API_URL}"
        $content = $content -replace $oldPattern, $newPattern

        # Also handle double quotes
        $oldPattern2 = '"https://slywriterapp\.onrender\.com'
        $content = $content -replace $oldPattern2, $newPattern

        # Write back
        Set-Content $fullPath -Value $content -NoNewline

        Write-Host "  -> URL replaced with env variable"
    } else {
        Write-Host "File not found: $fullPath" -ForegroundColor Yellow
    }
}

Write-Host "`nDone! All hardcoded URLs replaced." -ForegroundColor Green
