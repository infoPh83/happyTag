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
        
        if 'Debug' in app_name:
            if 'Verbose' in app_name:
                # Verbose debug build - enable ALL categories
                categories = "all"
                level = "VERBOSE"
                print(f"[RUNTIME_HOOK] VERBOSE debug mode enabled for {app_name}")
                print(f"[RUNTIME_HOOK] Categories: ALL")
                print(f"[RUNTIME_HOOK] Level: VERBOSE")
            elif 'Custom' in app_name:
                # ========== CUSTOM DEBUG CONFIGURATION ==========
                # Change these categories to whatever you want to debug:
                # Example options:
                # UI debugging: "layout,image_display,ui_events,layout_fix,width_control"
                # Cloudinary debugging: "cloudinary,business,upload,assessment,errors"
                # File processing: "file_ops,metadata,exiftool,tags,orientation"
                # Performance: "memory,timers,image_loading,temp_files"
                
                categories = "cloudinary,business,upload,assessment,errors,file_ops"
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