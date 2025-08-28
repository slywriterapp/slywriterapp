import os
import re

# Define comprehensive replacements for proper theming
replacements = [
    # Fix standalone text-white without dark: prefix
    (r'(?<!")(?<!dark:)(?<!/)text-white(?![/"\w-])', 'dark:text-white text-gray-900'),
    
    # Fix bg-gray patterns without dark: prefix
    (r'(?<!")(?<!dark:)(?<!/)bg-gray-900/50(?!")', 'dark:bg-gray-900/50 bg-white'),
    (r'(?<!")(?<!dark:)(?<!/)bg-gray-900(?!/)', 'dark:bg-gray-900 bg-white'),
    (r'(?<!")(?<!dark:)(?<!/)bg-gray-800/50(?!")', 'dark:bg-gray-800/50 bg-gray-50'),
    (r'(?<!")(?<!dark:)(?<!/)bg-gray-800(?!/)', 'dark:bg-gray-800 bg-gray-100'),
    (r'(?<!")(?<!dark:)(?<!/)bg-gray-700(?!/)', 'dark:bg-gray-700 bg-gray-100'),
    
    # Fix border patterns
    (r'(?<!")(?<!dark:)border-gray-700(?!/)', 'dark:border-gray-700 border-gray-300'),
    (r'(?<!")(?<!dark:)border-gray-800(?!/)', 'dark:border-gray-800 border-gray-300'),
    (r'(?<!")(?<!dark:)border-gray-600(?!/)', 'dark:border-gray-600 border-gray-300'),
    
    # Fix text-gray patterns
    (r'(?<!")(?<!dark:)text-gray-400(?!")', 'dark:text-gray-400 text-gray-600'),
    (r'(?<!")(?<!dark:)text-gray-300(?!")', 'dark:text-gray-300 text-gray-700'),
    
    # Fix specific component issues
    (r'<kbd className="px-3 py-1 bg-gray-700 rounded text-sm text-white font-mono">', 
     '<kbd className="px-3 py-1 dark:bg-gray-700 bg-gray-200 rounded text-sm dark:text-white text-gray-900 font-mono">'),
]

def fix_file(file_path, specific_fixes=None):
    """Apply theme fixes to a specific file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Apply general replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Apply specific fixes if provided
    if specific_fixes:
        for old_str, new_str in specific_fixes:
            content = content.replace(old_str, new_str)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Fix GlobalHotkeys component - Hotkey settings dark mode issue
print("Fixing GlobalHotkeys component...")
hotkeys_fixes = [
    ('className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"',
     'className="dark:bg-gray-900/50 bg-white rounded-xl p-6 backdrop-blur-sm border dark:border-gray-700/50 border-gray-300"'),
    
    ('className="text-lg font-semibold text-white mb-6"',
     'className="text-lg font-semibold dark:text-white text-gray-900 mb-6"'),
    
    ('className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg"',
     'className="flex items-center justify-between p-3 dark:bg-gray-800/50 bg-gray-50 rounded-lg"'),
    
    ('className="text-sm font-medium text-white capitalize"',
     'className="text-sm font-medium dark:text-white text-gray-900 capitalize"'),
]

if fix_file('C:\\Typing Project\\slywriter-ui\\app\\components\\GlobalHotkeys.tsx', hotkeys_fixes):
    print("  ✓ Fixed GlobalHotkeys theming")

# Fix LearningTabEnhanced - Achievements and recommendations
print("Fixing LearningTabEnhanced component...")
learning_fixes = [
    # Fix achievement cards
    ('className="bg-gray-800/50 rounded-lg p-4"',
     'className="dark:bg-gray-800/50 bg-gray-50 rounded-lg p-4"'),
    
    # Fix recommended topics section
    ('className="bg-gray-900/50 rounded-xl p-6"',
     'className="dark:bg-gray-900/50 bg-white rounded-xl p-6"'),
     
    ('className="text-lg font-semibold text-white mb-4"',
     'className="text-lg font-semibold dark:text-white text-gray-900 mb-4"'),
     
    # Fix topic cards
    ('className="bg-gray-800 rounded-lg p-3"',
     'className="dark:bg-gray-800 bg-gray-100 rounded-lg p-3"'),
]

if fix_file('C:\\Typing Project\\slywriter-ui\\app\\components\\LearningTabEnhanced.tsx', learning_fixes):
    print("  ✓ Fixed LearningTabEnhanced theming")

# Fix HumanizerTab - Workflow boxes
print("Fixing HumanizerTab component...")
humanizer_fixes = [
    # Fix MagicFlow section
    ('className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-xl p-6"',
     'className="dark:bg-gradient-to-br dark:from-purple-900/20 dark:to-blue-900/20 bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6"'),
    
    # Fix workflow cards
    ('className="bg-gray-800/50 rounded-lg p-4"',
     'className="dark:bg-gray-800/50 bg-gray-50 rounded-lg p-4"'),
     
    ('className="text-white font-medium"',
     'className="dark:text-white text-gray-900 font-medium"'),
]

if fix_file('C:\\Typing Project\\slywriter-ui\\app\\components\\HumanizerTab.tsx', humanizer_fixes):
    print("  ✓ Fixed HumanizerTab theming")

# Fix StatisticsTab - Achievement cards
print("Fixing StatisticsTab component...")
stats_fixes = [
    # Fix achievement section
    ('className="grid grid-cols-3 gap-4">',
     'className="grid grid-cols-3 gap-4">'),
     
    ('className="bg-gray-800 rounded-lg p-4"',
     'className="dark:bg-gray-800 bg-gray-100 rounded-lg p-4"'),
]

if fix_file('C:\\Typing Project\\slywriter-ui\\app\\components\\StatisticsTab.tsx', stats_fixes):
    print("  ✓ Fixed StatisticsTab theming")

# Fix text fading issue - remove truncate classes that cut text
print("\nFixing text truncation issues...")
truncate_fixes = [
    # Don't truncate descriptions in navigation
    ('className="text-xs text-gray-500 mt-0.5 truncate"',
     'className="text-xs dark:text-gray-500 text-gray-600 mt-0.5"'),
     
    ('className="text-xs opacity-70 truncate"',
     'className="text-xs opacity-70"'),
]

if fix_file('C:\\Typing Project\\slywriter-ui\\app\\app\\page.tsx', truncate_fixes):
    print("  ✓ Fixed text truncation in navigation")
    
if fix_file('C:\\Typing Project\\slywriter-ui\\app\\components\\SettingsTabComplete.tsx', truncate_fixes):
    print("  ✓ Fixed text truncation in settings")

# Apply general fixes to all components
print("\nApplying comprehensive theme fixes to all components...")
components = [
    'app/components/AIHubTab.tsx',
    'app/components/StatisticsTab.tsx',
    'app/components/SettingsTabComplete.tsx',
    'app/components/LearningTabEnhanced.tsx',
    'app/components/HumanizerTab.tsx',
    'app/components/OverlayWindowEnhanced.tsx',
    'app/components/GlobalHotkeys.tsx',
]

for component in components:
    full_path = os.path.join('C:\\Typing Project\\slywriter-ui', component)
    if fix_file(full_path):
        print(f"  ✓ Updated {component}")

print("\nDeep theme fixes complete!")