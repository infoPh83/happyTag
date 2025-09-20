# Custom Debug Configuration Guide

## Quick Start: Create Your Own Debug Executable

### Step 1: Choose Your Debug Categories

First, look at all available categories in `utilities/debug_utils.py`:

```python
# Available Categories:
'image_display'     # Widget sizing, scaling, dimensions, colors
'layout'           # Flow layout, positioning, widget arrangement
'tags'             # Tag handling, metadata extraction, keywords
'metadata'         # ExifTool operations, file metadata reading
'cloudinary'       # Cloudinary API calls, sync operations, uploads
'assessment'       # Image assessment, Cloudinary sync status
'upload'           # Cloudinary upload phase, file transfers
'memory'           # Memory usage, resource monitoring
'timers'           # Timer operations, callbacks, cleanup
'ui_events'        # Mouse clicks, selections, user actions
'file_ops'         # File operations, processing workflow
'startup'          # Application initialization
'errors'           # Error conditions and exceptions
'image_loading'    # Image preview creation, PIL processing
'exiftool'         # ExifTool path detection, version checks
'layout_fix'       # Layout refresh operations, widget visibility fixes
'business'         # Business data loading, spreadsheet processing
'width_control'    # Text widget width maintenance and enforcement
'ctrl_operations'  # Ctrl key operation suppression and detection
'orientation'      # Image orientation correction, EXIF processing
'color_conversion' # ICC profile handling, color space conversion
'file_dialogs'     # File/folder dialog operations and selections
'tag_widgets'      # Tag button creation, color processing
'temp_files'       # Temporary file operations for image processing
```

### Step 2: Edit the Runtime Hook

Open `runtime_hook_debug.py` and find this section:

```python
elif 'Custom' in app_name:
    # ========== CUSTOM DEBUG CONFIGURATION ==========
    # Change these categories to whatever you want to debug:
    categories = "layout,tags,image_display,ui_events,file_ops"
    level = "INFO"
    # ================================================
```

**Replace the categories string with your choices:**

Examples:
```python
# For UI debugging:
categories = "layout,image_display,ui_events,layout_fix,width_control"

# For Cloudinary debugging:
categories = "cloudinary,business,upload,assessment,errors"

# For file processing debugging:
categories = "file_ops,metadata,exiftool,tags,orientation"

# For performance debugging:
categories = "memory,timers,image_loading,temp_files"

# Mix and match:
categories = "errors,startup,layout,cloudinary,file_ops"

# Enable everything except noisy ones:
categories = "all,-image_display,-ui_events"
```

### Step 3: Build Your Custom Executable

```powershell
# Navigate to your project
cd "D:\Python playfolder\happyTag"

# Build your custom debug version
pyinstaller HappyTag_CustomDebug_Win.spec
```

### Step 4: Run and Test

```powershell
# Your executable will be created as:
dist/HappyTag_CustomDebug_Win.exe

# Run it to see your debug output
./dist/HappyTag_CustomDebug_Win.exe
```

## Advanced: Create Multiple Custom Builds

### Option 1: Multiple Runtime Hook Sections

Add more conditions to `runtime_hook_debug.py`:

```python
elif 'Layout' in app_name:
    # Layout debugging build
    categories = "layout,image_display,layout_fix,width_control"
    level = "INFO"
elif 'Cloudinary' in app_name:
    # Cloudinary debugging build
    categories = "cloudinary,business,upload,assessment,errors"
    level = "VERBOSE"
elif 'Performance' in app_name:
    # Performance debugging build  
    categories = "memory,timers,image_loading,temp_files"
    level = "INFO"
```

### Option 2: Multiple .spec Files

Create separate spec files for different purposes:

1. **`HappyTag_LayoutDebug_Win.spec`** - for UI issues
2. **`HappyTag_CloudinaryDebug_Win.spec`** - for API issues  
3. **`HappyTag_PerformanceDebug_Win.spec`** - for speed issues

## Real Examples

### Example 1: UI Layout Debugging

**Edit `runtime_hook_debug.py`:**
```python
elif 'Layout' in app_name:
    categories = "layout,image_display,ui_events,layout_fix,width_control"
    level = "INFO"
```

**Create `HappyTag_LayoutDebug_Win.spec`:**
```python
name='HappyTag_LayoutDebug_Win',
```

**Build:**
```powershell
pyinstaller HappyTag_LayoutDebug_Win.spec
```

### Example 2: Cloudinary API Debugging

**Edit `runtime_hook_debug.py`:**
```python
elif 'Cloudinary' in app_name:
    categories = "cloudinary,business,upload,assessment,errors,file_ops"
    level = "VERBOSE"
```

**Create `HappyTag_CloudinaryDebug_Win.spec`:**
```python
name='HappyTag_CloudinaryDebug_Win',
```

### Example 3: Silent Production Build

**Edit `runtime_hook_debug.py`:**
```python
elif 'Production' in app_name:
    categories = ""  # Silent mode
    level = "INFO"
```

**Create `HappyTag_Production_Win.spec`:**
```python
name='HappyTag_Production_Win',
console=False,  # Hide console window
```

## Tips and Tricks

### Debug Levels:
- `"INFO"` - Standard debug messages
- `"VERBOSE"` - More detailed messages  
- `"TRACE"` - Everything (very noisy)

### Category Syntax:
- `"errors,startup"` - Enable specific categories
- `"all"` - Enable everything
- `"all,-image_display,-ui_events"` - Enable all except specified ones

### Console Window:
- `console=True` - Shows debug output (development)
- `console=False` - Hides console (production)

### Log Files:
Debug output is automatically saved to `happytag_debug.log` in the same folder as your executable.

## Troubleshooting

### No Debug Output?
1. Check the executable name matches your runtime hook condition
2. Ensure `console=True` in your .spec file
3. Look for `[RUNTIME_HOOK]` messages at startup

### Too Much Output?
1. Reduce the number of categories
2. Remove noisy categories like `image_display` or `ui_events`
3. Change level from `VERBOSE` to `INFO`

### Categories Not Working?
1. Check spelling in category names
2. Verify categories exist in `utilities/debug_utils.py`
3. Rebuild the executable after changes

## File Locations Summary

```
D:\Python playfolder\happyTag\
├── runtime_hook_debug.py           # ← Edit categories here
├── HappyTag_CustomDebug_Win.spec   # ← Your custom spec file
├── utilities/debug_utils.py        # ← All available categories
└── dist/
    └── HappyTag_CustomDebug_Win.exe # ← Your built executable
```