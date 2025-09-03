# HappyTag PyInstaller Specifications - Clean Organization

## Current .spec Files (Latest Versions)

### Windows Builds
- **`HappyTag_Win.spec`** - Windows Production Build
  - Clean GUI app, no console
  - Optimized with exclusions
  - Uses unified ExifTool approach (binaries section)

- **`HappyTag_Debug_Win.spec`** - Windows Debug Build  
  - Debug enabled, console visible
  - Minimal exclusions for better debugging
  - Uses unified ExifTool approach (binaries section)

### macOS Builds
- **`HappyTag_macOS.spec`** - macOS Production Build
  - Clean .app bundle, no console
  - Optimized with exclusions
  - Uses unified ExifTool approach (binaries section)

- **`HappyTag_Debug_macOS.spec`** - macOS Debug Build
  - Debug enabled, console visible  
  - Minimal exclusions for better debugging
  - Uses unified ExifTool approach (binaries section)

## Key Features of All Specs

### Unified ExifTool Handling
- **Executables** → `binaries` section (requires execute permissions)
  - Windows: `exiftool(-k).exe`
  - macOS: `exiftool` (Perl script)
- **Support files** → `datas` section (data only)
  - Windows: `exiftool_files/`
  - macOS: `lib/` directory

### Organized Folder Structure
All specs reference the clean folder organization:
```
utilities/          # Python modules package
ui/                 # UI files and forms
packages/           # External tools (ExifTool)
```

### Debug vs Production Differences
| Feature | Production | Debug |
|---------|------------|-------|
| Console | Hidden | Visible |
| Debug flag | False | True |
| Exclusions | Many (smaller build) | Minimal (better debugging) |
| Bundle ID | `com.happytag.app` | `com.happytag.debug.app` |

## Usage Commands

### Windows
```bash
# Production build
pyinstaller HappyTag_Win.spec

# Debug build  
pyinstaller HappyTag_Debug_Win.spec
```

### macOS
```bash
# Production build
pyinstaller HappyTag_macOS.spec

# Debug build
pyinstaller HappyTag_Debug_macOS.spec
```

## Archived Files
Outdated .spec files have been moved to `old_specs/` folder:
- `HappyTag_Win_clean.spec` (outdated ExifTool approach)
- `HappyTag_Debug_Win_clean.spec` (outdated ExifTool approach) 
- `HappyTag_macOS_Old.spec` (old messy version)
- `HappyTag_macOS_Clean.spec` (intermediate version)
- `HappyTag.spec` (empty)
- `HappyTag_debug.spec` (empty)

## File Status Summary
✅ **Current & Up-to-date**: 4 files (2 Windows + 2 macOS)
📁 **Archived**: 6 outdated files moved to `old_specs/`
🗑️ **Removed**: None (all preserved for reference)

Last updated: September 3, 2025
