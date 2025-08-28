#!/usr/bin/env python3
"""
Fix remaining theme issues in the SlyWriter UI.
Focuses on:
1. Removing duplicate bg-gray-50/50 patterns
2. Ensuring proper text color contrast
3. Fixing Typing Automation Engine box theming
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def fix_duplicate_backgrounds(content: str) -> str:
    """Remove duplicate background classes like 'bg-gray-50/50 bg-gray-50'"""
    # Fix patterns like "bg-gray-50/50 bg-gray-50"
    content = re.sub(r'bg-gray-50/50\s+bg-gray-50', 'bg-gray-50', content)
    
    # Fix patterns like "bg-gray-100/50 bg-gray-100"
    content = re.sub(r'bg-gray-100/50\s+bg-gray-100', 'bg-gray-100', content)
    
    return content

def ensure_proper_text_colors(content: str) -> str:
    """Ensure text has proper dark/light mode colors"""
    patterns = [
        # Fix text-white without dark: prefix (should be dark:text-white text-gray-900)
        (r'(?<!dark:)text-white(?![\w-])', 'dark:text-white text-gray-900'),
        
        # Fix text-black without proper light mode alternative
        (r'(?<!:)text-black(?![\w-])', 'dark:text-white text-black'),
        
        # Ensure proper heading colors
        (r'text-2xl font-bold(?!.*text-)', 'text-2xl font-bold dark:text-white text-gray-900'),
        (r'text-xl font-bold(?!.*text-)', 'text-xl font-bold dark:text-white text-gray-900'),
        (r'text-lg font-semibold(?!.*text-)', 'text-lg font-semibold dark:text-white text-gray-900'),
        
        # Fix standalone text-gray-900 that should have dark mode variant
        (r'(?<!dark:text-white )text-gray-900(?!.*dark:text-)', 'dark:text-white text-gray-900'),
    ]
    
    for pattern, replacement in patterns:
        # Only replace if not already properly formatted
        if 'dark:text-' not in pattern:
            content = re.sub(pattern, replacement, content)
    
    return content

def fix_typing_automation_box(content: str) -> str:
    """Specifically fix the Typing Automation Engine box theming"""
    # Fix the main container background
    content = re.sub(
        r'<div className="dark:bg-gradient-to-r dark:from-purple-900/20 dark:to-blue-900/20 bg-gray-50',
        '<div className="dark:bg-gradient-to-r dark:from-purple-900/20 dark:to-blue-900/20 bg-white',
        content
    )
    
    # Ensure the title has proper colors
    content = re.sub(
        r'Typing Automation Engine\s*</h2>',
        'Typing Automation Engine</h2>',
        content
    )
    
    # Fix WPM display box
    content = re.sub(
        r'dark:bg-gray-900/50 bg-gray-50 rounded-lg px-4 py-2',
        'dark:bg-gray-900/50 bg-white rounded-lg px-4 py-2',
        content
    )
    
    return content

def fix_input_backgrounds(content: str) -> str:
    """Fix input and textarea backgrounds for proper theme switching"""
    patterns = [
        # Fix textareas with gray backgrounds
        (r'dark:bg-gray-800 bg-gray-50/50 bg-gray-50', 'dark:bg-gray-800 bg-white'),
        (r'dark:bg-gray-800 bg-gray-50', 'dark:bg-gray-800 bg-white'),
        
        # Fix input fields
        (r'dark:bg-gray-900/50 bg-gray-50', 'dark:bg-gray-900/50 bg-white'),
        
        # Fix card backgrounds
        (r'dark:bg-gray-900/50 bg-white rounded-xl', 'dark:bg-gray-900/50 bg-white rounded-xl'),
        (r'dark:bg-gray-900/50 bg-white rounded-2xl', 'dark:bg-gray-900/50 bg-white rounded-2xl'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_button_colors(content: str) -> str:
    """Ensure buttons have proper theme colors"""
    patterns = [
        # Fix purple buttons
        (r'bg-purple-500 hover:bg-purple-600 text-white',
         'dark:bg-purple-500 dark:hover:bg-purple-600 bg-brand-purple hover:bg-brand-purple-dark text-white'),
        
        # Fix gradient buttons
        (r'bg-gradient-to-r from-purple-500 to-blue-500 text-white',
         'dark:bg-gradient-to-r dark:from-purple-500 dark:to-blue-500 bg-brand-purple text-white'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def process_file(filepath: Path) -> Tuple[bool, List[str]]:
    """Process a single file and return whether changes were made and what changed"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        changes = []
        
        # Apply all fixes
        new_content = fix_duplicate_backgrounds(content)
        if new_content != content:
            changes.append("Fixed duplicate backgrounds")
            content = new_content
        
        new_content = ensure_proper_text_colors(content)
        if new_content != content:
            changes.append("Fixed text colors")
            content = new_content
        
        new_content = fix_typing_automation_box(content)
        if new_content != content:
            changes.append("Fixed Typing Automation box")
            content = new_content
        
        new_content = fix_input_backgrounds(content)
        if new_content != content:
            changes.append("Fixed input backgrounds")
            content = new_content
        
        new_content = fix_button_colors(content)
        if new_content != content:
            changes.append("Fixed button colors")
            content = new_content
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, []

def main():
    """Main function to process all component files"""
    base_dir = Path(r"C:\Typing Project\slywriter-ui")
    
    # Focus on components with reported issues
    priority_files = [
        "app/components/TypingTabWithWPM.tsx",
        "app/components/AIHubTab.tsx",
        "app/components/HumanizerTab.tsx",
        "app/components/StatisticsTab.tsx",
        "app/components/LearningTabEnhanced.tsx",
        "app/components/SettingsTabComplete.tsx",
        "app/app/page.tsx",
    ]
    
    print("Fixing remaining theme issues...\n")
    
    total_fixed = 0
    
    for rel_path in priority_files:
        filepath = base_dir / rel_path
        if filepath.exists():
            changed, changes = process_file(filepath)
            if changed:
                total_fixed += 1
                print(f"[FIXED] {rel_path}")
                for change in changes:
                    print(f"   - {change}")
            else:
                print(f"[OK] {rel_path} (no changes needed)")
    
    # Also process any other .tsx files
    print("\nChecking other components...")
    
    for filepath in base_dir.glob("app/components/*.tsx"):
        rel_path = filepath.relative_to(base_dir)
        if str(rel_path) not in [f"app/components/{p.split('/')[-1]}" for p in priority_files]:
            changed, changes = process_file(filepath)
            if changed:
                total_fixed += 1
                print(f"[FIXED] {rel_path}")
                for change in changes:
                    print(f"   - {change}")
    
    print(f"\nTheme fix complete! Fixed {total_fixed} files.")
    print("\nKey improvements:")
    print("- Removed duplicate background classes")
    print("- Fixed white-on-white text issues")
    print("- Improved Typing Automation Engine theming")
    print("- Ensured proper dark/light mode switching")

if __name__ == "__main__":
    main()