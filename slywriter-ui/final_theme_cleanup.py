#!/usr/bin/env python3
"""
Final cleanup for remaining theme issues.
Focuses on:
1. Removing duplicate dark: prefixes
2. Removing duplicate text-gray-900 patterns
3. Fixing bg-gray-100 duplicates
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def clean_duplicate_dark_prefixes(content: str) -> str:
    """Remove duplicate dark: prefixes like dark:dark:text-white"""
    # Fix multiple dark: prefixes
    content = re.sub(r'(dark:)+', 'dark:', content)
    return content

def clean_duplicate_classes(content: str) -> str:
    """Remove duplicate classes in className attributes"""
    # Find all className attributes
    pattern = r'className="([^"]*)"'
    
    def clean_classname(match):
        classname_content = match.group(1)
        
        # Split into individual classes
        classes = classname_content.split()
        
        # Remove duplicates while preserving order
        seen = set()
        unique_classes = []
        for cls in classes:
            if cls and cls not in seen:
                seen.add(cls)
                unique_classes.append(cls)
        
        return f'className="{" ".join(unique_classes)}"'
    
    content = re.sub(pattern, clean_classname, content)
    return content

def fix_text_color_patterns(content: str) -> str:
    """Fix specific text color patterns"""
    patterns = [
        # Fix dark:dark:text-white text-gray-900 text-gray-900
        (r'dark:dark:text-white text-gray-900 text-gray-900', 'dark:text-white text-gray-900'),
        
        # Fix hover:dark:dark:text-white text-gray-900 text-gray-900
        (r'hover:dark:dark:text-white text-gray-900 text-gray-900', 'hover:dark:text-white hover:text-gray-900'),
        
        # Fix hover:dark:bg-gray-600 bg-gray-100
        (r'hover:dark:bg-gray-600 bg-gray-100', 'dark:hover:bg-gray-600 hover:bg-gray-200'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def process_file(filepath: Path) -> Tuple[bool, List[str]]:
    """Process a single file and return whether changes were made"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        changes = []
        
        # Apply all fixes
        new_content = clean_duplicate_dark_prefixes(content)
        if new_content != content:
            changes.append("Cleaned duplicate dark: prefixes")
            content = new_content
        
        new_content = clean_duplicate_classes(content)
        if new_content != content:
            changes.append("Cleaned duplicate classes")
            content = new_content
        
        new_content = fix_text_color_patterns(content)
        if new_content != content:
            changes.append("Fixed text color patterns")
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
    
    print("Final theme cleanup...\n")
    
    total_fixed = 0
    
    # Process all .tsx files
    for filepath in base_dir.glob("app/**/*.tsx"):
        rel_path = filepath.relative_to(base_dir)
        changed, changes = process_file(filepath)
        if changed:
            total_fixed += 1
            print(f"[FIXED] {rel_path}")
            for change in changes:
                print(f"   - {change}")
    
    print(f"\nFinal cleanup complete! Fixed {total_fixed} files.")

if __name__ == "__main__":
    main()