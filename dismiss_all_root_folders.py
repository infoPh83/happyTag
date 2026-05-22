"""
dismiss_all_root_folders.py

One-time utility script to mark ALL top-level folders in the network root
as 'dismissed' in folder_status.csv.

Run from the project root:
    python3 dismiss_all_root_folders.py

This is safe to run multiple times — already-dismissed folders are skipped.
After running, launch HappyTag and use the Folder Manager to 'watch'
specific folders you want to sync.
"""

import sys
import os
import pickle
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Add project root to sys.path so we can import utilities
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Load settings from pickle
# ---------------------------------------------------------------------------
SETTINGS_PATH = Path.home() / ".happytag" / "settings.pkl"

def load_settings():
    if not SETTINGS_PATH.exists():
        print(f"ERROR: Settings file not found at {SETTINGS_PATH}")
        print("Please launch HappyTag at least once to create your settings.")
        sys.exit(1)
    with open(SETTINGS_PATH, "rb") as f:
        return pickle.load(f)

settings = load_settings()

network_root = settings.get("network_root_folder", "").strip()
log_folder   = settings.get("cloudinary_log_folder", "").strip()

if not network_root or not Path(network_root).is_dir():
    print(f"ERROR: network_root_folder is not set or does not exist: {network_root!r}")
    sys.exit(1)

print(f"Network root : {network_root}")
print(f"Log folder   : {log_folder or '(not set — will fall back to network root)'}")

# ---------------------------------------------------------------------------
# Resolve CSV path (mirrors FolderStatusManager logic)
# ---------------------------------------------------------------------------
CSV_FILENAME = "folder_status.csv"

if log_folder and Path(log_folder).is_dir():
    csv_path = Path(log_folder) / CSV_FILENAME
else:
    csv_path = Path(network_root) / CSV_FILENAME

print(f"CSV path     : {csv_path}")

# ---------------------------------------------------------------------------
# Import FolderStatusManager and batch-dismiss
# ---------------------------------------------------------------------------
from utilities.folder_status_manager import FolderStatusManager, STATUS_DISMISSED

mgr = FolderStatusManager(network_root, logs_folder=log_folder if log_folder else None)

# Load existing DB (creates it if it doesn't exist)
ok, msg = mgr.load_status_db()
if not ok:
    print(f"ERROR loading status DB: {msg}")
    sys.exit(1)

print(f"\nDB loaded: {msg}")
print(f"Existing entries: {len(mgr._status_cache)}")

# ---------------------------------------------------------------------------
# List top-level directories in network_root
# ---------------------------------------------------------------------------
top_level_dirs = sorted([
    p for p in Path(network_root).iterdir()
    if p.is_dir() and not p.name.startswith('.')
])

print(f"\nTop-level folders found: {len(top_level_dirs)}")

# ---------------------------------------------------------------------------
# Batch update: mark each top-level folder as dismissed in the cache
# (don't save after each — save once at the end)
# ---------------------------------------------------------------------------
now = datetime.now().isoformat()
added = 0
skipped = 0

for folder in top_level_dirs:
    rel_path = folder.name  # relative to network_root is just the folder name

    existing = mgr._status_cache.get(rel_path)
    if existing and existing.get("status") == STATUS_DISMISSED:
        skipped += 1
        continue  # already dismissed, leave it

    # Remove any existing children (mimics dismiss_folder behaviour)
    prefix = rel_path + "/"
    children = [k for k in list(mgr._status_cache.keys()) if k.startswith(prefix)]
    for child_key in children:
        del mgr._status_cache[child_key]

    # Add/overwrite the folder entry as dismissed
    mgr._status_cache[rel_path] = {
        'item_type': 'folder',
        'status': STATUS_DISMISSED,
        'cloudinary_id': '',
        'cloudinary_url': '',
        'original_size': '',
        'upload_size': '',
        'upload_date': '',
        'last_modified': now,
        'notes': 'Bulk-dismissed by dismiss_all_root_folders.py'
    }
    added += 1
    print(f"  dismissed: {rel_path}")

print(f"\nDismissed : {added}")
print(f"Skipped (already dismissed): {skipped}")

# ---------------------------------------------------------------------------
# Save once
# ---------------------------------------------------------------------------
if added > 0:
    ok, msg = mgr.save_status_db()
    if ok:
        print(f"\nSaved successfully to: {csv_path}")
    else:
        print(f"\nERROR saving: {msg}")
        sys.exit(1)
else:
    print("\nNothing to save — all folders were already dismissed.")

print("\nDone. Launch HappyTag and use Folder Manager to watch specific folders.")
