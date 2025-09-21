# HappyTag Build Configurations Summary

## Windows Builds (3 configurations)

### 1. Production Build - `HappyTag_Win.spec`
- **Purpose**: Clean production build without console
- **Console**: Hidden (`console=False`)
- **Debug**: Disabled
- **Output**: `HappyTag.exe`
- **Features**: Optimized with UPX compression, no debug output

### 2. Standard Debug Build - `HappyTag_Debug_Win.spec`
- **Purpose**: Standard debug build with console
- **Console**: Enabled (`console=True`)
- **Debug Categories**: `startup,errors,file_ops,exiftool,cloudinary,business`
- **Output**: `HappyTag_Debug_Win.exe`
- **Features**: Full debug capabilities, disabled UPX for debugging

### 3. Verbose Debug Build - `HappyTag_VerboseDebug_Win.spec`
- **Purpose**: Maximum debug output with all categories
- **Console**: Enabled (`console=True`)
- **Debug Categories**: `all` (every available category)
- **Debug Level**: `VERBOSE`
- **Output**: `HappyTag_VerboseDebug_Win.exe`
- **Features**: Complete debug information, log file output

### 4. Custom Debug Build - `HappyTag_CustomDebug_Win.spec`
- **Purpose**: Specific debug categories for focused debugging
- **Console**: Enabled (`console=True`)
- **Debug Categories**: `upload,cloudinary,errors,assessment,file_ops,image_loading`
- **Output**: `HappyTag_CustomDebug_Win.exe`
- **Features**: Targeted debugging for Cloudinary and file operations

## macOS Builds (4 configurations)

### 1. Production Build - `HappyTag_macOS.spec`
- **Purpose**: Clean production build without console
- **Console**: Hidden (`console=False`)
- **Debug**: Disabled
- **Output**: `HappyTag.app`
- **Features**: Full macOS app bundle with proper permissions

### 2. Standard Debug Build - `HappyTag_Debug_macOS.spec`
- **Purpose**: Standard debug build with console
- **Console**: Enabled (`console=True`)
- **Debug Categories**: `startup,errors,file_ops,exiftool,cloudinary,business`
- **Output**: `HappyTag.app` (in debug mode)
- **Features**: Debug capabilities with macOS app structure

### 3. Verbose Debug Build - `HappyTag_VerboseDebug_macOS.spec`
- **Purpose**: Maximum debug output with all categories
- **Console**: Enabled (`console=True`)
- **Debug Categories**: `all` (every available category)
- **Debug Level**: `VERBOSE`
- **Output**: `HappyTag_VerboseDebug_macOS.app`
- **Features**: Complete debug information, log file output

### 4. Custom Debug Build - `HappyTag_CustomDebug_macOS.spec`
- **Purpose**: Specific debug categories for focused debugging
- **Console**: Enabled (`console=True`)
- **Debug Categories**: `upload,cloudinary,errors,assessment,file_ops,image_loading`
- **Output**: `HappyTag_CustomDebug_macOS.app`
- **Features**: Targeted debugging for Cloudinary and file operations

## Debug System Configuration

The debug system is controlled by `runtime_hook_debug.py` which:

1. **Detects build type** from executable/app name
2. **Sets environment variables** for debug categories
3. **Configures log levels** automatically
4. **Works cross-platform** (Windows .exe and macOS .app detection)

### Debug Categories Available
- `upload` - File upload operations
- `cloudinary` - Cloudinary API interactions
- `errors` - Error conditions and exceptions
- `assessment` - Image assessment and database operations
- `file_ops` - File operations, loading, saving
- `image_loading` - Image loading and processing
- `startup` - Application initialization
- `layout` - UI layout and positioning
- `tags` - Tag handling and metadata
- `metadata` - ExifTool operations
- `memory` - Memory usage monitoring
- `ui_events` - User interface events

## Build Commands

### Windows
```bash
# Production (no console)
pyinstaller HappyTag_Win.spec

# Standard Debug (console + basic debug)
pyinstaller HappyTag_Debug_Win.spec

# Verbose Debug (console + all debug)
pyinstaller HappyTag_VerboseDebug_Win.spec

# Custom Debug (console + specific categories)
pyinstaller HappyTag_CustomDebug_Win.spec
```

### macOS
```bash
# Production (no console)
pyinstaller HappyTag_macOS.spec

# Standard Debug (console + basic debug)
pyinstaller HappyTag_Debug_macOS.spec

# Verbose Debug (console + all debug)
pyinstaller HappyTag_VerboseDebug_macOS.spec

# Custom Debug (console + specific categories)
pyinstaller HappyTag_CustomDebug_macOS.spec
```

## Runtime Debug Configuration

The `runtime_hook_debug.py` automatically configures debug settings based on the executable name:

- **VerboseDebug**: Enables all categories with VERBOSE level
- **CustomDebug**: Enables specific categories: `upload,cloudinary,errors,assessment,file_ops,image_loading`
- **Debug**: Standard debug categories
- **Production**: No debug output (silent mode)