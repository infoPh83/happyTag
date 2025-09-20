# PyInstaller Debug Configuration Guide

## Overview
The `HappyTag_Debug_Win.spec` file has been configured to automatically enable debugging for startup categories when building with PyInstaller. This setup uses a runtime hook that configures debug settings based on the executable name.

## Current Configuration

### Modified Files:
1. **`HappyTag_Debug_Win.spec`**: Added runtime hook for debug configuration
2. **`runtime_hook_debug.py`**: Runtime hook that sets debug environment variables based on executable name

### Debug Categories Enabled:
When building with `HappyTag_Debug_Win.spec`, the following categories are automatically enabled:
- `startup`: Application initialization
- `errors`: Error conditions and exceptions
- `file_ops`: File operations and processing workflow
- `exiftool`: ExifTool binary operations and path detection
- `cloudinary`: Cloudinary API calls and sync operations
- `business`: Billing data and credit calculations

### Debug Configuration:
- **Debug Level**: INFO
- **Log File**: `happytag_debug.log` (created in the same directory as the executable)
- **Console Output**: Enabled (since `console=True` in the spec file)

## How It Works

### 1. Runtime Hook Detection
The `runtime_hook_debug.py` file:
- Detects if running as a PyInstaller executable (`sys.frozen`)
- Checks the executable name for debug indicators
- Sets environment variables before the main application loads

### 2. Executable Name Detection
- **`*Debug*`**: Enables debug categories listed above
- **`*Release*` or `*Prod*`**: Silent mode (no debug output)
- **Other names**: Basic mode (errors + startup only)

## Building the Debug Executable

```powershell
# Navigate to your project directory
cd "D:\Python playfolder\happyTag"

# Build the debug executable
pyinstaller HappyTag_Debug_Win.spec

# The executable will be in dist/HappyTag_Debug_Win.exe
```

## Testing Debug Output

After building, run the executable and check for:
1. **Console output**: Debug messages appearing in the console window
2. **Log file**: `happytag_debug.log` created in the same directory as the exe
3. **Runtime hook messages**: Look for `[RUNTIME_HOOK]` prefixed messages

## Customizing Debug Categories

### Option 1: Modify the Runtime Hook
Edit `runtime_hook_debug.py` to change the debug categories:

```python
# Change this line in runtime_hook_debug.py
categories = "startup,errors,file_ops,exiftool,cloudinary,business"

# To enable different categories, e.g.:
categories = "all"  # Enable everything
categories = "startup,errors,layout,tags"  # Specific categories
categories = "all,-upload,-image_display"  # All except noisy ones
```

### Option 2: Create Additional Spec Files
Create variations like:

**`HappyTag_Verbose_Win.spec`** (copy of debug spec with different name):
```python
name='HappyTag_Verbose_Win',  # This triggers different debug config
```

**`HappyTag_Silent_Win.spec`** (production build):
```python
name='HappyTag_Release_Win',  # This triggers silent mode
console=False,               # Hide console for production
```

## Available Debug Categories

You can use any of these categories in your configuration:

### Core Application:
- `startup`, `errors`, `ui_events`, `file_ops`

### Image Processing:
- `image_display`, `image_loading`, `layout`, `orientation`, `color_conversion`

### Metadata & Tags:
- `tags`, `metadata`, `exiftool`, `tag_widgets`

### Cloudinary Integration:
- `cloudinary`, `assessment`, `upload`, `business`

### Performance & System:
- `memory`, `timers`, `temp_files`

### UI & Layout:
- `layout_fix`, `width_control`, `file_dialogs`

## Example Configurations

### Minimal Debug (Errors Only)
```python
categories = "errors"
```

### Startup Debugging
```python
categories = "startup,errors,file_ops,exiftool"
```

### Full Cloudinary Debugging
```python
categories = "cloudinary,business,upload,assessment,errors"
```

### Everything Except Noisy Categories
```python
categories = "all,-image_display,-layout,-ui_events"
```

## Build Variations

### Quick Debug Build
```powershell
pyinstaller HappyTag_Debug_Win.spec
# Result: HappyTag_Debug_Win.exe with startup debugging
```

### Verbose Build (if you create the spec)
```powershell
pyinstaller HappyTag_Verbose_Win.spec
# Result: HappyTag_Verbose_Win.exe with all debugging
```

### Production Build
```powershell
pyinstaller HappyTag_Release_Win.spec
# Result: HappyTag_Release_Win.exe with no debugging
```

## Troubleshooting

### No Debug Output?
1. Check the executable name contains "Debug"
2. Look for `[RUNTIME_HOOK]` messages at startup
3. Check if `happytag_debug.log` is created
4. Verify `console=True` in the spec file

### Too Much Debug Output?
1. Reduce categories in `runtime_hook_debug.py`
2. Change level from "INFO" to a higher threshold
3. Remove noisy categories like `image_display` or `layout`

### Debug Not Working?
1. Ensure `runtime_hook_debug.py` is in the project root
2. Check that `runtime_hooks=['runtime_hook_debug.py']` is in the spec file
3. Rebuild the executable after any changes to the runtime hook