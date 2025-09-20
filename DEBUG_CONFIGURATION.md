# Debug Configuration Guide

## Overview
The debug system supports both environment variable and programmatic configuration. This is especially useful for PyInstaller builds where you want to control debug output at runtime.

## Environment Variable Configuration (Development)

### Basic Usage
```powershell
# Silent mode (no debug output)
$env:HAPPYTAG_DEBUG = ""

# Enable specific categories
$env:HAPPYTAG_DEBUG = "cloudinary,business,errors"

# Enable all categories
$env:HAPPYTAG_DEBUG = "all"

# Enable all except specific categories
$env:HAPPYTAG_DEBUG = "all,-cloudinary,-upload"

# Set debug level
$env:HAPPYTAG_DEBUG_LEVEL = "VERBOSE"  # INFO, VERBOSE, TRACE

# Enable file logging
$env:HAPPYTAG_DEBUG_FILE = "debug.log"
```

## Programmatic Configuration (PyInstaller/Production)

### Basic Examples
```python
from utilities.debug_utils import configure_debug_programmatically

# Silent mode for production
configure_debug_programmatically("")

# Enable only critical categories
configure_debug_programmatically("errors,startup")

# Enable specific categories for debugging
configure_debug_programmatically("cloudinary,business", "VERBOSE")

# Enable all with file logging
configure_debug_programmatically("all", "INFO", "app_debug.log")

# Enable all except noisy categories
configure_debug_programmatically("all,-upload,-image_display")
```

### PyInstaller Integration Example
```python
# main.py - Entry point for PyInstaller
import sys
from utilities.debug_utils import configure_debug_programmatically

def main():
    # Configure debug based on build type or command line args
    if "--debug" in sys.argv:
        configure_debug_programmatically("all", "VERBOSE", "happytag_debug.log")
    elif "--debug-errors" in sys.argv:
        configure_debug_programmatically("errors,startup")
    else:
        # Production mode - silent
        configure_debug_programmatically("")
    
    # Import and run your main application
    from main import run_app
    run_app()

if __name__ == "__main__":
    main()
```

### Runtime Configuration Inspection
```python
from utilities.debug_utils import get_debug_configuration

# Check current configuration
config = get_debug_configuration()
print(f"Enabled categories: {config['categories']}")
print(f"Debug level: {config['level']}")
print(f"Debug enabled: {config['enabled']}")
print(f"Log file: {config['log_file']}")
```

## Available Debug Categories

### Core Application
- `startup`: Application initialization
- `errors`: Error conditions (always recommended)
- `ui_events`: User interactions, mouse clicks
- `file_ops`: File operations, processing workflow

### Image Processing
- `image_display`: Widget sizing, scaling, dimensions
- `image_loading`: Image preview creation, PIL processing
- `layout`: Flow layout, positioning, widgets
- `orientation`: Image orientation correction
- `color_conversion`: ICC profile handling

### Metadata & Tags
- `tags`: Tag handling, metadata extraction
- `metadata`: ExifTool operations
- `exiftool`: ExifTool binary operations
- `tag_widgets`: Tag button creation

### Cloudinary Integration
- `cloudinary`: API calls, sync operations
- `assessment`: Image assessment, sync status
- `upload`: Upload phase, file transfers
- `business`: Billing data, credit calculations

### Performance & System
- `memory`: Memory usage monitoring
- `timers`: Timer operations, callbacks
- `temp_files`: Temporary file operations

### UI & Layout
- `layout_fix`: Layout refresh operations
- `width_control`: Text widget width maintenance
- `file_dialogs`: File/folder dialog operations

## Best Practices

### Development
- Use environment variables for quick testing
- Use `all,-noisy_category` to debug most things
- Use specific categories to focus on issues

### Production/PyInstaller
- Default to silent mode: `configure_debug_programmatically("")`
- Provide command line flags for debugging
- Log to file in production: `configure_debug_programmatically("errors", "INFO", "error.log")`
- Consider user-configurable debug levels

### Performance
- Silent mode has minimal overhead
- Avoid expensive debug message formatting when possible
- Use lambda functions for expensive debug operations: `debug("category", lambda: expensive_operation())`