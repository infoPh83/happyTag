#!/usr/bin/env python3

"""
Test script to verify business functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from business_widgets import BusinessButton

def test_business_button():
    """Test the BusinessButton functionality"""
    print("Testing BusinessButton functionality...")
    
    # Create a test business button
    business_button = BusinessButton(
        tenant_name="Workpad Fitzrovia Ltd",
        street_name="Margaret Street", 
        property_name="5 Margaret Street",
        category="Lifestyle",
        trading_as="Workpad Co-working",
        background_color="#F8F8F0"
    )
    
    # Test the description methods
    full_description = business_button.get_full_description()
    search_text = business_button.get_search_text()
    
    print(f"Full description: {full_description}")
    print(f"Search text: {search_text}")
    
    # Test expected output
    expected_desc = "Workpad Fitzrovia Ltd 5 Margaret Street Margaret Street Lifestyle TLE Tenant"
    assert full_description == expected_desc, f"Expected: {expected_desc}, Got: {full_description}"
    
    # Test search functionality
    assert "workpad" in search_text
    assert "fitzrovia" in search_text
    assert "margaret" in search_text
    assert "lifestyle" in search_text
    assert "tle tenant" in search_text
    
    print("✅ BusinessButton functionality test passed!")

if __name__ == "__main__":
    test_business_button()
    print("All tests completed successfully!")
