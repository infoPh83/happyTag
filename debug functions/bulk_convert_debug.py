#!/usr/bin/env python3
"""
Bulk convert remaining debug prints in main.py to new debug system.
This script handles the patterns automatically to speed up conversion.
"""

import re

def convert_debug_prints(file_path):
    """Convert debug prints to new debug system calls"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Cloudinary related prints
    cloudinary_patterns = [
        (r'print\(\s*f?\"\[DEBUG\]\s*(.+?(?:cloudinary|Cloudinary|CLOUDINARY).+?)\"\s*\)', r'debug_cloudinary(f"\1")'),
        (r'print\(\s*f?\"\[DEBUG\]\s*(✅.+?)\"\s*\)', r'debug_cloudinary(f"\1")'),
        (r'print\(\s*f?\"\[DEBUG\]\s*(❌.+?)\"\s*\)', r'debug_cloudinary(f"\1")'),
        (r'print\(\s*f?\"\[DEBUG\]\s*(📊.+?)\"\s*\)', r'debug_cloudinary(f"\1")'),
        (r'print\(\s*f?\"\[DEBUG\]\s*(⚠️.+?)\"\s*\)', r'debug_cloudinary(f"\1")'),
    ]
    
    # Pattern 2: UI events and tag operations
    ui_patterns = [
        (r'print\(\s*f?\"\[DEBUG\]\s*(.+?(?:clicked|append|tag|Tag|business|Business|building|Building|street|Street).+?)\"\s*\)', r'debug_tags(f"\1")'),
        (r'print\(\s*f?\"\[DEBUG\]\s*(.+?(?:Before|After|current_text|new_text).+?)\"\s*\)', r'debug_tags(f"\1")'),
    ]
    
    # Pattern 3: Assessment and processing
    assessment_patterns = [
        (r'print\(\s*f?\"\[DEBUG\]\s*(.+?(?:assessment|Assessment|processing|synced|status|cache).+?)\"\s*\)', r'debug_assessment(f"\1")'),
    ]
    
    # Pattern 4: Error patterns
    error_patterns = [
        (r'print\(\s*f?\"\[DEBUG\]\s*(.+?Error.+?)\"\s*\)', r'debug_errors(f"\1")'),
    ]
    
    # Pattern 5: Generic UI updates
    ui_generic_patterns = [
        (r'print\(\s*f?\"\[DEBUG\]\s*(.+?(?:update|Update|UI|status|credits).+?)\"\s*\)', r'debug_cloudinary(f"\1")'),
    ]
    
    # Pattern 6: File operations and general processing
    file_patterns = [
        (r'print\(\s*f?\"\[DEBUG\]\s*(.+?(?:file|File|complete|Complete|finished|Finished).+?)\"\s*\)', r'debug_file_ops(f"\1")'),
    ]
    
    # Apply patterns in order of specificity (most specific first)
    all_patterns = cloudinary_patterns + ui_patterns + assessment_patterns + error_patterns + ui_generic_patterns + file_patterns
    
    changes_made = 0
    for pattern, replacement in all_patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            changes_made += count
            print(f"Applied pattern: {pattern[:50]}... -> {count} changes")
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Converted {changes_made} debug prints in {file_path}")
        return changes_made
    else:
        print(f"❌ No changes made to {file_path}")
        return 0

if __name__ == "__main__":
    changes = convert_debug_prints("main.py")
    print(f"\nTotal changes: {changes}")