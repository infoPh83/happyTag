#!/usr/bin/env python3
"""
Debug script to investigate the discrepancy between local Cloudinary tracking
and actual Cloudinary resource count.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path to import our modules
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

import cloudinary
import cloudinary.api
from cloudinary.api import usage
from utilities.image_assessment import ImageAssessment
from utilities.cloudinary_upload_handler import check_file_cloudinary_status_by_metadata

def debug_cloudinary_discrepancy():
    """Debug the discrepancy between local and remote Cloudinary counts"""
    
    print("=== CLOUDINARY COUNT DISCREPANCY INVESTIGATION ===\n")
    
    # Load Cloudinary config from settings
    settings_file = script_dir / "settings.pkl"
    if not settings_file.exists():
        print("❌ No settings.pkl found. Please configure Cloudinary first.")
        return
    
    import pickle
    try:
        with open(settings_file, 'rb') as f:
            settings = pickle.load(f)
        
        cloudinary_config = settings.get('cloudinary_config', [])
        if len(cloudinary_config) < 4:
            print("❌ Incomplete Cloudinary configuration")
            return
            
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloudinary_config[1],
            api_key=cloudinary_config[2], 
            api_secret=cloudinary_config[3]
        )
        
        print(f"✅ Cloudinary configured for: {cloudinary_config[1]}")
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return
    
    # 1. Get usage API data
    print("\n1. USAGE API DATA:")
    print("-" * 40)
    try:
        usage_data = usage()
        resources_count = usage_data.get('resources', 0)
        derived_count = usage_data.get('derived_resources', 0)
        objects_count = usage_data.get('objects', {}).get('usage', 0)
        
        print(f"Resources: {resources_count}")
        print(f"Derived Resources: {derived_count}")
        print(f"Objects Usage: {objects_count}")
        print(f"Total Storage: {usage_data.get('storage', {}).get('usage', 0)} bytes")
        
    except Exception as e:
        print(f"❌ Error getting usage data: {e}")
        return
    
    # 2. Get actual resources from API
    print("\n2. RESOURCES API DATA:")
    print("-" * 40)
    try:
        # Get first 100 resources to see what we actually have
        resources_response = cloudinary.api.resources(max_results=100)
        actual_resources = resources_response.get('resources', [])
        total_count = resources_response.get('total_count', 0)
        
        print(f"Total Count from API: {total_count}")
        print(f"Resources returned: {len(actual_resources)}")
        
        if actual_resources:
            print("\nFirst 10 resources:")
            for i, resource in enumerate(actual_resources[:10]):
                public_id = resource.get('public_id', 'N/A')
                resource_type = resource.get('resource_type', 'N/A')
                format_type = resource.get('format', 'N/A')
                bytes_size = resource.get('bytes', 0)
                created = resource.get('created_at', 'N/A')
                print(f"  {i+1}. {public_id} ({resource_type}/{format_type}) - {bytes_size} bytes - {created}")
        
        # Try different resource types
        for resource_type in ['image', 'video', 'raw']:
            try:
                type_resources = cloudinary.api.resources(resource_type=resource_type, max_results=1)
                type_count = type_resources.get('total_count', 0)
                print(f"{resource_type.title()} resources: {type_count}")
            except Exception as e:
                print(f"{resource_type.title()} resources: Error - {e}")
                
    except Exception as e:
        print(f"❌ Error getting resources data: {e}")
    
    # 3. Check local folder for comparison
    print("\n3. LOCAL FOLDER ANALYSIS:")
    print("-" * 40)
    
    # Let user specify folder to check
    test_folder = input("Enter path to your image folder (or press Enter to skip): ").strip()
    
    if test_folder and os.path.exists(test_folder):
        print(f"Analyzing folder: {test_folder}")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        image_files = []
        
        for root, dirs, files in os.walk(test_folder):
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    image_files.append(os.path.join(root, file))
        
        print(f"Total image files found: {len(image_files)}")
        
        # Check how many have Cloudinary metadata
        cloudinary_files = []
        assessment = ImageAssessment()
        
        for i, file_path in enumerate(image_files[:20]):  # Check first 20 to avoid too much output
            try:
                # Check if file has Cloudinary metadata
                has_cloudinary_meta = check_file_cloudinary_status_by_metadata(file_path)
                if has_cloudinary_meta:
                    cloudinary_files.append(file_path)
                    print(f"  ✅ {os.path.basename(file_path)} - has Cloudinary metadata")
                else:
                    print(f"  ❌ {os.path.basename(file_path)} - no Cloudinary metadata")
                    
            except Exception as e:
                print(f"  ⚠️  {os.path.basename(file_path)} - error checking: {e}")
        
        print(f"\nFiles with Cloudinary metadata (first 20 checked): {len(cloudinary_files)}")
        
        if len(image_files) > 20:
            print(f"Note: Only checked first 20 of {len(image_files)} total files")
    
    # 4. Summary
    print("\n4. SUMMARY:")
    print("-" * 40)
    print(f"Cloudinary Usage API reports: {resources_count} resources")
    print(f"Cloudinary Resources API reports: {total_count} resources")
    
    if 'cloudinary_files' in locals():
        print(f"Local files with Cloudinary metadata: {len(cloudinary_files)} (sample)")
    
    print("\nPOSSIBLE EXPLANATIONS:")
    print("• Different API endpoints count resources differently")
    print("• Some local files may have stale/incorrect metadata") 
    print("• Some images may have been deleted from Cloudinary but local metadata not updated")
    print("• Cloudinary may deduplicate identical images")
    print("• Resource counting may exclude certain types or states")

if __name__ == "__main__":
    debug_cloudinary_discrepancy()
