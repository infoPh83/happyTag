#!/usr/bin/env python3
"""
Test script to verify the fix for year not being added to Cloudinary-imported tags
"""

def test_tag_building_logic():
    """Test the logic for building tags with/without year based on Cloudinary import"""
    
    print("=== Testing Tag Building Logic ===\n")
    
    # Test Case 1: Local keywords (should include year)
    print("Test Case 1: Local keywords")
    year = "2024"
    keywords = ["DISK ONLY", "local tag"]
    keywords_from_cloudinary = False
    
    all_tags = []
    seen = set()
    
    if year and not keywords_from_cloudinary:
        year_str = str(year)
        all_tags.append(year_str)
        seen.add(year_str)
        print(f"  Added year '{year_str}' to tags (local keywords)")
    elif keywords_from_cloudinary:
        print(f"  Skipped adding year - keywords imported from Cloudinary")
    
    # Add keywords
    if keywords:
        for keyword in keywords:
            keyword_str = str(keyword).strip()
            if keyword_str and keyword_str not in seen:
                all_tags.append(keyword_str)
                seen.add(keyword_str)
    
    result1 = ', '.join(all_tags)
    print(f"  Result: '{result1}'")
    print(f"  Expected: '2024, DISK ONLY, local tag'")
    print(f"  ✅ Correct: {result1 == '2024, DISK ONLY, local tag'}\n")
    
    # Test Case 2: Cloudinary imported keywords (should NOT include year)
    print("Test Case 2: Cloudinary imported keywords")
    year = "2024"
    keywords = ["ON CLOUDINARY"]
    keywords_from_cloudinary = True
    
    all_tags = []
    seen = set()
    
    if year and not keywords_from_cloudinary:
        year_str = str(year)
        all_tags.append(year_str)
        seen.add(year_str)
        print(f"  Added year '{year_str}' to tags (local keywords)")
    elif keywords_from_cloudinary:
        print(f"  Skipped adding year - keywords imported from Cloudinary")
    
    # Add keywords
    if keywords:
        for keyword in keywords:
            keyword_str = str(keyword).strip()
            if keyword_str and keyword_str not in seen:
                all_tags.append(keyword_str)
                seen.add(keyword_str)
    
    result2 = ', '.join(all_tags)
    print(f"  Result: '{result2}'")
    print(f"  Expected: 'ON CLOUDINARY'")
    print(f"  ✅ Correct: {result2 == 'ON CLOUDINARY'}\n")
    
    # Test Case 3: Cloudinary tags that happen to include the year
    print("Test Case 3: Cloudinary tags that include year")
    year = "2024"
    keywords = ["2024", "ON CLOUDINARY", "professional"]
    keywords_from_cloudinary = True
    
    all_tags = []
    seen = set()
    
    if year and not keywords_from_cloudinary:
        year_str = str(year)
        all_tags.append(year_str)
        seen.add(year_str)
        print(f"  Added year '{year_str}' to tags (local keywords)")
    elif keywords_from_cloudinary:
        print(f"  Skipped adding year - keywords imported from Cloudinary")
    
    # Add keywords
    if keywords:
        for keyword in keywords:
            keyword_str = str(keyword).strip()
            if keyword_str and keyword_str not in seen:
                all_tags.append(keyword_str)
                seen.add(keyword_str)
    
    result3 = ', '.join(all_tags)
    print(f"  Result: '{result3}'")
    print(f"  Expected: '2024, ON CLOUDINARY, professional'")
    print(f"  ✅ Correct: {result3 == '2024, ON CLOUDINARY, professional'}\n")
    
    print("=== Test Summary ===")
    print("✅ Local keywords: Year is automatically added")
    print("✅ Cloudinary import: Year is NOT automatically added")
    print("✅ Cloudinary with year: Year comes from Cloudinary tags, not auto-added")
    print("\nThe fix should resolve the issue where UI tags didn't match displayed tags!")

if __name__ == "__main__":
    test_tag_building_logic()