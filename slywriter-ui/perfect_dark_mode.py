#!/usr/bin/env python3
"""
Perfect dark mode implementation for SlyWriter UI.
This script:
1. Removes light mode styling
2. Fixes gradient text issues
3. Ensures consistent dark backgrounds
4. Removes text truncation
5. Perfects all dark mode theming
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def remove_light_mode_classes(content: str) -> str:
    """Remove light mode specific classes and keep only dark mode"""
    patterns = [
        # Remove light mode conditionals
        (r'theme === \'light\' \? \'[^\']*\' : ', ''),
        (r' \? \'[^\']*\' : \'([^\']*)\' # assuming second is dark', r"'\1'"),
        
        # Remove non-dark prefixed colors for backgrounds
        (r'(?<!dark:)bg-white(?![\w-])', 'bg-gray-900'),
        (r'(?<!dark:)bg-gray-50(?![\w-])', 'bg-gray-900/50'),
        (r'(?<!dark:)bg-gray-100(?![\w-])', 'bg-gray-800'),
        (r'(?<!dark:)bg-brand-purple/10(?![\w-])', 'bg-purple-500/10'),
        (r'(?<!dark:)bg-brand-purple/20(?![\w-])', 'bg-purple-500/20'),
        
        # Remove non-dark text colors
        (r'(?<!dark:)text-gray-900(?![\w-])', 'text-white'),
        (r'(?<!dark:)text-gray-600(?![\w-])', 'text-gray-400'),
        (r'(?<!dark:)text-gray-700(?![\w-])', 'text-gray-300'),
        (r'(?<!dark:)text-brand-purple(?![\w-])', 'text-purple-400'),
        
        # Remove dark: prefixes since we're dark only
        (r'dark:', ''),
        
        # Fix borders
        (r'(?<!:)border-gray-300(?![\w-])', 'border-gray-700'),
        (r'(?<!:)border-brand-purple/20(?![\w-])', 'border-purple-500/20'),
        (r'(?<!:)border-brand-purple/30(?![\w-])', 'border-purple-500/30'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_gradient_text_issues(content: str) -> str:
    """Fix gradient text that's cutting off"""
    # Fix incomplete gradient definitions
    patterns = [
        # Fix gradients missing 'from' or 'to'
        (r'bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent',
         'bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent'),
        
        # Fix gradients missing proper dark mode
        (r'bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent',
         'bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent'),
         
        # Fix partial gradients
        (r'bg-gradient-to-r from-(\w+)-(\d+) bg-clip-text',
         r'bg-gradient-to-r from-\1-\2 to-\1-300 bg-clip-text'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Remove truncate classes that cut off text
    content = re.sub(r'\s*truncate(?![\w-])', '', content)
    content = re.sub(r'\s*line-clamp-\d+', '', content)
    
    return content

def fix_typing_automation_box(content: str) -> str:
    """Specifically fix the Typing Automation Engine box"""
    # Fix the main container
    content = re.sub(
        r'className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 bg-white',
        'className="bg-gradient-to-r from-purple-900/20 to-blue-900/20',
        content
    )
    
    # Fix the WPM display box
    content = re.sub(
        r'bg-gray-900/50 bg-white rounded-lg',
        'bg-gray-900/50 rounded-lg',
        content
    )
    
    # Fix text colors in the box
    content = re.sub(
        r'text-xl font-bold text-white text-gray-900 text-brand-purple',
        'text-xl font-bold text-white',
        content
    )
    
    return content

def enforce_dark_backgrounds(content: str) -> str:
    """Ensure all backgrounds are properly dark themed"""
    patterns = [
        # Main containers
        ('bg-white rounded-xl', 'bg-gray-900/50 rounded-xl'),
        ('bg-white rounded-2xl', 'bg-gray-900/50 rounded-2xl'),
        ('bg-white rounded-lg', 'bg-gray-800 rounded-lg'),
        
        # Input fields
        ('bg-gray-50 rounded-lg', 'bg-gray-800 rounded-lg'),
        ('bg-gray-50/50', 'bg-gray-800/50'),
        
        # Cards and panels
        ('bg-gray-100', 'bg-gray-800'),
        ('bg-gray-50', 'bg-gray-900/50'),
        
        # Hover states
        ('hover:bg-gray-200', 'hover:bg-gray-700'),
        ('hover:bg-gray-100', 'hover:bg-gray-800'),
        ('hover:bg-brand-purple/5', 'hover:bg-purple-500/10'),
        ('hover:bg-brand-purple/20', 'hover:bg-purple-500/30'),
    ]
    
    for pattern, replacement in patterns:
        content = content.replace(pattern, replacement)
    
    return content

def ensure_text_visibility(content: str) -> str:
    """Ensure all text is visible in dark mode"""
    patterns = [
        # Headers
        ('text-gray-900 font-bold', 'text-white font-bold'),
        ('text-gray-900 font-semibold', 'text-white font-semibold'),
        
        # Regular text
        ('text-gray-700', 'text-gray-300'),
        ('text-gray-600', 'text-gray-400'),
        ('text-gray-500', 'text-gray-400'),
        
        # Links and accents
        ('text-brand-purple', 'text-purple-400'),
        ('text-brand-purple-dark', 'text-purple-300'),
        
        # Placeholders
        ('placeholder-gray-400', 'placeholder-gray-500'),
        ('placeholder-gray-500', 'placeholder-gray-600'),
    ]
    
    for pattern, replacement in patterns:
        content = content.replace(pattern, replacement)
    
    return content

def fix_theme_context(content: str) -> str:
    """Force dark mode in theme context"""
    if 'ThemeContext' in content:
        # Default to dark mode
        content = re.sub(
            r"useState<'light' \| 'dark'>\('dark'\)",
            "useState<'dark'>('dark')",
            content
        )
        
        # Remove theme toggle functionality
        content = re.sub(
            r"setTheme\(prev => prev === 'light' \? 'dark' : 'light'\)",
            "// Theme toggle disabled - dark mode only",
            content
        )
        
        # Force dark mode
        content = re.sub(
            r"const savedTheme = localStorage\.getItem\('slywriter-theme'\).*",
            "const savedTheme = 'dark' // Force dark mode",
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
        new_content = remove_light_mode_classes(content)
        if new_content != content:
            changes.append("Removed light mode classes")
            content = new_content
        
        new_content = fix_gradient_text_issues(content)
        if new_content != content:
            changes.append("Fixed gradient text issues")
            content = new_content
        
        new_content = fix_typing_automation_box(content)
        if new_content != content:
            changes.append("Fixed Typing Automation box")
            content = new_content
        
        new_content = enforce_dark_backgrounds(content)
        if new_content != content:
            changes.append("Enforced dark backgrounds")
            content = new_content
        
        new_content = ensure_text_visibility(content)
        if new_content != content:
            changes.append("Ensured text visibility")
            content = new_content
        
        new_content = fix_theme_context(content)
        if new_content != content:
            changes.append("Fixed theme context")
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
    
    print("=" * 60)
    print("PERFECTING DARK MODE THEMING")
    print("=" * 60)
    print()
    
    # Priority files to fix
    priority_files = [
        "app/components/TypingTabWithWPM.tsx",
        "app/components/AIHubTab.tsx",
        "app/components/HumanizerTab.tsx",
        "app/components/StatisticsTab.tsx",
        "app/components/LearningTabEnhanced.tsx",
        "app/components/SettingsTabComplete.tsx",
        "app/app/page.tsx",
        "app/context/ThemeContext.tsx",
        "app/components/ThemeToggle.tsx",
    ]
    
    total_fixed = 0
    
    print("Processing priority components...")
    print("-" * 40)
    
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
                print(f"[OK] {rel_path}")
    
    print()
    print("Processing all other components...")
    print("-" * 40)
    
    # Process all other .tsx files
    for filepath in base_dir.glob("app/**/*.tsx"):
        rel_path = filepath.relative_to(base_dir)
        if str(rel_path) not in [f"{p}" for p in priority_files]:
            changed, changes = process_file(filepath)
            if changed:
                total_fixed += 1
                print(f"[FIXED] {rel_path}")
                for change in changes:
                    print(f"   - {change}")
    
    print()
    print("=" * 60)
    print(f"DARK MODE PERFECTION COMPLETE!")
    print(f"Fixed {total_fixed} files")
    print()
    print("Improvements made:")
    print("- Removed all light mode styling")
    print("- Fixed gradient text cutoff issues")
    print("- Fixed Typing Automation Engine box")
    print("- Enforced consistent dark backgrounds")
    print("- Ensured all text is visible")
    print("- Removed text truncation")
    print("=" * 60)

if __name__ == "__main__":
    main()