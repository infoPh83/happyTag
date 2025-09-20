"""
ExifTool utility module for HappyTag application.
Provides shared ExifTool functionality for main app and upload handlers.
"""

import os
import subprocess
import platform
from pathlib import Path
from utilities.debug_utils import debug_startup, debug_upload, debug_metadata

# Global ExifTool configuration
EXIFTOOL_AVAILABLE = False
EXIFTOOL_PATH = None

def initialize_exiftool():
    """Initialize ExifTool and set global availability variables"""
    global EXIFTOOL_AVAILABLE, EXIFTOOL_PATH
    
    debug_startup("Initializing ExifTool...")
    
    # Reset to defaults
    EXIFTOOL_AVAILABLE = False
    EXIFTOOL_PATH = None
    
    current_platform = platform.system().lower()
    debug_startup(f"Platform detected: {current_platform}")
    
    # Define potential ExifTool paths based on platform
    if current_platform == 'windows':
        potential_paths = [
            'utilities/exiftool.exe',
            'exiftool.exe',
            'C:/Program Files/ExifTool/exiftool.exe',
            'C:/ExifTool/exiftool.exe'
        ]
    else:  # macOS/Linux
        potential_paths = [
            '/usr/local/bin/exiftool',
            '/usr/bin/exiftool',
            '/opt/homebrew/bin/exiftool',
            'exiftool'  # In PATH
        ]
    
    # Test each potential path
    for path in potential_paths:
        debug_startup(f"Testing ExifTool path: {path}")
        try:
            result = subprocess.run(
                [path, '-ver'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                EXIFTOOL_AVAILABLE = True
                EXIFTOOL_PATH = path
                version = result.stdout.strip()
                debug_startup(f"✅ ExifTool found at: {path} (version {version})")
                break
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            debug_startup(f"❌ ExifTool not found at {path}: {e}")
            continue
    
    if not EXIFTOOL_AVAILABLE:
        debug_startup("❌ ExifTool not found in any standard location")
        # Try system PATH as last resort
        try:
            result = subprocess.run(
                ['exiftool', '-ver'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                EXIFTOOL_AVAILABLE = True
                EXIFTOOL_PATH = 'exiftool'
                version = result.stdout.strip()
                debug_startup(f"✅ ExifTool found in system PATH (version {version})")
        except Exception as e:
            debug_startup(f"❌ ExifTool not found in system PATH: {e}")
    
    debug_startup(f"Final ExifTool status: AVAILABLE={EXIFTOOL_AVAILABLE}, PATH={EXIFTOOL_PATH}")
    return EXIFTOOL_AVAILABLE, EXIFTOOL_PATH

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
    if not EXIFTOOL_AVAILABLE or not EXIFTOOL_PATH:
        return {
            'success': False,
            'message': 'ExifTool not available for writing metadata',
            'details': {'exiftool_available': EXIFTOOL_AVAILABLE, 'exiftool_path': EXIFTOOL_PATH}
        }
    
    try:
        # Write public_id to UserComment field first with UTF-8 encoding support
        public_id_commands = [
            EXIFTOOL_PATH,
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
    if not EXIFTOOL_AVAILABLE or not EXIFTOOL_PATH:
        debug_upload(f"ExifTool not available for reading metadata from {file_path}")
        return None
        
    try:
        # Use ExifTool to read UserComment field with better encoding handling
        read_commands = [
            EXIFTOOL_PATH,
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

# Initialize ExifTool when module is imported
initialize_exiftool()