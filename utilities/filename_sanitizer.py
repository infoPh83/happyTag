"""
Filename sanitization utilities for Cloudinary uploads.
Handles problematic characters that cause encoding issues.
"""

import re
import unicodedata

def sanitize_filename_for_cloudinary(filename):
    """
    Sanitize filename by replacing problematic characters with safe alternatives.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename safe for Cloudinary upload
    """
    # Keep the original extension
    name_part, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    
    # Character replacement map for common problematic characters
    replacements = {
        '©': 'Copyright',
        '®': 'Registered',
        '™': 'Trademark',
        '€': 'Euro',
        '£': 'Pound',
        '¥': 'Yen',
        '§': 'Section',
        '¶': 'Paragraph',
        '°': 'Degree',
        'µ': 'Micro',
        '±': 'PlusMinus',
        '÷': 'Division',
        '×': 'Multiply',
        # Add more as needed
    }
    
    # Apply character replacements
    sanitized = name_part
    for char, replacement in replacements.items():
        sanitized = sanitized.replace(char, replacement)
    
    # Normalize Unicode to remove accents and convert to ASCII-compatible form
    sanitized = unicodedata.normalize('NFKD', sanitized)
    sanitized = sanitized.encode('ascii', 'ignore').decode('ascii')
    
    # Replace any remaining non-alphanumeric characters with underscores
    # Keep spaces, hyphens, and underscores for readability
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '_', sanitized)
    
    # Clean up multiple underscores and trim
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    
    # Ensure we don't have an empty name
    if not sanitized:
        sanitized = 'unnamed_file'
    
    return f"{sanitized}.{ext}" if ext else sanitized

def create_cloudinary_public_id(original_filename, folder_path=""):
    """
    Create a Cloudinary-safe public_id from original filename.
    
    Args:
        original_filename (str): Original filename
        folder_path (str): Optional folder path prefix
        
    Returns:
        str: Safe public_id for Cloudinary
    """
    sanitized_filename = sanitize_filename_for_cloudinary(original_filename)
    
    if folder_path:
        # Also sanitize folder path
        sanitized_folder = folder_path.replace('\\', '/').strip('/')
        sanitized_folder = re.sub(r'[^a-zA-Z0-9\s\-_/]', '_', sanitized_folder)
        return f"{sanitized_folder}/{sanitized_filename}"
    
    return sanitized_filename


def generate_unique_public_id(original_filename, folder_path="", cloudinary_cache=None):
    """
    Generate a unique public_id for Cloudinary upload with duplicate detection.
    
    Args:
        original_filename (str): Original filename
        folder_path (str): Optional folder path prefix  
        cloudinary_cache (list): List of existing Cloudinary files to check for duplicates
        
    Returns:
        str: Unique Cloudinary public_id that won't conflict with existing files
    """
    import random
    import string
    
    # Start with basic sanitized public_id
    base_public_id = create_cloudinary_public_id(original_filename, folder_path)
    
    # If no cache provided, return the base public_id
    if not cloudinary_cache:
        return base_public_id
    
    # Check if base public_id already exists in Cloudinary cache
    existing_public_ids = {cf.get('public_id', '') for cf in cloudinary_cache if cf.get('public_id')}
    
    if base_public_id not in existing_public_ids:
        # No conflict, use the base public_id
        return base_public_id
    
    # Conflict detected - generate unique suffix
    attempts = 0
    max_attempts = 100
    
    # Pre-extract name and extension for reuse
    name_part, ext = (base_public_id.rsplit('.', 1) 
                     if '.' in base_public_id and not base_public_id.endswith('/') 
                     else (base_public_id, ''))
    
    while attempts < max_attempts:
        # Generate random suffix
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Create unique public_id with suffix
        unique_public_id = f"{name_part}_{suffix}"
        if ext:
            unique_public_id += f".{ext}"
        
        # Check if this is unique
        if unique_public_id not in existing_public_ids:
            return unique_public_id
            
        attempts += 1
    
    # Fallback: use timestamp if we couldn't generate unique ID
    import time
    timestamp = str(int(time.time()))
    fallback_public_id = f"{name_part}_{timestamp}"
    if ext:
        fallback_public_id += f".{ext}"
    
    return fallback_public_id

if __name__ == "__main__":
    # Test cases
    test_files = [
        "©Luca Piffaretti_A.jpg",
        "©Luca Piffaretti_TP MAYA House_Print_0010.jpg", 
        "Test with €50 and £30.png",
        "Café résumé.pdf",
        "Document with § and ¶.docx",
        "Temperature 25°C.txt"
    ]
    
    print("=== Filename Sanitization Test ===")
    for filename in test_files:
        sanitized = sanitize_filename_for_cloudinary(filename)
        public_id = create_cloudinary_public_id(filename, "test images")
        print(f"Original:  {filename}")
        print(f"Sanitized: {sanitized}")
        print(f"Public ID: {public_id}")
        print("-" * 50)