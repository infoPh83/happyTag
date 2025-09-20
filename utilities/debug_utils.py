# utilities/debug_utils.py
"""
Centralized debug system with configurable areas and levels.

Features added:
 - Category based enabling/disabling (existing)
 - Environment variable configuration (HAPPYTAG_DEBUG, HAPPYTAG_DEBUG_FILE, HAPPYTAG_DEBUG_LEVEL)
     * HAPPYTAG_DEBUG examples:
         - "all" -> enable all known categories
         - "layout,tags,metadata" -> enable listed
         - "all,-cloudinary" -> enable all then disable cloudinary
     * HAPPYTAG_DEBUG_LEVEL: INFO (default) | VERBOSE | TRACE
     * HAPPYTAG_DEBUG_FILE: path to append log output in addition to console
 - Single generic debug() API plus category helpers
 - Lazy message evaluation when a callable is passed (avoid expensive formatting when disabled)
 - Context manager debug_timer() to measure elapsed time in a category
 - Runtime category registration
"""

import os
from datetime import datetime
from contextlib import contextmanager
from typing import Callable, Dict, Optional

##############################
# Base configuration
##############################

# Debug configuration - default state (temporarily enabled for performance analysis)
DEBUG_CONFIG: Dict[str, bool] = {
    # Image display and widget management
    'image_display': True,    # Widget sizing, scaling, dimensions, colors
    'layout': True,           # Flow layout, positioning, widget arrangement

    # Content and metadata
    'tags': True,             # Tag handling, metadata extraction, keywords
    'metadata': True,         # ExifTool operations, file metadata reading

    # External services
    'cloudinary': True,       # Cloudinary API calls, sync operations, uploads
    
    # Analysis and processing
    'assessment': True,       # Image assessment, Cloudinary sync status
    'upload': True,           # Cloudinary upload phase, file transfers

    # Performance and resources
    'memory': True,           # Memory usage, resource monitoring
    'timers': True,           # Performance timing analysis, QTimer operations, callbacks
    'timings': True,          # Detailed upload phase timing breakdown and reports

    # User interactions
    'ui_events': True,        # Mouse clicks, selections, user actions
    
    # Application workflow
    'file_ops': True,         # File operations, processing workflow

    # System level
    'startup': True,          # Application initialization
    'errors': True,           # Error conditions and exceptions (always forced)
    
    # NEW CATEGORIES - previously uncategorized debug outputs
    'image_loading': False,   # Image preview creation, PIL processing, QPixmap conversion
    'exiftool': False,        # ExifTool path detection, version checks, binary operations
    'layout_fix': False,     # Layout refresh operations, widget visibility fixes
    'business': False,        # Business data loading, spreadsheet processing
    'width_control': False,  # Text widget width maintenance and enforcement
    'ctrl_operations': False, # Ctrl key operation suppression and detection
    'orientation': False,    # Image orientation correction, EXIF processing
    'color_conversion': False, # ICC profile handling, color space conversion
    'file_dialogs': False,   # File/folder dialog operations and selections
    'tag_widgets': False,    # Tag button creation, color processing
    'temp_files': False,     # Temporary file operations for image processing
}

# Global debug state & levels
_debug_enabled: bool = True

# Severity / verbosity levels (numeric for simple comparison)
_LEVELS = {"INFO": 1, "VERBOSE": 2, "TRACE": 3}
_current_level_name = os.environ.get("HAPPYTAG_DEBUG_LEVEL", "INFO").upper()
_current_level = _LEVELS.get(_current_level_name, 1)

_log_file_path: Optional[str] = None
_log_file_handle = None

def _open_log_file_if_needed():
    global _log_file_handle
    if _log_file_handle is None and _log_file_path:
        try:
            _log_file_handle = open(_log_file_path, 'a', encoding='utf-8')
        except Exception:
            # Fallback silently if file can't be opened
            pass

