#!/usr/bin/env python3
"""
Test script to verify NON TLE tenants list.ods reading functionality
"""

import os
import sys
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from utilities.tag_manager import TagManager

def test_non_tle_reading():
    """Test reading NON TLE tenants list.ods file"""
    tag_manager = TagManager()
    
    # Test file path
    non_tle_path = "docs/NON TLE tenants list.ods"
    
    if not os.path.exists(non_tle_path):
        print(f"❌ File not found: {non_tle_path}")
        return False
    
    print(f"📁 Testing file: {non_tle_path}")
    
    try:
        # Read non-TLE business data
        non_tle_data = tag_manager.read_non_tle_businesses_from_ods(non_tle_path)
        
        if not non_tle_data:
            print("❌ No data returned from NON TLE file")
            return False
        
        print(f"✅ Successfully loaded {len(non_tle_data)} categories:")
        
        for category_name, category_color, businesses in non_tle_data:
            print(f"\n  📂 Category: {category_name} (Color: {category_color})")
            print(f"     Businesses: {len(businesses)}")
            
            # Show first few businesses as examples
            for i, (tenant_name, street_name, property_name, category, trading_as, business_color, business_type) in enumerate(businesses[:3]):
                print(f"     {i+1}. {tenant_name}")
                print(f"        Street: {street_name}")
                print(f"        Address: {property_name}")
                print(f"        Category: {category}")
                print(f"        Trading As: {trading_as}")
                print(f"        Type: {business_type}")
            
            if len(businesses) > 3:
                print(f"     ... and {len(businesses) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading NON TLE file: {e}")
        return False

if __name__ == "__main__":
    # Create QApplication
    app = QApplication(sys.argv)
    
    print("NON TLE Tenants List Test")
    print("=" * 40)
    
    success = test_non_tle_reading()
    
    if success:
        print(f"\n✅ Test completed successfully!")
    else:
        print(f"\n❌ Test failed!")
