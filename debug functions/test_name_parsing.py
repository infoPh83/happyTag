# Test the name parsing logic
import os

def test_name_parsing():
    """Test how different executable names would be parsed"""
    
    test_names = [
        "HappyTag_CustomDebug_Win.exe",
        "HappyTag_VerboseDebug_Win.exe", 
        "HappyTag_Debug_Win.exe",
        "HappyTag_Release_Win.exe",
        "HappyTag_Production_Win.exe",
        "HappyTag_MyTest_Win.exe"
    ]
    
    for app_name in test_names:
        print(f"\nTesting: {app_name}")
        
        if 'Debug' in app_name:
            if 'Verbose' in app_name:
                result = "VERBOSE mode - all categories"
            elif 'Custom' in app_name:
                result = "CUSTOM mode - your custom categories"
            else:
                result = "STANDARD debug mode"
        elif 'Release' in app_name or 'Prod' in app_name:
            result = "SILENT mode"
        else:
            result = "BASIC mode (errors+startup)"
            
        print(f"  → {result}")

if __name__ == "__main__":
    test_name_parsing()