def set_level(level: str):
    """Set current debug verbosity level (INFO|VERBOSE|TRACE)."""
    global _current_level, _current_level_name
    level_u = level.upper()
    if level_u in _LEVELS:
        _current_level_name = level_u
        _current_level = _LEVELS[level_u]
        # Avoid circular dependency by using print directly during early initialization
        print(f"[STARTUP] Debug level set to {_current_level_name}")
    else:
        print(f"[ERROR] Unknown debug level: {level}")

def register_category(name: str, enabled: bool = False):
    """Register a new debug category at runtime if it does not exist."""
    if name not in DEBUG_CONFIG:
        DEBUG_CONFIG[name] = enabled

def enable_categories(*names: str):
    for name in names:
        if name in DEBUG_CONFIG:
            DEBUG_CONFIG[name] = True
        else:
            register_category(name, True)

def disable_categories(*names: str):
    for name in names:
        if name in DEBUG_CONFIG and name != 'errors':  # never disable errors via this path
            DEBUG_CONFIG[name] = False

def parse_env_configuration():
    """Parse environment variables to adjust debug configuration dynamically."""
    global _log_file_path
    env_spec = os.environ.get('HAPPYTAG_DEBUG')
    
    # Handle silent mode: if HAPPYTAG_DEBUG is not set or empty, disable all categories
    if env_spec is None or env_spec == "":
        # Silent mode - disable all categories for performance testing
        for k in DEBUG_CONFIG.keys():
            DEBUG_CONFIG[k] = False
    else:
        # When environment variable is set, start from disabled state and only enable specified categories
        # This ensures clean selective debugging
        for k in DEBUG_CONFIG.keys():
            DEBUG_CONFIG[k] = False
        
        # Parse non-empty environment variable
        tokens = [t.strip() for t in env_spec.split(',') if t.strip()]
        apply_all = any(t.lower() == 'all' or t == '*' for t in tokens)
        if apply_all:
            for k in DEBUG_CONFIG.keys():
                DEBUG_CONFIG[k] = True
        else:
            for tok in tokens:
                if tok.lower() in ('all', '*'):
                    continue
                if tok.startswith('-'):
                    disable_categories(tok[1:])
                else:
                    enable_categories(tok)
                
    # Level override already captured at import time but allow re-parse
    lvl = os.environ.get('HAPPYTAG_DEBUG_LEVEL')
    if lvl:
        set_level(lvl)
    # Log file
    log_path = os.environ.get('HAPPYTAG_DEBUG_FILE')
    if log_path:
        _log_file_path = log_path
        _open_log_file_if_needed()
        if _log_file_handle:
            print(f"[STARTUP] File logging enabled: {_log_file_path}")  # Simple print to avoid circular dependency

parse_env_configuration()

def configure_debug_programmatically(categories: str = "", level: str = "INFO", log_file: str = ""):
    """
    Configure debug settings programmatically, bypassing environment variables.
    
    This is especially useful for PyInstaller builds where you want to set debug
    configuration at runtime without relying on environment variables.
    
    Args:
        categories (str): Debug categories to enable, same format as HAPPYTAG_DEBUG:
                         - "" or None: Silent mode (disable all)
                         - "all": Enable all categories
                         - "layout,tags,metadata": Enable specific categories
                         - "all,-cloudinary": Enable all except cloudinary
        level (str): Debug level ("INFO", "VERBOSE", "TRACE")
        log_file (str): Optional file path for logging output
    
    Examples:
        # Silent mode for production builds
        configure_debug_programmatically("")
        
        # Enable only specific categories
        configure_debug_programmatically("errors,startup")
        
        # Enable all with file logging
        configure_debug_programmatically("all", "VERBOSE", "debug.log")
    """
    global _log_file_path
    
    # Reset all categories to disabled first
    for k in DEBUG_CONFIG.keys():
        DEBUG_CONFIG[k] = False
    
    # Apply category configuration
    if categories is None or categories == "":
        # Silent mode - all categories already disabled above
        pass
    else:
        # Parse category specification
        tokens = [t.strip() for t in categories.split(',') if t.strip()]
        apply_all = any(t.lower() == 'all' or t == '*' for t in tokens)
        
        if apply_all:
            # Enable all categories first
            for k in DEBUG_CONFIG.keys():
                DEBUG_CONFIG[k] = True
        
        # Process individual tokens
        for tok in tokens:
            if tok.lower() in ('all', '*'):
                continue
            elif tok.startswith('-'):
                # Disable specific category
                category = tok[1:]
                if category in DEBUG_CONFIG and category != 'errors':
                    DEBUG_CONFIG[category] = False
            else:
                # Enable specific category
                enable_categories(tok)
    
    # Set debug level
    if level:
        set_level(level)
    
    # Configure log file
    if log_file:
        _log_file_path = log_file
        _open_log_file_if_needed()
        if _log_file_handle:
            debug_print('startup', f"Programmatic file logging enabled: {_log_file_path}")

