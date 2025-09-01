import os
import re

# Define the replacements
replacements = [
    # Typing API replacements
    (r"\`\$\{TYPING_API_URL\}/api/profiles\`", "API_ENDPOINTS.PROFILES_LIST"),
    (r"\`\$\{TYPING_API_URL\}/api/typing/start\`", "API_ENDPOINTS.TYPING_START"),
    (r"\`\$\{TYPING_API_URL\}/api/typing/stop\`", "API_ENDPOINTS.TYPING_STOP"),
    (r"\`\$\{TYPING_API_URL\}/api/typing/pause\`", "API_ENDPOINTS.TYPING_PAUSE"),
    (r"\`\$\{TYPING_API_URL\}/api/typing/resume\`", "API_ENDPOINTS.TYPING_RESUME"),
    (r"\`\$\{TYPING_API_URL\}/api/typing/status\`", "API_ENDPOINTS.TYPING_STATUS"),
    (r"\`\$\{TYPING_API_URL\}/api/typing/update_wpm\`", "API_ENDPOINTS.TYPING_UPDATE_WPM"),
    (r"\`\$\{TYPING_API_URL\}/api/profiles/generate-from-wpm\`", "API_ENDPOINTS.PROFILES_GENERATE_FROM_WPM"),
    (r"\`\$\{TYPING_API_URL\}/api/voice/transcribe\`", "API_ENDPOINTS.VOICE_TRANSCRIBE"),
    (r"\`\$\{TYPING_API_URL\}/api/wpm-test/calculate\`", "API_ENDPOINTS.WPM_TEST_CALCULATE"),
    
    # AI API replacements
    (r"\`\$\{API_URL\}/api/ai/generate\`", "API_ENDPOINTS.AI_GENERATE"),
    (r"\`\$\{API_URL\}/api/ai/humanize\`", "API_ENDPOINTS.AI_HUMANIZE"),
    (r"\`\$\{AI_API_URL\}/api/ai/generate\`", "API_ENDPOINTS.AI_GENERATE"),
    (r"\`\$\{AI_API_URL\}/api/ai/humanize\`", "API_ENDPOINTS.AI_HUMANIZE"),
    
    # WebSocket replacements
    (r"new WebSocket\(\`ws://localhost:8000/ws/\$\{userId\}\`\)", "new WebSocket(getWebSocketUrl(userId))"),
    (r"new WebSocket\('ws://localhost:8000/ws'\)", "new WebSocket(API_ENDPOINTS.WS_TYPING)"),
    
    # Variable declarations to remove
    (r"const TYPING_API_URL = 'http://localhost:8000'.*\n", ""),
    (r"const API_URL = 'http://localhost:8000'.*\n", ""),
    (r"const LOCAL_API_URL = 'http://localhost:5000'.*\n", ""),
]

# Components to update
components_dir = r"C:\Typing Project\slywriter-ui\app\components"
files_to_update = [
    "TypingTabWithWPM.tsx",
    "GlobalHotkeys.tsx", 
    "WPMTest.tsx",
    "TypingTab.tsx",
    "TypingTabEnhanced.tsx",
    "TypingTabComplete.tsx",
    "TypingTabFriendly.tsx",
    "TypingTabModern.tsx",
    "OverlayWindowEnhanced.tsx",
    "OverlayWindowOptimized.tsx",
    "LearningTab.tsx",
]

# Add import statement at the top of each file
import_statement = "import { API_ENDPOINTS, getWebSocketUrl, AI_API_URL, TYPING_API_URL, API_URL } from '../config/api'\n"

for filename in files_to_update:
    filepath = os.path.join(components_dir, filename)
    if os.path.exists(filepath):
        print(f"Updating {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if import already exists
        if "from '../config/api'" not in content:
            # Add import after the first import statement
            import_pos = content.find("import")
            if import_pos != -1:
                # Find the end of the first line starting with 'import'
                end_of_line = content.find('\n', import_pos)
                if end_of_line != -1:
                    content = content[:end_of_line+1] + import_statement + content[end_of_line+1:]
        
        # Apply replacements
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  [OK] Updated {filename}")
    else:
        print(f"  ✗ {filename} not found")

print("\nDone! All components updated to use centralized API configuration.")