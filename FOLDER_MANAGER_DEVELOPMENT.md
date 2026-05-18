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

## Phase 2: Scanner ✅ COMPLETED

### Created Modules:

4. **folder_scanner.py**
   - Lazy loading directory scanner
   - Shallow scan (root folders only)
   - Deep scan on demand (recursive or single-level)
   - Discarded folder skipping during scans
   - Progress tracking with callbacks
   - Cancellation support
   - Image file filtering (12 extensions)
   - Size estimation for progress bars
   - FolderItem tree structure

**Tests:** 7/7 passing (test_folder_scanner.py)

## Phase 3: UI Dialog ✅ COMPLETED

### Created Modules:

5. **folder_status_dialog.py**
   - QDialog with QTreeWidget for folder hierarchy
   - Lazy loading - expand triggers scan_folder_contents()
   - Status management with color coding
   - Context menu for bulk operations
   - Deep scan (recursive) support
   - Progress dialogs for long operations
   - Search and status filtering
   - Expand/Collapse all functionality
   - Signal emission on status updates

**Tests:** 8/8 passing (test_folder_status_dialog.py)
**Total Tests:** 49/49 passing across all modules

### Status Constants:
- `STATUS_DISCARDED` - Won't be processed
- `STATUS_NOT_EVALUATED` - Default for new files
- `STATUS_REQUIRING_TAGS` - Selected for tagging
- `STATUS_TAGGED_LOCAL` - Tagged but not uploaded
- `STATUS_SYNCED` - Tagged and uploaded to Cloudinary
- `STATUS_NOT_FOUND` - Missing from filesystem

### Supported Image Types:
.jpg, .jpeg, .png, .tiff, .tif, .webp, .heic, .heif, .raw, .cr2, .nef, .arw, .dng, .psd, .bmp, .gif

## Next: Phase 4 - Settings & Main Window Integration

### To Do:
1. ✅ folder_scanner.py - Directory scanning with lazy loading **COMPLETED**
2. ✅ folder_status_dialog.py - QDialog UI with tree view **COMPLETED**
3. Settings integration - Add network root path **NEXT**
4. Main window integration - Menu item and filtering

