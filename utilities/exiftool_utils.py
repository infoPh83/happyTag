"""
ExifTool utility module for HappyTag application.
Provides shared ExifTool functionality for main app and upload handlers.
"""

import os
import subprocess
import platform
from pathlib import Path
from utilities.debug_utils import debug_startup, debug_upload, debug_metadata
from utilities.exiftool_detector import get_exiftool_info

def get_exiftool_command():
    """
    Get the appropriate ExifTool command structure for subprocess calls.
    
    Returns:
        list[str]: Command components for subprocess, or None if ExifTool not available
    """
    # Get current status from the unified detector
    info = get_exiftool_info()
    
    if not info['available'] or not info['path']:
        return None
    
    exiftool_path = info['path']
    
    if isinstance(exiftool_path, dict) and exiftool_path.get('type') == 'perl':
        # Perl-based ExifTool: [perl.exe, exiftool.pl]
        return [str(exiftool_path['path']), str(exiftool_path['args'][0])]
    else:
        # Regular ExifTool executable: [exiftool.exe]
        return [str(exiftool_path)]

def initialize_exiftool():
    """
    Initialize ExifTool using the unified detector.
    This function is kept for backward compatibility but now delegates to exiftool_detector.
    """
    # Delegate to unified detector - no local state needed
    info = get_exiftool_info()
    
    debug_startup(f"ExifTool Utils: AVAILABLE={info['available']}, PATH={info['path']}")
    
    return info['available']

def write_cloudinary_metadata_to_file(file_path, public_id, tags=None):
    """
    Write both Cloudinary public_id and tags to image metadata using ExifTool.
    
    Args:
        file_path: Path to the image file
        public_id: The Cloudinary public_id to store
        tags: Optional list of tags to also store
        
    Returns:
        dict: {'success': bool, 'message': str, 'details': dict}
    """
    try:
        # Get the appropriate ExifTool command structure (auto-initializes if needed)
        exiftool_cmd = get_exiftool_command()
        if not exiftool_cmd:
            return {
                'success': False,
                'message': 'ExifTool not available for writing metadata',
                'details': {'message': 'ExifTool command not available'}
            }
        
        # Write public_id to UserComment field first with UTF-8 encoding support
        public_id_commands = exiftool_cmd + [
            '-overwrite_original_in_place',  # Preserves extended attributes including Finder tags
            '-charset', 'UTF8',  # Explicit UTF-8 charset for special characters
            '-codedcharacterset=UTF8',  # For IPTC fields
            f'-UserComment=cloudinary_public_id:{public_id}',
            str(file_path)
        ]
        
        debug_upload(f"Writing public_id with command: {' '.join(public_id_commands)}")
        
        # On Windows, handle Unicode filenames properly
        if os.name == 'nt':  # Windows
            # Use CREATE_NO_WINDOW to hide console window and handle Unicode properly
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                public_id_commands, 
                capture_output=True, 
                text=False,  # Use binary mode to avoid encoding issues
                timeout=30,
                startupinfo=startupinfo
            )
        else:  # Unix-like systems
            result = subprocess.run(
                public_id_commands, 
                capture_output=True, 
                text=False,  # Use binary mode to avoid encoding issues
                timeout=30
            )
        
        # Decode the output safely
        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
        
        if result.returncode != 0:
            return {
                'success': False,
                'message': f'ExifTool error writing public_id: {stderr}',
                'details': {'returncode': result.returncode, 'stderr': stderr}
            }
        
        # NOTE: Tags are no longer written here to avoid duplication with main app's tag writing system
        # The main app already writes tags to standardized metadata fields (XMP-dc:Subject, IPTC:Keywords, etc.)
        # This function now only writes the Cloudinary public_id to avoid metadata duplication
        tags_written = 0
        if tags:
            debug_upload(f"Skipping tag write to avoid duplication - main app handles tag metadata")
        
        details = {
            'public_id': public_id,
            'tags_skipped_to_avoid_duplication': len(tags) if tags else 0,
            'file': os.path.basename(file_path)
        }
        debug_upload(f"✅ Successfully wrote Cloudinary public_id to {os.path.basename(file_path)}: {public_id} (tags handled by main app)")
        return {
            'success': True,
            'message': 'Metadata written successfully',
            'details': details
        }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Exception writing metadata: {e}',
            'details': {'exception': str(e)}
        }

def get_cloudinary_public_id_from_metadata(file_path):
    """
    Read stored Cloudinary public_id from image metadata using ExifTool.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        str or None: The public_id if found, None if not found or error
    """
    try:
        # Get the appropriate ExifTool command structure (auto-initializes if needed)
        exiftool_cmd = get_exiftool_command()
        if not exiftool_cmd:
            debug_upload(f"ExifTool not available for reading metadata from {file_path}")
            return None
        
        # Use ExifTool to read UserComment field with better encoding handling
        read_commands = exiftool_cmd + [
            '-charset', 'UTF8',  # Explicit UTF-8 charset for special characters
            '-UserComment',
            '-s3',  # Short format, no tag names
            str(file_path)
        ]
        
        # On Windows, handle Unicode filenames properly
        if os.name == 'nt':  # Windows
            # Use CREATE_NO_WINDOW to hide console window and handle Unicode properly
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                read_commands, 
                capture_output=True, 
                text=False, 
                timeout=30,
                startupinfo=startupinfo
            )
        else:  # Unix-like systems
            result = subprocess.run(
                read_commands, 
                capture_output=True, 
                text=False, 
                timeout=30
            )
        
        if result.returncode == 0 and result.stdout:
            try:
                # Try to decode as UTF-8, with fallback handling
                user_comment = result.stdout.decode('utf-8', errors='replace').strip()
            except UnicodeDecodeError:
                # Fallback to latin-1 which never fails
                user_comment = result.stdout.decode('latin-1', errors='replace').strip()
            
            # Check if it contains our cloudinary public_id marker
            if user_comment.startswith('cloudinary_public_id:'):
                public_id = user_comment.replace('cloudinary_public_id:', '', 1)
                debug_metadata(f"Found Cloudinary public_id in metadata: {public_id}")
                return public_id
        
        debug_metadata(f"No Cloudinary public_id found in metadata for {os.path.basename(file_path)}")
        return None
        
    except Exception as e:
        debug_upload(f"Error reading metadata from {file_path}: {e}")
        return None

# NOTE: ExifTool initialization is now handled by the main application
# using the unified exiftool_detector module. No module-level initialization needed.