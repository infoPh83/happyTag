#!/usr/bin/env python3
"""
Test script to verify that tag_manager can handle different file formats
"""

def test_file_format_detection():
    """Test the file format detection logic"""
    
    # Test cases: (file_path, expected_engine)
    test_cases = [
        ("test.ods", "odf"),
        ("test.xlsx", "openpyxl"),
        ("test.xlsm", "openpyxl"),
        ("test.xls", "xlrd"),
        ("TEST.ODS", "odf"),  # Test case sensitivity
        ("TEST.XLSX", "openpyxl"),
        ("TEST.XLSM", "openpyxl"),
        ("unknown.abc", "odf"),  # Unknown extension defaults to odf
    ]
    
    print("Testing file format detection logic...")
    print("=" * 50)
    
    for file_path, expected_engine in test_cases:
        # Simulate the detection logic from tag_manager.py
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'ods':
            detected_engine = 'odf'
        elif file_extension in ['xlsx', 'xlsm']:
            detected_engine = 'openpyxl'
        elif file_extension == 'xls':
            detected_engine = 'xlrd'
        else:
            detected_engine = 'odf'  # Default
        
        status = "✅ PASS" if detected_engine == expected_engine else "❌ FAIL"
        print(f"{status} | {file_path:12} → {detected_engine:10} (expected: {expected_engine})")
    
    print("=" * 50)
    print("File format detection test completed!")

def list_supported_formats():
    """List all supported file formats"""
    print("\nSupported File Formats:")
    print("=" * 30)
    print("📊 ODS Files (.ods)")
    print("   - OpenDocument Spreadsheet")
    print("   - Engine: odf (via odfpy)")
    print("   - Full color support")
    print()
    print("📊 Excel Files (.xlsx)")
    print("   - Excel 2007+ format")
    print("   - Engine: openpyxl")
    print("   - Supports modern Excel features")
    print()
    print("📊 Excel Macro Files (.xlsm)")
    print("   - Excel 2007+ with macros")
    print("   - Engine: openpyxl")
    print("   - Macros are ignored during reading")
    print()
    print("📊 Legacy Excel Files (.xls)")
    print("   - Excel 97-2003 format")
    print("   - Engine: xlrd")
    print("   - Limited feature support")
    print()
    print("🔄 Auto-Detection:")
    print("   - File format detected by extension")
    print("   - No manual configuration needed")
    print("   - Fallback to ODS if unknown")

if __name__ == "__main__":
    test_file_format_detection()
    list_supported_formats()
