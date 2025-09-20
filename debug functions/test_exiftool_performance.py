#!/usr/bin/env python3
"""
Test script to compare ExifTool performance between single call vs multiple calls
"""

import time
import os
from exiftool import ExifTool

def test_single_call(et, file_path):
    """Test single combined ExifTool call"""
    start_time = time.time()
    try:
        result = et.execute('-DateTimeOriginal', '-CreateDate', '-IPTC:Keywords', '-XMP:Keywords', '-XMP:Subject', file_path)
        # Process the combined result
        if result and len(result) > 0:
            data = result[0]
            year = None
            keywords = []
            
            # Extract year from date fields
            for date_field in ['DateTimeOriginal', 'CreateDate']:
                if date_field in data and data[date_field] and data[date_field] != '-':
                    try:
                        year = int(str(data[date_field])[:4])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Extract keywords from all keyword fields
            for keyword_field in ['IPTC.Keywords', 'XMP.Keywords', 'XMP.Subject']:
                if keyword_field in data and data[keyword_field]:
                    keyword_data = data[keyword_field]
                    if isinstance(keyword_data, list):
                        keywords.extend(keyword_data)
                    else:
                        keywords.append(keyword_data)
            
            # Remove duplicates
            keywords = list(set([k.strip() for k in keywords if k and k.strip()]))
            
        end_time = time.time()
        return end_time - start_time, year, keywords
    except Exception as e:
        end_time = time.time()
        return end_time - start_time, None, []

def test_multiple_calls(et, file_path):
    """Test multiple separate ExifTool calls"""
    start_time = time.time()
    year = None
    keywords = []
    
    try:
        # Get date info with separate calls
        for date_tag in ['-DateTimeOriginal', '-CreateDate']:
            try:
                result = et.execute(date_tag, file_path)
                if result and len(result) > 0:
                    date_value = result[0].get(date_tag.replace('-', ''))
                    if date_value and date_value != '-':
                        year = int(str(date_value)[:4])
                        break
            except Exception:
                continue
        
        # Get keywords with separate calls
        for keyword_tag in ['-IPTC:Keywords', '-XMP:Keywords', '-XMP:Subject']:
            try:
                result = et.execute(keyword_tag, file_path)
                if result and len(result) > 0:
                    tag_name = keyword_tag.replace('-', '').replace(':', '.')
                    keyword_data = result[0].get(tag_name)
                    if keyword_data:
                        if isinstance(keyword_data, list):
                            keywords.extend(keyword_data)
                        else:
                            keywords.append(keyword_data)
            except Exception:
                continue
        
        # Remove duplicates
        keywords = list(set([k.strip() for k in keywords if k and k.strip()]))
        
    except Exception as e:
        pass
    
    end_time = time.time()
    return end_time - start_time, year, keywords

def main():
    # Test files directory
    test_dir = "test images"
    
    if not os.path.exists(test_dir):
        print(f"Test directory '{test_dir}' not found!")
        return
    
    # Get test image files
    test_files = []
    for file in os.listdir(test_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif')):
            test_files.append(os.path.join(test_dir, file))
    
    if not test_files:
        print("No test images found!")
        return
    
    print(f"Testing ExifTool performance with {len(test_files)} images...")
    print("=" * 60)
    
    with ExifTool() as et:
        # Test single call approach
        print("\n🚀 SINGLE CALL APPROACH:")
        single_call_times = []
        single_call_results = []
        
        for file_path in test_files:
            time_taken, year, keywords = test_single_call(et, file_path)
            single_call_times.append(time_taken)
            single_call_results.append((year, keywords))
            print(f"  {os.path.basename(file_path)}: {time_taken:.4f}s -> Year: {year}, Keywords: {len(keywords)}")
        
        # Test multiple calls approach
        print("\n🔄 MULTIPLE CALLS APPROACH:")
        multiple_call_times = []
        multiple_call_results = []
        
        for file_path in test_files:
            time_taken, year, keywords = test_multiple_calls(et, file_path)
            multiple_call_times.append(time_taken)
            multiple_call_results.append((year, keywords))
            print(f"  {os.path.basename(file_path)}: {time_taken:.4f}s -> Year: {year}, Keywords: {len(keywords)}")
        
        # Calculate statistics
        avg_single = sum(single_call_times) / len(single_call_times)
        avg_multiple = sum(multiple_call_times) / len(multiple_call_times)
        total_single = sum(single_call_times)
        total_multiple = sum(multiple_call_times)
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY:")
        print("=" * 60)
        print(f"Single Call Approach:")
        print(f"  Average time per image: {avg_single:.4f}s")
        print(f"  Total time for all images: {total_single:.4f}s")
        print(f"\nMultiple Calls Approach:")
        print(f"  Average time per image: {avg_multiple:.4f}s")
        print(f"  Total time for all images: {total_multiple:.4f}s")
        print(f"\n🎯 IMPROVEMENT:")
        if avg_multiple > avg_single:
            improvement = ((avg_multiple - avg_single) / avg_multiple) * 100
            speedup = avg_multiple / avg_single
            print(f"  Single call is {improvement:.1f}% faster")
            print(f"  Speedup factor: {speedup:.2f}x")
        else:
            slowdown = ((avg_single - avg_multiple) / avg_single) * 100
            print(f"  Multiple calls is {slowdown:.1f}% faster")
        
        print(f"\n⏱️  Time saved per image: {(avg_multiple - avg_single):.4f}s")
        print(f"⏱️  Total time saved: {(total_multiple - total_single):.4f}s")
        
        # Verify results are consistent
        results_match = True
        for i, (single_result, multiple_result) in enumerate(zip(single_call_results, multiple_call_results)):
            if single_result != multiple_result:
                print(f"\n⚠️  Results differ for {os.path.basename(test_files[i])}: {single_result} vs {multiple_result}")
                results_match = False
        
        if results_match:
            print(f"\n✅ All results match between single and multiple call approaches!")
        
        print("=" * 60)

if __name__ == "__main__":
    main()