def get_debug_configuration():
    """
    Get the current debug configuration for inspection.
    
    Returns:
        dict: Contains 'categories', 'level', 'enabled', and 'log_file' keys
    """
    enabled_categories = [k for k, v in DEBUG_CONFIG.items() if v]
    return {
        'categories': enabled_categories,
        'level': _current_level_name,
        'enabled': _debug_enabled,
        'log_file': _log_file_path
    }

def set_debug_state(enabled: bool):
    """Enable or disable all debug output globally"""
    global _debug_enabled
    _debug_enabled = enabled

def is_debug_enabled(category: str, *, level: str = "INFO") -> bool:
    """Check if debug is enabled for a specific category at the given level."""
    if not _debug_enabled:
        return False
    if not DEBUG_CONFIG.get(category, False) and category != 'errors':
        return False
    lvl_value = _LEVELS.get(level.upper(), 1)
    return lvl_value <= _current_level

def debug_print(category: str, message: str, force: bool = False, *, level: str = "INFO"):
    """Low-level printing helper (kept for backward compatibility)."""
    if force or is_debug_enabled(category, level=level):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] [{level}] [{category.upper()}] {message}"
        print(formatted)
        if _log_file_handle:
            try:
                _log_file_handle.write(formatted + '\n')
                _log_file_handle.flush()
            except Exception:
                pass

def debug(category: str, message: "str | Callable[[], str]", *, level: str = "INFO", force: bool = False):
    """Generic debug function.

    message may be a string or a zero-arg callable for lazy evaluation.
    """
    if not (force or is_debug_enabled(category, level=level)):
        return
    if callable(message):  # type: ignore
        try:
            message = message()  # type: ignore
        except Exception as e:  # Fallback if callable fails
            message = f"<lazy message error: {e}>"  # type: ignore
    debug_print(category, str(message), force=True, level=level)

def debug_image_display(message: str, *, level: str = "INFO"):
    debug('image_display', message, level=level)

def debug_layout(message: str, *, level: str = "INFO"):
    debug('layout', message, level=level)

def debug_tags(message: str, *, level: str = "INFO"):
    debug('tags', message, level=level)

def debug_metadata(message: str, *, level: str = "INFO"):
    debug('metadata', message, level=level)

def debug_cloudinary(message: str, *, level: str = "INFO"):
    debug('cloudinary', message, level=level)

def debug_assessment(message: str, *, level: str = "INFO"):
    debug('assessment', message, level=level)

def debug_upload(message: str, *, level: str = "INFO"):
    debug('upload', message, level=level)

def debug_memory(message: str, *, level: str = "INFO"):
    debug('memory', message, level=level)

def debug_timers(message: str, *, level: str = "INFO"):
    debug('timers', message, level=level)

def debug_timings(message: str, *, level: str = "INFO"):
    debug('timings', message, level=level)

def debug_ui_events(message: str, *, level: str = "INFO"):
    debug('ui_events', message, level=level)

def debug_file_ops(message: str, *, level: str = "INFO"):
    debug('file_ops', message, level=level)

