# HappyTag — Copilot Context

Keep this file up to date as the project evolves. Commit it so any device can pick up context.

---

## What this app does
PyQt5 desktop app for tagging images and uploading to Cloudinary, used by 3 users on a shared macOS network drive at `/Volumes/Marketing`.

## Key paths
- Network root: `/Volumes/Marketing` (configured per-user in settings)
- Settings: `/Users/<user>/.happytag/settings.pkl` (local, not shared)
- Folder status CSV: `{log_folder}/folder_status.csv` = `logs/folder_status.csv` (on network drive, shared)
- Python command on macOS: `python3`
- Venv: `.venv/bin/activate`

## CSV schema
`relative_path, item_type, status, cloudinary_id, cloudinary_url, original_size, upload_size, upload_date, last_modified, notes`

## Folder status constants (`utilities/folder_status_manager.py`)
| Constant | Value | Assignable by user? | Notes |
|---|---|---|---|
| `STATUS_DISMISSED` | `"dismissed"` | ✅ | Folder excluded from workflow |
| `STATUS_NEW` | `"new"` | ❌ auto | New folder, not yet reviewed |
| `STATUS_WATCHED` | `"watched"` | ✅ | Folder being monitored/scanned |
| `STATUS_NOT_FOUND` | `"not_found"` | ❌ auto | Missing from filesystem |
| `STATUS_PART_WATCHED` | `"part_watched"` | ❌ display-only | **Not stored in CSV.** Computed at render time: a dismissed folder that has ≥1 watched descendant. Shown amber in tree. |

## Key utilities
- `utilities/folder_status_manager.py` — CSV read/write, status tracking, folder seeding
  - `seed_folder_structure()` — first-launch: `os.walk` entire network root, adds all dirs as dismissed
  - `has_child_folders(rel_path)` — checks CSV cache for immediate children (no filesystem)
  - `get_immediate_child_folders(rel_path)` — returns child folders from CSV cache (no filesystem)
  - `has_watched_descendant(rel_path)` — checks if any descendant has `STATUS_WATCHED` (powers part_watched display)
  - `is_fresh_db` flag — `True` when CSV was just created (triggers first-launch seeding)
- `utilities/folder_status_dialog.py` — QDialog with QTreeWidget, lazy-loading folder tree
  - First launch: detects `is_fresh_db`, shows progress dialog, seeds all folders
  - Dismissed folders expand from CSV cache (zero filesystem hits)
  - Watched/New folders expand by scanning filesystem
  - Context menu: "Set Status" (Watched/Dismissed only) + "Re-scan Folder Structure" + "Deep Scan"
  - `STATUS_PART_WATCHED` computed in `_update_tree_item_status` — visual only, stored status stays dismissed
- `utilities/folder_scanner.py` — lazy directory scanner
- `utilities/cloudinary_upload_handler.py` — handles all Cloudinary uploads, writes to `folder_status.csv`
- `utilities/path_mapper.py` — cross-OS relative path handling (`path_mapper.network_root` is a `Path`)
- `utilities/file_lock_manager.py` — multi-user concurrent CSV access

## `STATUS_CONFIG` (`folder_status_dialog.py`)
Each entry has `label`, `color`, `description`, `user_assignable` (bool).
Only `user_assignable=True` statuses appear in the context menu.
`STATUS_PART_WATCHED` is in `STATUS_CONFIG` for color/label but `user_assignable=False`.

## Architecture: startup flow
```
App opens Folder Manager
  → load_status_db()
      → no CSV? is_fresh_db=True; create empty CSV
  → if is_fresh_db: _run_first_launch_seed() (progress dialog, os.walk all dirs → dismissed)
  → _collect_root_items() (CSV + filesystem merge for root level)
  → reconcile WATCHED root folders only
  → build tree

User expands dismissed folder  → get_immediate_child_folders() from CSV (no filesystem)
User expands watched folder    → scan filesystem, reconcile non-dismissed children
Right-click "Re-scan Folder Structure" → os.walk that folder, add new dirs as dismissed
Right-click "Set Status → Watched"    → status_manager.set_status(rel_path, STATUS_WATCHED)
Right-click "Set Status → Dismissed"  → status_manager.dismiss_folder(rel_path) (removes descendants)
Right-click "Deep Scan (Recursive)"   → full recursive image scan + reconcile
```

## Completed work (as of 2026-05-22)
1. ✅ Full `FolderStatusManager` / `FolderStatusDialog` / `CloudinaryUploadHandler` refactor
2. ✅ First-launch seeding: on first open (no CSV), seeds entire folder tree as dismissed
3. ✅ Tree fully browsable from day one; dismissed folders expand from CSV (no scanning)
4. ✅ Right-click "Re-scan Folder Structure" — adds new sub-folders as dismissed, no image scan
5. ✅ Context menu simplified: single "Set Status" with Watched/Dismissed only
6. ✅ `STATUS_PART_WATCHED`: amber display for dismissed folders that contain watched descendants
