import os
import re

def find_all_white_text_issues(directory):
    """Find all instances of text-white without dark: prefix"""
    issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip node_modules and other non-source directories
        if 'node_modules' in root or '.next' in root:
            continue
            
        for file in files:
            if file.endswith('.tsx'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    for i, line in enumerate(lines, 1):
                        # Find text-white without dark: prefix
                        if 'text-white' in line and 'dark:text-white' not in line:
                            # Check if it's not already prefixed
                            pattern = r'(?<!dark:)text-white(?![/-])'
                            if re.search(pattern, line):
                                issues.append({
                                    'file': file_path.replace(directory + '\\', ''),
                                    'line': i,
                                    'content': line.strip()
                                })
                except Exception as e:
                    pass
    
    return issues

def find_all_bg_issues(directory):
    """Find all instances of bg-gray/white without dark: prefix"""
    issues = []
    
    patterns = [
        (r'(?<!dark:)bg-gray-900(?![/-])', 'bg-gray-900'),
        (r'(?<!dark:)bg-gray-800(?![/-])', 'bg-gray-800'),
        (r'(?<!dark:)bg-gray-700(?![/-])', 'bg-gray-700'),
        (r'(?<!dark:)bg-white(?![/-])', 'bg-white needs dark variant'),
    ]
    
    for root, dirs, files in os.walk(directory):
        if 'node_modules' in root or '.next' in root:
            continue
            
        for file in files:
            if file.endswith('.tsx'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    for i, line in enumerate(lines, 1):
                        for pattern, desc in patterns:
                            if re.search(pattern, line):
                                issues.append({
                                    'file': file_path.replace(directory + '\\', ''),
                                    'line': i,
                                    'issue': desc,
                                    'content': line.strip()[:100]
                                })
                except:
                    pass
    
    return issues

# Comprehensive replacement patterns
COMPREHENSIVE_FIXES = [
    # Text colors - MUST have dark: prefix
    (r'\btext-white\b(?![/-])', 'dark:text-white text-gray-900'),
    (r'(?<!dark:)text-gray-300\b', 'dark:text-gray-300 text-gray-700'),
    (r'(?<!dark:)text-gray-200\b', 'dark:text-gray-200 text-gray-800'),
    
    # Background colors - MUST have dark: prefix  
    (r'(?<!dark:)bg-gray-900(?![/-])', 'dark:bg-gray-900 bg-white'),
    (r'(?<!dark:)bg-gray-800(?![/-])', 'dark:bg-gray-800 bg-gray-50'),
    (r'(?<!dark:)bg-gray-700(?![/-])', 'dark:bg-gray-700 bg-gray-100'),
    (r'(?<!dark:)bg-gray-600(?![/-])', 'dark:bg-gray-600 bg-gray-100'),
    
    # Fix specific problematic patterns
    (r'className="([^"]*)\btext-white\b([^"]*)"', r'className="\1dark:text-white text-gray-900\2"'),
    (r'className="([^"]*)\bbg-gray-800\b([^"]*)"', r'className="\1dark:bg-gray-800 bg-gray-50\2"'),
]

def fix_file_comprehensively(file_path):
    """Apply ALL theme fixes to a file"""
    if not os.path.exists(file_path):
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Apply regex fixes
    for pattern, replacement in COMPREHENSIVE_FIXES:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            changes.append(f"Fixed: {pattern[:30]}...")
            content = new_content
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return []

def main():
    directory = 'C:\\Typing Project\\slywriter-ui'
    
    print("=" * 60)
    print("COMPREHENSIVE THEME FIX - DEEP DIVE ANALYSIS")
    print("=" * 60)
    
    # Find all issues first
    print("\n1. SCANNING FOR WHITE TEXT ISSUES...")
    white_text_issues = find_all_white_text_issues(os.path.join(directory, 'app'))
    
    if white_text_issues:
        print(f"\nFound {len(white_text_issues)} white text issues:")
        for issue in white_text_issues[:10]:  # Show first 10
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['content'][:80]}...")
    
    print("\n2. SCANNING FOR BACKGROUND COLOR ISSUES...")
    bg_issues = find_all_bg_issues(os.path.join(directory, 'app'))
    
    if bg_issues:
        print(f"\nFound {len(bg_issues)} background issues:")
        for issue in bg_issues[:10]:
            print(f"  {issue['file']}:{issue['line']} - {issue['issue']}")
    
    # Now fix all components
    print("\n3. APPLYING COMPREHENSIVE FIXES...")
    
    components_to_fix = [
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
        'app/components/FirstTimeHelper.tsx',
    ]
    
    for component in components_to_fix:
        file_path = os.path.join(directory, component)
        changes = fix_file_comprehensively(file_path)
        if changes:
            print(f"\n  Fixed {component}:")
            for change in changes[:3]:
                print(f"    - {change}")
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE FIX COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    main()