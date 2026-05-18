# Folder Manager Feature - Development Log

## Phase 1: Foundation ✅ COMPLETED

### Created Modules:

1. **path_mapper.py**
   - Cross-platform path handling
   - Converts between absolute and relative paths
   - Handles different mount points (macOS/Windows)
   - Path validation and normalization

2. **file_lock_manager.py**
   - Single-user access control
   - File-based locking mechanism
   - 10-minute inactivity timeout
   - Lock refresh and activity tracking

3. **folder_status_manager.py**
   - CSV database management
   - 6 status states: discarded, not_evaluated, requiring_tags, tagged_local, synced, not_found
   - Recursive folder operations
   - Mixed folder detection
   - Path remapping for moved folders
   - Image file type filtering

### Status Constants:
- `STATUS_DISCARDED` - Won't be processed
- `STATUS_NOT_EVALUATED` - Default for new files
- `STATUS_REQUIRING_TAGS` - Selected for tagging
- `STATUS_TAGGED_LOCAL` - Tagged but not uploaded
- `STATUS_SYNCED` - Tagged and uploaded to Cloudinary
- `STATUS_NOT_FOUND` - Missing from filesystem

### Supported Image Types:
.jpg, .jpeg, .png, .tiff, .tif, .webp, .heic, .heif, .raw, .cr2, .nef, .arw, .dng, .psd, .bmp, .gif

## Next: Phase 2 - Scanner & UI

### To Do:
1. folder_scanner.py - Directory scanning with lazy loading
2. folder_status_dialog.py - QDialog UI with tree view
3. Settings integration - Add network root path
4. Main window integration - Menu item and filtering

