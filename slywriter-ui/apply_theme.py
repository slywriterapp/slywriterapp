import os
import re

# Define replacement patterns
replacements = [
    (r'bg-gray-900/50', 'dark:bg-gray-900/50 bg-white'),
    (r'bg-gray-900(?!/)', 'dark:bg-gray-900 bg-white'),
    (r'bg-gray-800/50', 'dark:bg-gray-800/50 bg-gray-50'),
    (r'bg-gray-800(?!/)', 'dark:bg-gray-800 bg-gray-100'),
    (r'(?<!dark:)text-white(?!/)', 'dark:text-white text-gray-900'),
    (r'(?<!dark:)text-gray-400', 'dark:text-gray-400 text-gray-600'),
    (r'(?<!dark:)text-gray-500', 'dark:text-gray-500 text-gray-600'),
    (r'(?<!dark:)text-gray-300', 'dark:text-gray-300 text-gray-700'),
    (r'border-gray-700', 'dark:border-gray-700 border-gray-300'),
    (r'border-gray-800', 'dark:border-gray-800 border-brand-purple/20'),
    (r'bg-purple-500/20', 'dark:bg-purple-500/20 bg-brand-purple/10'),
    (r'bg-purple-500/10', 'dark:bg-purple-500/10 bg-brand-purple/10'),
    (r'bg-purple-500(?!/)', 'dark:bg-purple-500 bg-brand-purple'),
    (r'hover:bg-purple-600', 'dark:hover:bg-purple-600 hover:bg-brand-purple-dark'),
    (r'text-purple-400', 'dark:text-purple-400 text-brand-purple'),
    (r'text-purple-300', 'dark:text-purple-300 text-brand-purple'),
    (r'border-purple-500/20', 'dark:border-purple-500/20 border-brand-purple/20'),
    (r'border-purple-500/30', 'dark:border-purple-500/30 border-brand-purple/30'),
    (r'placeholder-gray-500', 'dark:placeholder-gray-500 placeholder-gray-400'),
    (r'bg-gradient-to-r from-purple', 'dark:bg-gradient-to-r dark:from-purple'),
    (r' to-blue', ' dark:to-blue'),
    (r' to-purple', ' dark:to-purple'),
]

# Files to update
files = [
    'app/components/HumanizerTab.tsx',
    'app/components/AIHubTab.tsx',
    'app/components/StatisticsTab.tsx',
    'app/components/SettingsTabComplete.tsx',
    'app/components/LearningTabEnhanced.tsx',
]

for file_path in files:
    full_path = os.path.join('C:\\Typing Project\\slywriter-ui', file_path)
    if not os.path.exists(full_path):
        print(f"Skipping {file_path} - file not found")
        continue
    
    print(f"Processing {file_path}...")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Apply replacements
    for pattern, replacement in replacements:
        # Skip if replacement already exists (avoid double application)
        if replacement in content and pattern not in ['bg-gradient-to-r from-purple', ' to-blue', ' to-purple']:
            continue
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Updated {file_path}")
    else:
        print(f"  No changes needed for {file_path}")

print("\nTheme update complete!")