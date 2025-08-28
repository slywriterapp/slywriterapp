import os
import re

def fix_file_content(file_path, replacements_list):
    """Apply specific replacements to a file"""
    if not os.path.exists(file_path):
        print(f"  - File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    for old_str, new_str in replacements_list:
        content = content.replace(old_str, new_str)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

print("Fixing remaining theme issues...")

# Fix GlobalHotkeys button colors
print("\nFixing GlobalHotkeys buttons...")
hotkey_fixes = [
    ('className="px-3 py-1 bg-purple-500 hover:bg-purple-600',
     'className="px-3 py-1 dark:bg-purple-500 dark:hover:bg-purple-600 bg-brand-purple hover:bg-brand-purple-dark'),
     
    ('className="px-4 py-2 bg-purple-500 hover:bg-purple-600',
     'className="px-4 py-2 dark:bg-purple-500 dark:hover:bg-purple-600 bg-brand-purple hover:bg-brand-purple-dark'),
     
    ('className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">',
     'className="mt-4 p-3 dark:bg-yellow-500/10 bg-yellow-50 rounded-lg border dark:border-yellow-500/30 border-yellow-400">'),
     
    ('className="text-xs text-yellow-300">',
     'className="text-xs dark:text-yellow-300 text-yellow-700">'),
     
    ('className="text-xs text-gray-400">',
     'className="text-xs dark:text-gray-400 text-gray-600">'),
     
    ('hover:bg-gray-600',
     'dark:hover:bg-gray-600 hover:bg-gray-200'),
]

if fix_file_content('C:\\Typing Project\\slywriter-ui\\app\\components\\GlobalHotkeys.tsx', hotkey_fixes):
    print("  + Fixed GlobalHotkeys button theming")

# Fix LearningTabEnhanced achievements and recommendations
print("\nFixing LearningTabEnhanced...")
learning_fixes = [
    # Fix achievement cards
    ('className="bg-gray-800/50 rounded-lg p-4 flex items-center gap-3">',
     'className="dark:bg-gray-800/50 bg-gray-50 rounded-lg p-4 flex items-center gap-3">'),
     
    ('className="text-sm font-medium text-white">',
     'className="text-sm font-medium dark:text-white text-gray-900">'),
     
    # Fix recommended topics
    ('className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-xl p-6">',
     'className="dark:bg-gradient-to-br dark:from-purple-900/20 dark:to-blue-900/20 bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6">'),
     
    ('className="text-lg font-semibold text-white mb-4">Recommended Learning Topics',
     'className="text-lg font-semibold dark:text-white text-gray-900 mb-4">Recommended Learning Topics'),
     
    ('className="bg-gray-800 rounded-lg p-3 hover:bg-gray-700',
     'className="dark:bg-gray-800 bg-gray-100 rounded-lg p-3 dark:hover:bg-gray-700 hover:bg-gray-50'),
]

if fix_file_content('C:\\Typing Project\\slywriter-ui\\app\\components\\LearningTabEnhanced.tsx', learning_fixes):
    print("  + Fixed LearningTabEnhanced achievements")

# Fix HumanizerTab MagicFlow and workflow sections
print("\nFixing HumanizerTab workflow sections...")
humanizer_fixes = [
    # MagicFlow section
    ('className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-xl p-6 backdrop-blur-sm border border-purple-500/20">',
     'className="dark:bg-gradient-to-br dark:from-purple-900/20 dark:to-blue-900/20 bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 backdrop-blur-sm border dark:border-purple-500/20 border-brand-purple/20">'),
     
    ('className="text-lg font-semibold text-white mb-4 flex items-center gap-2">',
     'className="text-lg font-semibold dark:text-white text-gray-900 mb-4 flex items-center gap-2">'),
     
    # Workflow boxes
    ('className="bg-gray-800/50 rounded-lg p-4">',
     'className="dark:bg-gray-800/50 bg-gray-50 rounded-lg p-4">'),
     
    ('className="text-white font-medium flex items-center gap-2">',
     'className="dark:text-white text-gray-900 font-medium flex items-center gap-2">'),
     
    ('className="text-sm text-gray-300">',
     'className="text-sm dark:text-gray-300 text-gray-700">'),
     
    # SlyWriter Workflow section  
    ('className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-xl p-6">',
     'className="dark:bg-gradient-to-r dark:from-purple-900/20 dark:to-blue-900/20 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6">'),
]

if fix_file_content('C:\\Typing Project\\slywriter-ui\\app\\components\\HumanizerTab.tsx', humanizer_fixes):
    print("  + Fixed HumanizerTab workflow boxes")

# Fix StatisticsTab achievements
print("\nFixing StatisticsTab achievements...")
stats_fixes = [
    ('className="bg-gray-800 rounded-lg p-4 text-center">',
     'className="dark:bg-gray-800 bg-gray-100 rounded-lg p-4 text-center">'),
     
    ('className="text-2xl font-bold text-white">',
     'className="text-2xl font-bold dark:text-white text-gray-900">'),
]

if fix_file_content('C:\\Typing Project\\slywriter-ui\\app\\components\\StatisticsTab.tsx', stats_fixes):
    print("  + Fixed StatisticsTab achievements")

# Fix text truncation in sidebar navigation
print("\nFixing text truncation issues...")
page_fixes = [
    # Remove truncation from descriptions
    ('className="text-xs dark:text-gray-500 text-gray-600 mt-0.5 truncate">',
     'className="text-xs dark:text-gray-500 text-gray-600 mt-0.5">'),
]

if fix_file_content('C:\\Typing Project\\slywriter-ui\\app\\app\\page.tsx', page_fixes):
    print("  + Fixed sidebar text truncation")

# Fix settings tab description truncation
settings_fixes = [
    ('className="text-xs opacity-70 truncate">',
     'className="text-xs opacity-70">'),
]

if fix_file_content('C:\\Typing Project\\slywriter-ui\\app\\components\\SettingsTabComplete.tsx', settings_fixes):
    print("  + Fixed settings text truncation")

print("\nAll deep theme issues fixed!")