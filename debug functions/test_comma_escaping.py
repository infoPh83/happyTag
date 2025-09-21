#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Cloudinary comma escaping functionality.

Demonstrates the fix for the issue where tags containing commas 
(like "Guaranty Trust Bank (UK) Ltd") get split by Cloudinary.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.tag_utils import escape_tags_for_cloudinary, unescape_tags_from_cloudinary

def test_comma_escaping():
    """Test comma escaping and unescaping functionality"""
    
    print("=== Cloudinary Comma Escaping Test ===\n")
    
    # Test cases with problematic tags
    test_tags = [
        "Guaranty Trust Bank (UK) Ltd",
        "Smith, John & Associates", 
        "Regular tag without commas",
        "Another, problematic, tag",
        "Simple tag",
        "Company, Inc., LLC"
    ]
    
    print("Original tags:")
    for i, tag in enumerate(test_tags, 1):
        print(f"  {i}. '{tag}'")
    
    print("\nEscaped tags (what gets sent to Cloudinary):")
    escaped_tags = escape_tags_for_cloudinary(test_tags)
    for i, tag in enumerate(escaped_tags, 1):
        print(f"  {i}. '{tag}'")
    
    print("\nUnescaped tags (what gets read back from Cloudinary):")
    unescaped_tags = unescape_tags_from_cloudinary(escaped_tags)
    for i, tag in enumerate(unescaped_tags, 1):
        print(f"  {i}. '{tag}'")
    
    print("\n=== Verification ===")
    if test_tags == unescaped_tags:
        print("SUCCESS: Original tags match unescaped tags!")
        print("   The escaping/unescaping process is working correctly.")
    else:
        print("FAILED: Tags don't match!")
        print(f"   Original: {test_tags}")
        print(f"   Final:    {unescaped_tags}")
    
    print("\n=== Character Analysis ===")
    for i, (original, escaped) in enumerate(zip(test_tags, escaped_tags), 1):
        if original != escaped:
            print(f"Tag {i}: '{original}' -> '{escaped}'")
            print(f"   Regular comma (U+002C): {original.count(',')}")
            print(f"   Fullwidth comma (U+FF0C): {escaped.count('\uff0c')}")
        else:
            print(f"Tag {i}: No escaping needed for '{original}'")

    print("\n=== Integration Notes ===")
    print("• This fix prevents Cloudinary from splitting tags on commas")
    print("• Regular commas (,) are replaced with fullwidth commas")
    print("• Fullwidth commas look nearly identical but don't trigger Cloudinary's splitting")
    print("• Tags are unescaped when read back from Cloudinary for display/editing")

if __name__ == "__main__":
    test_comma_escaping()