"""
Test script to verify the 404 handling logic
"""

def test_404_detection():
    # Test different error message formats that might come from Cloudinary
    test_errors = [
        "Error 404 - Resource not found - Uploads/test images/CopyrightLuca Piffaretti_B.jpg",
        "cloudinary.exceptions.NotFound: Resource not found",
        "HTTP 404: Not Found",
        "Resource 'test' not found",
        "Some other error message",
        "Connection timeout"
    ]
    
    print("=== Testing 404 Detection Logic ===")
    for error_msg in test_errors:
        is_404 = "404" in error_msg or "not found" in error_msg.lower()
        print(f"Error: {error_msg}")
        print(f"Is 404: {is_404}")
        print("-" * 50)

if __name__ == "__main__":
    test_404_detection()