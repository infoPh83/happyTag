# runtime_hook_debug.py
# PyInstaller runtime hook for debug configuration
# This file is executed before main.py when running as PyInstaller executable

import sys
import os

def configure_happytag_debug():
    """Configure HappyTag debug system for PyInstaller builds"""
    try:
        # Only configure if running as PyInstaller executable
        if not getattr(sys, 'frozen', False):
            return
        
        # Set environment variables for debug configuration
        # This approach works better with PyInstaller's import system
        app_name = os.path.basename(sys.executable)
        
        # For macOS apps, also check the app bundle name from environment or executable path
        if hasattr(sys, '_MEIPASS'):
            # Running from PyInstaller bundle
            bundle_path = os.path.dirname(os.path.dirname(sys.executable))
            if bundle_path.endswith('.app'):
                app_name = os.path.basename(bundle_path)
        
        print(f"[RUNTIME_HOOK] Detected app name: {app_name}")
        
        if 'Debug' in app_name or 'debug' in app_name:
            if 'Verbose' in app_name or 'verbose' in app_name:
                # Verbose debug build - enable ALL categories
                categories = "all"
                level = "VERBOSE"
                print(f"[RUNTIME_HOOK] VERBOSE debug mode enabled for {app_name}")
                print(f"[RUNTIME_HOOK] Categories: ALL")
                print(f"[RUNTIME_HOOK] Level: VERBOSE")
            elif 'Custom' in app_name or 'custom' in app_name:
                # ========== CUSTOM DEBUG CONFIGURATION ==========
                # Custom categories: upload, cloudinary, errors, assessment, file_ops, image_loading
                categories = "upload,cloudinary,errors,assessment,file_ops,image_loading"
                level = "INFO"
                print(f"[RUNTIME_HOOK] CUSTOM debug mode enabled for {app_name}")
                print(f"[RUNTIME_HOOK] Categories: {categories}")
                print(f"[RUNTIME_HOOK] Level: {level}")
                # ================================================
            else:
                # Standard debug build configuration
                categories = "startup,errors,file_ops,exiftool,cloudinary,business"
                level = "INFO"
                print(f"[RUNTIME_HOOK] Debug mode enabled for {app_name}")
                print(f"[RUNTIME_HOOK] Categories: {categories}")
                print(f"[RUNTIME_HOOK] Level: {level}")
            
            os.environ['HAPPYTAG_DEBUG'] = categories
            os.environ['HAPPYTAG_DEBUG_LEVEL'] = level
            os.environ['HAPPYTAG_DEBUG_FILE'] = 'happytag_debug.log'
            print(f"[RUNTIME_HOOK] Log file: happytag_debug.log")
            
        elif 'Release' in app_name or 'Prod' in app_name:
            # Production build - silent mode
            os.environ['HAPPYTAG_DEBUG'] = ''
            print(f"[RUNTIME_HOOK] Silent mode enabled for {app_name}")
            
        else:
            # Default debug configuration for other builds
            os.environ['HAPPYTAG_DEBUG'] = 'errors,startup'
            print(f"[RUNTIME_HOOK] Basic debug mode enabled for {app_name}")
            
    except Exception as e:
        # Fallback - don't let debug configuration break the app
        print(f"[RUNTIME_HOOK] Debug configuration failed: {e}")

# Configure debug system
configure_happytag_debug()