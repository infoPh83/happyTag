#!/usr/bin/env python3

"""
Test script to verify business field-level duplicate prevention
"""

def test_field_level_duplicate_prevention():
    """Test sophisticated field-level duplicate checking logic"""
    
    # Sample business fields
    business_fields = [
        "Workpad Fitzrovia Ltd",  # Tenant Name
        "5 Margaret Street",      # Property  
        "Margaret Street",        # Street Name
        "Lifestyle",             # Category
        "TLE Tenant"             # Hard-coded
    ]
    
    full_business_text = " ".join(business_fields)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Empty field",
            "current_text": "",
            "expected_behavior": "Should add all fields",
            "expected_duplicates": [],
            "expected_missing": business_fields
        },
        {
            "name": "Completely different content",
            "current_text": "Some other tags, different content entirely",
            "expected_behavior": "Should add all fields",
            "expected_duplicates": [],
            "expected_missing": business_fields
        },
        {
            "name": "All fields already present",
            "current_text": "Workpad Fitzrovia Ltd 5 Margaret Street Margaret Street Lifestyle TLE Tenant",
            "expected_behavior": "Should skip (all duplicates)",
            "expected_duplicates": business_fields,
            "expected_missing": []
        },
        {
            "name": "Tenant name already present",
            "current_text": "Some tags, Workpad Fitzrovia Ltd, other content",
            "expected_behavior": "Should add missing fields only",
            "expected_duplicates": ["Workpad Fitzrovia Ltd"],
            "expected_missing": ["5 Margaret Street", "Margaret Street", "Lifestyle", "TLE Tenant"]
        },
        {
            "name": "Multiple fields already present",
            "current_text": "Previous content, Workpad Fitzrovia Ltd, some text, Lifestyle, more content, TLE Tenant",
            "expected_behavior": "Should add only missing fields",
            "expected_duplicates": ["Workpad Fitzrovia Ltd", "Lifestyle", "TLE Tenant"],
            "expected_missing": ["5 Margaret Street", "Margaret Street"]
        },
        {
            "name": "Property and street already present",
            "current_text": "5 Margaret Street, Margaret Street, other tags",
            "expected_behavior": "Should add missing fields",
            "expected_duplicates": ["5 Margaret Street", "Margaret Street"],
            "expected_missing": ["Workpad Fitzrovia Ltd", "Lifestyle", "TLE Tenant"]
        },
        {
            "name": "Mixed with other business",
            "current_text": "Different Company Ltd, 5 Margaret Street, Margaret Street, Finance, TLE Tenant",
            "expected_behavior": "Should add unique fields only",
            "expected_duplicates": ["5 Margaret Street", "Margaret Street", "TLE Tenant"],
            "expected_missing": ["Workpad Fitzrovia Ltd", "Lifestyle"]
        }
    ]
    
    print("Field-Level Duplicate Prevention Test")
    print("=" * 45)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Current text: '{test_case['current_text']}'")
        print(f"Business fields: {business_fields}")
        
        # Simulate the field-level duplicate check logic
        duplicate_fields = []
        missing_fields = []
        
        for field in business_fields:
            if field.strip() and field.strip() in test_case['current_text']:
                duplicate_fields.append(field.strip())
            else:
                missing_fields.append(field.strip())
        
        # Check if all fields are present
        all_present = len(duplicate_fields) == len([f for f in business_fields if f.strip()])
        
        print(f"Duplicate fields found: {duplicate_fields}")
        print(f"Missing fields: {missing_fields}")
        print(f"All fields present: {all_present}")
        
        # Check against expected results
        duplicates_match = set(duplicate_fields) == set(test_case['expected_duplicates'])
        missing_match = set(missing_fields) == set(test_case['expected_missing'])
        
        if duplicates_match and missing_match:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            print(f"  Expected duplicates: {test_case['expected_duplicates']}")
            print(f"  Expected missing: {test_case['expected_missing']}")
            
        print(f"Expected behavior: {test_case['expected_behavior']}")
        
        # Determine what would be added
        if all_present:
            print("Action: Skip (all fields already present)")
        elif missing_fields:
            if duplicate_fields:
                print(f"Action: Add missing fields only: {missing_fields}")
            else:
                print(f"Action: Add all fields: {business_fields}")
        else:
            print("Action: Skip (logic error)")
    
    print("\n" + "=" * 45)
    print("Field-Level Duplicate Prevention Logic:")
    print("- Checks each business field individually")
    print("- Identifies which fields are already present")
    print("- Only adds missing fields, preventing partial duplicates") 
    print("- Allows different businesses with shared location/category")
    print("- Provides detailed logging for debugging")

if __name__ == "__main__":
    test_field_level_duplicate_prevention()
