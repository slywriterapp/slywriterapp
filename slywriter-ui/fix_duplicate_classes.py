import os
import re

def clean_duplicate_classes(content):
    """Remove duplicate class names and fix multiple dark: prefixes"""
    
    # Fix patterns like "dark:dark:dark:text-white" -> "dark:text-white"
    content = re.sub(r'(dark:)+', 'dark:', content)
    
    # Fix patterns like "text-gray-900 text-gray-900 text-gray-900" -> "text-gray-900"
    # This regex finds repeated class names
    def remove_duplicates(match):
        classname = match.group(0)
        # Split by spaces and remove duplicates while preserving order
        classes = classname.split()
        seen = set()
        unique_classes = []
        for cls in classes:
            if cls not in seen:
                seen.add(cls)
                unique_classes.append(cls)
        return ' '.join(unique_classes)
    
    # Match className attributes
    content = re.sub(
        r'className="([^"]+)"',
        lambda m: 'className="' + remove_duplicates(re.match(r'^.*$', m.group(1))) + '"',
        content
    )
    
    # Fix specific problematic patterns
    replacements = [
        # Fix text colors - ensure proper theming
        (r'\btext-white\b(?![\w/-])', 'dark:text-white text-gray-900'),
        
        # Fix backgrounds that are missing dark variants
        (r'(?<!dark:)bg-gray-900(?![/-])', 'dark:bg-gray-900 bg-white'),
        (r'(?<!dark:)bg-gray-800/50(?![/-])', 'dark:bg-gray-800/50 bg-gray-50'),
        (r'(?<!dark:)bg-gray-800(?![/-])', 'dark:bg-gray-800 bg-gray-50'),  
        (r'(?<!dark:)bg-gray-700(?![/-])', 'dark:bg-gray-700 bg-gray-100'),
        (r'(?<!dark:)bg-gray-600(?![/-])', 'dark:bg-gray-600 bg-gray-100'),
        
        # Fix hover states
        (r'hover:dark:bg-gray-600 bg-gray-100', 'dark:hover:bg-gray-600 hover:bg-gray-200'),
        (r'hover:dark:text-white text-gray-900', 'dark:hover:text-white hover:text-gray-900'),
        
        # Fix disabled states
        (r'disabled:bg-gray-600', 'disabled:dark:bg-gray-600 disabled:bg-gray-300'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_file(file_path):
    """Fix a single file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    content = clean_duplicate_classes(content)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    directory = 'C:\\Typing Project\\slywriter-ui'
    
    print("=" * 60)
    print("FIXING DUPLICATE CLASSES AND THEME ISSUES")
    print("=" * 60)
    
    components = [
        'app/app/page.tsx',
        'app/components/TypingTabWithWPM.tsx',
        'app/components/HumanizerTab.tsx',
        'app/components/AIHubTab.tsx',
        'app/components/StatisticsTab.tsx',
        'app/components/SettingsTabComplete.tsx',
        'app/components/LearningTabEnhanced.tsx',
        'app/components/OverlayWindowEnhanced.tsx',
        'app/components/GlobalHotkeys.tsx',
        'app/components/GoogleLogin.tsx',
        'app/components/OnboardingFlow.tsx',
    ]
    
    fixed_count = 0
    for component in components:
        file_path = os.path.join(directory, component)
        if fix_file(file_path):
            print(f"  Fixed: {component}")
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    print("=" * 60)

if __name__ == '__main__':
    main()