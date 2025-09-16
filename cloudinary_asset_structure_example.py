# Example of Cloudinary Asset Data Structure
# This shows what fields are available from cloudinary.api.resources()

"""
When you call cloudinary.api.resources(), each asset in the response includes:

BASIC ASSET INFORMATION:
- public_id: Unique identifier (e.g., "2024_photos/vacation_photo.jpg")
- filename: Original filename (may not always be available)
- format: File format (jpg, png, webp, etc.)
- bytes: File size in bytes
- width: Image width in pixels
- height: Image height in pixels
- created_at: Upload timestamp
- uploaded_at: Upload timestamp (alternative field)

CLOUDINARY-SPECIFIC DATA:
- url: Public URL to access the image
- secure_url: HTTPS URL to access the image
- version: Cloudinary version number
- signature: Security signature
- resource_type: Usually "image"
- type: Usually "upload"

METADATA AND TAGS:
- tags: Array of tags associated with the image
- context: Custom metadata key-value pairs
- metadata: Additional metadata
- faces: Face detection data (if enabled)
- colors: Dominant colors (if analysis enabled)

FOLDER STRUCTURE:
- folder: Folder path (extracted from public_id)
- asset_id: Internal Cloudinary asset ID
"""

# Example of what a single asset object looks like:
example_cloudinary_asset = {
    "public_id": "2024_photos/my_vacation_photo.jpg",
    "format": "jpg",
    "version": 1234567890,
    "resource_type": "image",
    "type": "upload",
    "created_at": "2024-09-15T10:30:00Z",
    "uploaded_at": "2024-09-15T10:30:00Z",
    "bytes": 2045632,  # File size in bytes
    "width": 4000,
    "height": 3000,
    "url": "http://res.cloudinary.com/your-cloud/image/upload/v1234567890/2024_photos/my_vacation_photo.jpg",
    "secure_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/2024_photos/my_vacation_photo.jpg",
    "tags": ["vacation", "2024", "beach"],
    "context": {"caption": "Beautiful sunset at the beach"},
    "metadata": {"camera": "Canon EOS R5"},
    "signature": "abc123def456...",
    "folder": "2024_photos"
}

# How to extract key information for your application:
def extract_asset_info(cloudinary_asset):
    """Extract useful information from a Cloudinary asset for HappyTag"""
    return {
        'cloudinary_public_id': cloudinary_asset.get('public_id'),
        'filename': extract_filename_from_public_id(cloudinary_asset.get('public_id', '')),
        'format': cloudinary_asset.get('format'),
        'size_bytes': cloudinary_asset.get('bytes'),
        'dimensions': {
            'width': cloudinary_asset.get('width'),
            'height': cloudinary_asset.get('height')
        },
        'tags': cloudinary_asset.get('tags', []),
        'upload_date': cloudinary_asset.get('created_at'),
        'cloudinary_url': cloudinary_asset.get('secure_url', cloudinary_asset.get('url')),
        'folder': cloudinary_asset.get('folder', ''),
        'metadata': cloudinary_asset.get('context', {})
    }

def extract_filename_from_public_id(public_id):
    """Extract original filename from Cloudinary public_id"""
    if '/' in public_id:
        return public_id.split('/')[-1]  # Get last part after folder
    return public_id