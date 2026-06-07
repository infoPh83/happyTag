"""
Cross-platform ExifTool detection and initialization module.
Handles both PyInstaller bundled ExifTool and system installations.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from utilities.debug_utils import debug_startup, debug_exiftool

# Global ExifTool configuration
EXIFTOOL_AVAILABLE = False
EXIFTOOL_PATH = None

def detect_bundled_exiftool():
    """
    Detect bundled ExifTool in PyInstaller package.
    This should be the PRIMARY detection method for production builds.
    """
    debug_startup("Checking for bundled ExifTool...")
    
    # Determine if we're running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        debug_startup(f"Running from PyInstaller bundle, base path: {base_path}")
    else:
        base_path = os.path.abspath(".")
        debug_startup(f"Running in development mode, base path: {base_path}")
    
    system = platform.system().lower()
    is_64bit = platform.architecture()[0] == '64bit'
    
    if system == 'windows':
        # Windows: Try multiple ExifTool variants
        if is_64bit:
            # Try both (-k) version and perl-based version
            candidates = [
                # Option 1: Regular exiftool.exe (if available) - fastest
                os.path.join(base_path, 'packages', 'exiftool_win64', 'exiftool-13.34_64', 'exiftool.exe'),
                # Option 2: Perl version - more reliable but slower
                {
                    'path': os.path.join(base_path, 'packages', 'exiftool_win64', 'exiftool-13.34_64', 'exiftool_files', 'perl.exe'),
                    'args': [os.path.join(base_path, 'packages', 'exiftool_win64', 'exiftool-13.34_64', 'exiftool_files', 'exiftool.pl'), '-ver'],
                    'type': 'perl'
                },
                # Option 3: Keep-alive version (last resort) - slowest
                os.path.join(base_path, 'packages', 'exiftool_win64', 'exiftool-13.34_64', 'exiftool(-k).exe')
            ]
        else:
            candidates = [
                os.path.join(base_path, 'packages', 'exiftool_win32', 'exiftool-13.34_32', 'exiftool.exe'),
                {
                    'path': os.path.join(base_path, 'packages', 'exiftool_win32', 'exiftool-13.34_32', 'exiftool_files', 'perl.exe'),
                    'args': [os.path.join(base_path, 'packages', 'exiftool_win32', 'exiftool-13.34_32', 'exiftool_files', 'exiftool.pl'), '-ver'],
                    'type': 'perl'
                },
                os.path.join(base_path, 'packages', 'exiftool_win32', 'exiftool-13.34_32', 'exiftool(-k).exe')
            ]
        
        for candidate in candidates:
            if isinstance(candidate, dict):
                # Perl-based version
                debug_exiftool(f"Windows bundled ExifTool (Perl): {candidate['path']} + exiftool.pl")
                if os.path.exists(candidate['path']) and os.path.exists(candidate['args'][0]):
                    debug_startup(f"✅ Bundled ExifTool (Perl) found at: {candidate['path']}")
                    if test_exiftool_perl(candidate['path'], candidate['args'][0]):
                        return {'path': candidate['path'], 'args': candidate['args'], 'type': 'perl'}
                    else:
                        debug_startup(f"❌ Bundled ExifTool (Perl) failed test: {candidate['path']}")
            else:
                # Regular executable
                debug_exiftool(f"Windows bundled ExifTool path: {candidate}")
                if os.path.exists(candidate):
                    debug_startup(f"✅ Bundled ExifTool found at: {candidate}")
                    timeout = 3 if 'exiftool(-k).exe' in candidate else 10  # Shorter timeout for (-k) version
                    if test_exiftool_executable(candidate, timeout=timeout):
                        return candidate
                    else:
                        debug_startup(f"❌ Bundled ExifTool exists but failed version test: {candidate}")
                else:
                    debug_startup(f"❌ Bundled ExifTool not found at: {candidate}")
        
    elif system == 'darwin':  # macOS
        # macOS: Perl version of ExifTool
        exiftool_path = os.path.join(base_path, 'packages', 'Image-ExifTool-13.34', 'exiftool')
        debug_exiftool(f"macOS bundled ExifTool path: {exiftool_path}")
        
        if os.path.exists(exiftool_path):
            debug_startup(f"✅ Bundled ExifTool found at: {exiftool_path}")
            if test_exiftool_executable(exiftool_path):
                return exiftool_path
            else:
                debug_startup(f"❌ Bundled ExifTool exists but failed version test: {exiftool_path}")
        else:
            debug_startup(f"❌ Bundled ExifTool not found at: {exiftool_path}")
        
    elif system == 'linux':
        # Linux: Perl version of ExifTool
        exiftool_path = os.path.join(base_path, 'packages', 'Image-ExifTool-13.34', 'exiftool')
        debug_exiftool(f"Linux bundled ExifTool path: {exiftool_path}")
        
        if os.path.exists(exiftool_path):
            debug_startup(f"✅ Bundled ExifTool found at: {exiftool_path}")
            if test_exiftool_executable(exiftool_path):
                return exiftool_path
            else:
                debug_startup(f"❌ Bundled ExifTool exists but failed version test: {exiftool_path}")
        else:
            debug_startup(f"❌ Bundled ExifTool not found at: {exiftool_path}")
        
    else:
        debug_startup(f"Unsupported platform for bundled ExifTool: {system}")
    
    return None

def detect_system_exiftool():
    """
    Detect system-installed ExifTool.
    This is the fallback method for development or system installations.
    """
    debug_startup("Checking for system-installed ExifTool...")
    
    current_platform = platform.system().lower()
    
    # Define potential ExifTool paths based on platform
    if current_platform == 'windows':
        potential_paths = [
            'exiftool.exe',  # In PATH (most common)
            'C:/Program Files/ExifTool/exiftool.exe',
            'C:/ExifTool/exiftool.exe',
            'utilities/exiftool.exe'  # Local development fallback
        ]
    else:  # macOS/Linux
        potential_paths = [
            'exiftool',  # In PATH (most common)
            '/usr/local/bin/exiftool',  # Homebrew on macOS
            '/opt/homebrew/bin/exiftool',  # Apple Silicon Homebrew
            '/usr/bin/exiftool',  # System package managers
        ]
    
    # Test each potential path
    for path in potential_paths:
        debug_startup(f"Testing system ExifTool path: {path}")
        if test_exiftool_executable(path):
            debug_startup(f"✅ System ExifTool found at: {path}")
            return path
        else:
            debug_startup(f"❌ System ExifTool not found or failed at: {path}")
    
    return None

def test_exiftool_executable(path, timeout=10):
    """
    Test if ExifTool executable works by checking its version.
    Returns True if executable works, False otherwise.
    """
    try:
        kwargs = {}
        if platform.system().lower() == 'windows':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            [path, '-ver'], 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            **kwargs
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            debug_startup(f"ExifTool version test successful: {version}")
            return True
        else:
            debug_startup(f"ExifTool version test failed with return code: {result.returncode}")
            return False
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        debug_startup(f"ExifTool test failed: {e}")
        return False

def test_exiftool_perl(perl_path, exiftool_pl_path, timeout=10):
    """
    Test if Perl-based ExifTool works by checking its version.
    Returns True if executable works, False otherwise.
    """
    try:
        kwargs = {}
        if platform.system().lower() == 'windows':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            [perl_path, exiftool_pl_path, '-ver'], 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            **kwargs
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            debug_startup(f"ExifTool (Perl) version test successful: {version}")
            return True
        else:
            debug_startup(f"ExifTool (Perl) version test failed with return code: {result.returncode}")
            return False
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        debug_startup(f"ExifTool (Perl) test failed: {e}")
        return False

def initialize_exiftool():
    """
    Initialize ExifTool with smart detection order optimized for development vs production.
    
    Detection Priority:
    - Development mode: System first (faster), then bundled (if system fails)
    - PyInstaller builds: Bundled first (more reliable), then system (fallback)
    
    Returns:
        bool: True if ExifTool is available, False otherwise
    """
    global EXIFTOOL_AVAILABLE, EXIFTOOL_PATH
    
    debug_startup("=== ExifTool Initialization ===")
    debug_startup(f"Platform: {platform.system()} {platform.architecture()[0]}")
    
    is_bundled = getattr(sys, 'frozen', False)
    debug_startup(f"PyInstaller bundle: {is_bundled}")
    
    # Reset global state
    EXIFTOOL_AVAILABLE = False
    EXIFTOOL_PATH = None
    
    if is_bundled:
        # Production PyInstaller build: Bundled first, system fallback
        debug_startup("Production mode: Checking bundled ExifTool first...")
        bundled_path = detect_bundled_exiftool()
        if bundled_path:
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = bundled_path
            debug_startup(f"🎯 Using bundled ExifTool: {bundled_path}")
            return True
        
        # Fallback to system
        debug_startup("Bundled ExifTool failed, trying system...")
        system_path = detect_system_exiftool()
        if system_path:
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = system_path
            debug_startup(f"🎯 Using system ExifTool: {system_path}")
            return True
    else:
        # Development mode: System first (faster), bundled fallback  
        debug_startup("Development mode: Checking system ExifTool first...")
        system_path = detect_system_exiftool()
        if system_path:
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = system_path
            debug_startup(f"🎯 Using system ExifTool: {system_path}")
            return True
            
        # Fallback to bundled (with timeout warning)
        debug_startup("System ExifTool not found, trying bundled (may be slow)...")
        bundled_path = detect_bundled_exiftool()
        if bundled_path:
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = bundled_path
            debug_startup(f"🎯 Using bundled ExifTool: {bundled_path}")
            return True
    
    # No ExifTool found
    debug_startup("❌ ExifTool not found in bundled package or system")
    debug_startup("   Please ensure ExifTool is installed or included in the build")
    EXIFTOOL_AVAILABLE = False
    EXIFTOOL_PATH = None
    return False

def get_exiftool_info():
    """
    Get current ExifTool status and path.
    
    Returns:
        dict: ExifTool status information
    """
    return {
        'available': EXIFTOOL_AVAILABLE,
        'path': EXIFTOOL_PATH,
        'platform': platform.system(),
        'is_bundled': getattr(sys, 'frozen', False)
    }