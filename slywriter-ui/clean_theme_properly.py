import os
import re

def clean_classname(classname_content):
    """Clean duplicate classes from a className string"""
    # Remove multiple dark: prefixes
    classname_content = re.sub(r'(dark:)+', 'dark:', classname_content)
    
    # Split into individual classes
    classes = classname_content.split()
    
    # Remove duplicates while preserving order
    seen = set()
    unique_classes = []
    for cls in classes:
        # Clean each class
        cls = cls.strip()
        if cls and cls not in seen:
            seen.add(cls)
            unique_classes.append(cls)
    
    return ' '.join(unique_classes)

def fix_component(file_path):
    """Fix all theme issues in a component"""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Step 1: Clean all className attributes
    def clean_classnames(match):
        return f'className="{clean_classname(match.group(1))}"'
    
    content = re.sub(r'className="([^"]*)"', clean_classnames, content)
    
    # Step 2: Fix specific patterns that need proper theming
    fixes = [
        # Fix typing automation engine box
        ('dark:bg-gray-900/50 bg-gray-100', 'dark:bg-gray-900/50 bg-gray-50'),
        
        # Fix text that needs dark mode
        (r'\btext-white\b(?![/\w-])', 'dark:text-white text-gray-900'),
        
        # Fix backgrounds missing light mode
        ('bg-gray-800/50(?![/\w])', 'dark:bg-gray-800/50 bg-gray-50'),
        ('bg-gray-800(?![/\w])', 'dark:bg-gray-800 bg-gray-50'),
        ('bg-gray-700(?![/\w])', 'dark:bg-gray-700 bg-gray-100'),
        ('bg-gray-600(?![/\w])', 'dark:bg-gray-600 bg-gray-100'),
        
        # Fix hover states
        ('hover:bg-gray-600 bg-gray-100', 'dark:hover:bg-gray-600 hover:bg-gray-200'),
        
        # Fix disabled states  
        ('disabled:bg-gray-600', 'disabled:dark:bg-gray-600 disabled:bg-gray-300'),
    ]
    
    for pattern, replacement in fixes:
        if pattern.startswith('r'):
            # It's a regex
            content = re.sub(pattern[1:], replacement, content)
        else:
            # It's a literal string
            content = content.replace(pattern, replacement)
    
    # Step 3: Final cleanup - ensure no standalone white text
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Check if line has text-white without dark: prefix
        if 'text-white' in line and 'dark:text-white' not in line:
            # Add dark: prefix and light mode color
            line = re.sub(r'\btext-white\b', 'dark:text-white text-gray-900', line)
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    base_dir = 'C:\\Typing Project\\slywriter-ui'
    
    print("CLEANING THEME ISSUES PROPERLY")
    print("-" * 40)
    
    components = [
        'app/app/page.tsx',
        'app/components/TypingTabWithWPM.tsx',
        'app/components/SettingsTabComplete.tsx',
        'app/components/LearningTabEnhanced.tsx',
        'app/components/GlobalHotkeys.tsx',
        'app/components/GoogleLogin.tsx',
        'app/components/OverlayWindowEnhanced.tsx',
        'app/components/HumanizerTab.tsx',
        'app/components/AIHubTab.tsx',
        'app/components/StatisticsTab.tsx',
    ]
    
    for component in components:
        path = os.path.join(base_dir, component)
        if fix_component(path):
            print(f"Fixed: {component}")
        else:
            print(f"No changes: {component}")
    
    print("-" * 40)
    print("Cleanup complete!")

if __name__ == '__main__':
    main()