def debug_startup(message: str, *, level: str = "INFO"):
    debug('startup', message, level=level)

def debug_errors(message: str, *, level: str = "INFO"):
    debug('errors', message, level=level, force=True)

# NEW DEBUG FUNCTIONS for previously uncategorized outputs
def debug_image_loading(message: str, *, level: str = "INFO"):
    debug('image_loading', message, level=level)

def debug_exiftool(message: str, *, level: str = "INFO"):
    debug('exiftool', message, level=level)

def debug_layout_fix(message: str, *, level: str = "INFO"):
    debug('layout_fix', message, level=level)

def debug_width_control(message: str, *, level: str = "INFO"):
    debug('width_control', message, level=level)

def debug_ctrl_operations(message: str, *, level: str = "INFO"):
    debug('ctrl_operations', message, level=level)

def debug_orientation(message: str, *, level: str = "INFO"):
    debug('orientation', message, level=level)

def debug_color_conversion(message: str, *, level: str = "INFO"):
    debug('color_conversion', message, level=level)

def debug_file_dialogs(message: str, *, level: str = "INFO"):
    debug('file_dialogs', message, level=level)

def debug_tag_widgets(message: str, *, level: str = "INFO"):
    debug('tag_widgets', message, level=level)

def debug_temp_files(message: str, *, level: str = "INFO"):
    debug('temp_files', message, level=level)

@contextmanager
def debug_timer(category: str, label: str, *, level: str = "VERBOSE"):
    """Context manager to time a block of code.

    Example:
        with debug_timer('layout', 'refresh widgets'):
            self._refresh()
    """
    if not is_debug_enabled(category, level=level):
        yield
        return
    start = datetime.now()
    debug(category, f"⏱ START {label}", level=level)
    try:
        yield
    finally:
        elapsed = (datetime.now() - start).total_seconds() * 1000.0
        debug(category, f"⏱ END {label} ({elapsed:.2f} ms)", level=level)

def configure_debug(**kwargs):
    """Configure debug settings for specific categories.

    Example:
        configure_debug(image_display=False, cloudinary=True, tags=True)
    """
    for category, enabled in kwargs.items():
        if category not in DEBUG_CONFIG:
            register_category(category, enabled)
        else:
            DEBUG_CONFIG[category] = enabled
        debug_print('startup', f"Debug {category}: {'enabled' if enabled else 'disabled'}")

def get_debug_status():
    """Return current debug configuration and level."""
    return {
        'global_enabled': _debug_enabled,
        'level': _current_level_name,
        'categories': DEBUG_CONFIG.copy(),
        'log_file': _log_file_path
    }

def print_debug_status():
    """Print current debug configuration."""
    status = get_debug_status()
    debug_print('startup', "=== Debug Configuration ===", force=True)
    debug_print('startup', f"Global debug: {'enabled' if status['global_enabled'] else 'disabled'}", force=True)
    debug_print('startup', f"Level: {status['level']}", force=True)
    if status.get('log_file'):
        debug_print('startup', f"Log file: {status['log_file']}", force=True)
    enabled_categories = [cat for cat, enabled in status['categories'].items() if enabled]
    disabled_categories = [cat for cat, enabled in status['categories'].items() if not enabled]
    if enabled_categories:
        debug_print('startup', f"Enabled: {', '.join(enabled_categories)}", force=True)
    if disabled_categories:
        debug_print('startup', f"Disabled: {', '.join(disabled_categories)}", force=True)
    debug_print('startup', "=" * 30, force=True)

# Initialize debug system
if __name__ == "__main__":
    # Quick test of the debug system
    print_debug_status()
    
    debug_image_display("Testing image display debug")
    debug_cloudinary("Testing cloudinary debug (should be disabled)")
    debug_errors("Testing error debug (always shows)")
    
    # Test configuration
    configure_debug(cloudinary=True, image_display=False)
    debug_image_display("This should not show")
    debug_cloudinary("This should now show")