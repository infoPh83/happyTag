# utilities/tag_utils.py
"""
Centralized tag/keyword parsing utilities for consistent separator handling.

Follows IPTC/XMP standards:
- Primary separator: semicolon (;) 
- Fallback: comma (,) for backwards compatibility
"""

def parse_keywords_from_text(keywords_text):
    """
    Parse keywords from text using standardized separator handling.
    
    Primary separator: semicolon (;) - follows IPTC/XMP standards
    Fallback separator: comma (,) - for backwards compatibility
    
    Returns: List of cleaned keyword strings
    """
    if not keywords_text or not keywords_text.strip():
        return []
    
    keywords_text = keywords_text.strip()
    
    # Use semicolon separator exclusively (IPTC/XMP standard)
    # Note: Comma fallback removed for clean semicolon-only approach
    keywords = []
    for part in keywords_text.split(';'):
        part = part.strip()
        if part:
            keywords.append(part)
    
    # Remove duplicates while preserving order
    unique_keywords = []
    seen = set()
    for keyword in keywords:
        if keyword and keyword not in seen:
            unique_keywords.append(keyword)
            seen.add(keyword)
    
    return unique_keywords


def format_keywords_for_display(keywords_list):
    """
    Format keywords list for display using standard separator.
    
    Uses semicolon (;) as the standard separator following IPTC/XMP standards.
    """
    if not keywords_list:
        return ""
    return "; ".join(str(k).strip() for k in keywords_list if str(k).strip())


def format_keywords_for_metadata(keywords_list):
    """
    Format keywords list for metadata writing (no spaces after separator).
    
    Uses semicolon (;) as the standard separator following IPTC/XMP standards.
    """
    if not keywords_list:
        return ""
    return ";".join(str(k).strip() for k in keywords_list if str(k).strip())


def escape_tags_for_cloudinary(tags_list):
    """
    Escape tags for Cloudinary upload to prevent comma-splitting issues.
    
    Cloudinary internally splits tags on commas even when sent as a list.
    This function replaces commas with a safe alternative to preserve tag integrity.
    
    Args:
        tags_list: List of tag strings
        
    Returns:
        List of escaped tag strings safe for Cloudinary
    """
    if not tags_list:
        return []
    
    escaped_tags = []
    for tag in tags_list:
        if not tag or not str(tag).strip():
            continue
            
        tag_str = str(tag).strip()
        # Replace commas with a safe character sequence that won't be split
        # Using unicode "FULLWIDTH COMMA" (U+FF0C) which displays similarly but won't trigger splitting
        escaped_tag = tag_str.replace(',', '，')  # Regular comma -> fullwidth comma
        escaped_tags.append(escaped_tag)
    
    return escaped_tags


def unescape_tags_from_cloudinary(tags_list):
    """
    Convert escaped Cloudinary tags back to original format.
    
    Reverses the escaping done by escape_tags_for_cloudinary().
    
    Args:
        tags_list: List of escaped tag strings from Cloudinary
        
    Returns:
        List of unescaped tag strings with original commas
    """
    if not tags_list:
        return []
    
    unescaped_tags = []
    for tag in tags_list:
        if not tag or not str(tag).strip():
            continue
            
        tag_str = str(tag).strip()
        # Convert fullwidth comma back to regular comma
        unescaped_tag = tag_str.replace('，', ',')  # Fullwidth comma -> regular comma
        unescaped_tags.append(unescaped_tag)
    
    return unescaped_tags