#!/usr/bin/env python3
"""
Test script to verify search/filter functionality
"""

import os
import sys
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from tag_manager import TagManager

def test_search_functionality():
    """Test the search functionality with typing and deleting"""
    # Create QApplication
    app = QApplication(sys.argv)
    
    tag_manager = TagManager()
    
    # Load business data
    b2b_path = "docs/B2B + B2C final.ods"
    if not os.path.exists(b2b_path):
        print(f"❌ File not found: {b2b_path}")
        return False
    
    print(f"📁 Loading business data from: {b2b_path}")
    tag_manager.load_businesses_from_file(b2b_path)
    
    # Check initial state
    initial_count = len(tag_manager.original_business_data) if hasattr(tag_manager, 'original_business_data') else 0
    print(f"✅ Initial data loaded: {initial_count} categories")
    
    # Test 1: Search for "coffee" (should filter down)
    print("\n🔍 Test 1: Searching for 'coffee'")
    tag_manager.businessInput.setPlainText("coffee")
    tag_manager.filter_businesses()
    
    # Test 2: Change search to "cof" (should show more results)
    print("\n🔍 Test 2: Changing search to 'cof' (should expand results)")
    tag_manager.businessInput.setPlainText("cof")
    tag_manager.filter_businesses()
    
    # Test 3: Clear search (should show all results)
    print("\n🔍 Test 3: Clearing search (should show all results)")
    tag_manager.businessInput.setPlainText("")
    tag_manager.filter_businesses()
    
    # Test 4: Search for "street" then reduce to "str"
    print("\n🔍 Test 4: Search for 'street' then reduce to 'str'")
    tag_manager.businessInput.setPlainText("street")
    tag_manager.filter_businesses()
    
    print("\n🔍 Test 4b: Reducing search to 'str' (should expand results)")
    tag_manager.businessInput.setPlainText("str")
    tag_manager.filter_businesses()
    
    print("\n✅ Search functionality test completed")
    return True

if __name__ == "__main__":
    print("Search Functionality Test")
    print("=" * 40)
    
    success = test_search_functionality()
    
    if success:
        print(f"\n✅ Test completed!")
    else:
        print(f"\n❌ Test failed!")
