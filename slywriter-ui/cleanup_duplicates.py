#!/usr/bin/env python3
"""
Clean up duplicate classes that were created by the dark mode script.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def clean_duplicate_classes(content: str) -> str:
    """Remove duplicate class names within className attributes"""
    
    def clean_classname(match):
        classname_content = match.group(1)
        
        # Split into individual classes
        classes = classname_content.split()
        
        # Remove exact duplicates while preserving order
        seen = set()
        unique_classes = []
        for cls in classes:
            if cls and cls not in seen:
                seen.add(cls)
                unique_classes.append(cls)
        
        return f'className="{" ".join(unique_classes)}"'
    
    # Find all className attributes
    content = re.sub(r'className="([^"]*)"', clean_classname, content)
    
    return content

def fix_specific_duplicates(content: str) -> str:
    """Fix specific duplicate patterns"""
    patterns = [
        # Remove duplicate text colors
        (r'text-white text-white', 'text-white'),
        (r'text-gray-400 text-gray-400', 'text-gray-400'),
        (r'text-gray-300 text-gray-300', 'text-gray-300'),
        (r'text-purple-400 text-purple-400', 'text-purple-400'),
        (r'text-purple-300 text-purple-300', 'text-purple-300'),
        
        # Remove duplicate backgrounds
        (r'bg-gray-900 bg-gray-900', 'bg-gray-900'),
        (r'bg-gray-800 bg-gray-800', 'bg-gray-800'),
        (r'bg-gray-700 bg-gray-700', 'bg-gray-700'),
        (r'bg-purple-500/10 bg-purple-500/10', 'bg-purple-500/10'),
        (r'bg-purple-500/20 bg-purple-500/20', 'bg-purple-500/20'),
        (r'bg-purple-500/30 bg-purple-500/30', 'bg-purple-500/30'),
        
        # Remove duplicate borders
        (r'border-gray-700 border-gray-700', 'border-gray-700'),
        (r'border-purple-500/20 border-purple-500/20', 'border-purple-500/20'),
        (r'border-purple-500/30 border-purple-500/30', 'border-purple-500/30'),
        
        # Fix conflicting backgrounds
        (r'bg-gray-900/50 bg-gray-900(?![\w/-])', 'bg-gray-900/50'),
        (r'bg-gray-800 bg-gray-900(?![\w/-])', 'bg-gray-800'),
        
        # Fix conflicting hover states
        (r'hover:bg-gray-600 hover:bg-gray-700', 'hover:bg-gray-700'),
        
        # Remove text-brand-purple references (should be text-purple-400)
        (r'text-brand-purple', 'text-purple-400'),
        (r'bg-brand-purple', 'bg-purple-500'),
        (r'border-brand-purple', 'border-purple-500'),
        
        # Fix placeholder duplicates
        (r'placeholder-gray-600 placeholder-gray-600', 'placeholder-gray-600'),
        (r'placeholder-gray-500 placeholder-gray-500', 'placeholder-gray-500'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def ensure_gradient_completeness(content: str) -> str:
    """Ensure gradient text is properly formatted"""
    # Fix gradients missing 'to' color
    content = re.sub(
        r'bg-gradient-to-r from-purple-400(?! to-)',
        'bg-gradient-to-r from-purple-400 to-pink-400',
        content
    )
    
    content = re.sub(
        r'bg-gradient-to-r from-purple-400(?! to-)',
        'bg-gradient-to-r from-purple-400 to-blue-400',
        content
    )
    
    return content

def process_file(filepath: Path) -> Tuple[bool, List[str]]:
    """Process a single file and return whether changes were made"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        changes = []
        
        # Apply all fixes
        new_content = clean_duplicate_classes(content)
        if new_content != content:
            changes.append("Cleaned duplicate classes")
            content = new_content
        
        new_content = fix_specific_duplicates(content)
        if new_content != content:
            changes.append("Fixed specific duplicates")
            content = new_content
        
        new_content = ensure_gradient_completeness(content)
        if new_content != content:
            changes.append("Fixed gradients")
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
    """Main function to process all files"""
    base_dir = Path(r"C:\Typing Project\slywriter-ui")
    
    print("Cleaning up duplicate classes...")
    print("-" * 40)
    
    total_fixed = 0
    
    # Process all .tsx files
    for filepath in base_dir.glob("app/**/*.tsx"):
        rel_path = filepath.relative_to(base_dir)
        changed, changes = process_file(filepath)
        if changed:
            total_fixed += 1
            print(f"[CLEANED] {rel_path}")
            for change in changes:
                print(f"   - {change}")
    
    print()
    print(f"Cleanup complete! Fixed {total_fixed} files.")

if __name__ == "__main__":
    main()