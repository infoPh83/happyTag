#!/usr/bin/env python3

import exiftool
import os

def check_webp_metadata():
    """Check the metadata structure of the WebP file after re-tagging"""
    
    webp_file = r"tag test images\01\webP_from_raw_NO_INITIAL_TAGS.webp"
    
    if not os.path.exists(webp_file):
        print(f"WebP file not found: {webp_file}")
        return
    
    print(f"Checking metadata structure of: {webp_file}")
    
    try:
        # Use local ExifTool
        exiftool_path = r"packages\exiftool_win64\exiftool-13.34_64\exiftool(-k).exe"
        
        with exiftool.ExifTool(executable=exiftool_path) as et:
            
            print(f"\n=== CURRENT XMP SUBJECT (formatted) ===")
            subject_formatted = et.execute('-XMP:Subject', webp_file)
            print(f"XMP:Subject: {subject_formatted}")
            
            print(f"\n=== CURRENT XMP KEYWORDS (formatted) ===")
            keywords_formatted = et.execute('-XMP:Keywords', webp_file)
            print(f"XMP:Keywords: {keywords_formatted}")
            
            print(f"\n=== RAW XMP STRUCTURE ===")
            
            # Get the raw XMP block
            xmp_raw = et.execute('-XMP', '-b', webp_file)
            if xmp_raw:
                if isinstance(xmp_raw, bytes):
                    xmp_str = xmp_raw.decode('utf-8', errors='ignore')
                else:
                    xmp_str = str(xmp_raw)
                
                # Look for dc:subject section
                if 'dc:subject' in xmp_str:
                    lines = xmp_str.split('\n')
                    in_subject = False
                    subject_lines = []
                    
                    for line in lines:
                        if '<dc:subject>' in line:
                            in_subject = True
                            subject_lines.append(line)
                        elif in_subject:
                            subject_lines.append(line)
                            if '</dc:subject>' in line:
                                break
                    
                    print("Dublin Core Subject structure:")
                    for line in subject_lines:
                        print(line.strip())
                        
                else:
                    print("No dc:subject found in XMP metadata")
                    print("First 500 characters of XMP:")
                    print(xmp_str[:500])
            
            print(f"\n=== WHAT WINDOWS EXPLORER EXPECTS ===")
            print("Windows Explorer expects XMP:Subject (Dublin Core) with this structure:")
            print("<dc:subject>")
            print("   <rdf:Bag>")
            print("      <rdf:li>keyword1</rdf:li>")
            print("      <rdf:li>keyword2</rdf:li>")
            print("      <rdf:li>keyword3</rdf:li>")
            print("   </rdf:Bag>")
            print("</dc:subject>")
            
            print(f"\n=== TROUBLESHOOTING ===")
            print("If tags still don't appear in Windows Explorer:")
            print("1. Refresh Windows Explorer (F5)")
            print("2. Right-click file → Properties → Details tab to check tags")
            print("3. Make sure 'Tags' column is visible in Windows Explorer")
            print("4. Try viewing in Windows Explorer's 'Details' view")
            
    except Exception as e:
        print(f"Error checking metadata: {e}")

if __name__ == "__main__":
    check_webp_metadata()
