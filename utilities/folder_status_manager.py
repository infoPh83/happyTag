"""
Folder Status Manager - Core logic for folder/file status tracking

Manages CSV database of folder and file statuses, handles inheritance,
detects mixed folder states, and provides status operations with file locking.

Author: HappyTag Development Team
Date: May 2026
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from utilities.debug_utils import debug
from utilities.path_mapper import PathMapper
from utilities.file_lock_manager import FileLockManager


# Status constants for FOLDERS
STATUS_DISMISSED = "dismissed"
STATUS_NEW = "new"
STATUS_WATCHED = "watched"
STATUS_NOT_FOUND = "not_found"
STATUS_PART_WATCHED = "part_watched"  # auto-computed: dismissed folder with at least one watched descendant

# Status constants for FILES (in watched folders)
FILE_STATUS_ON_CLOUD = "on_cloud"
FILE_STATUS_DISMISSED = "dismissed"
FILE_STATUS_NEW = "new"
FILE_STATUS_NOT_FOUND = "not_found"

ALL_STATUSES = [
    STATUS_DISMISSED,
    STATUS_NEW,
    STATUS_WATCHED,
    STATUS_NOT_FOUND,
    STATUS_PART_WATCHED,
]

ALL_FILE_STATUSES = [
    FILE_STATUS_ON_CLOUD,
    FILE_STATUS_DISMISSED,
    FILE_STATUS_NEW,
    FILE_STATUS_NOT_FOUND
]

# All valid status values (folders + files combined for validation)
ALL_VALID_STATUSES = set(ALL_STATUSES + ALL_FILE_STATUSES)

# Supported image file extensions
SUPPORTED_IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tiff', '.tif',
    '.webp', '.heic', '.heif', '.raw', '.cr2',
    '.nef', '.arw', '.dng', '.psd', '.bmp',
    '.gif'
}


class FolderStatusManager:
    """
    Manages folder and file status database (CSV) with locking support.
    
    CSV Structure:
    relative_path,item_type,status,last_modified,cloudinary_id,date_tagged,date_synced,notes
    
    item_type: 'folder' or 'file'
    status for folders: dismissed, new, watched, not_found
    status for files in watched folders: on_cloud, dismissed, new, not_found
    """
    
    CSV_FILENAME = "folder_status.csv"
    CSV_HEADERS = [
        'relative_path',
        'item_type',  # 'folder' or 'file'
        'status',
        'cloudinary_id',
        'cloudinary_url',
        'original_size',
        'upload_size',
        'upload_date',
        'last_modified',
        'notes'
    ]
    
    def __init__(self, network_root: str, logs_folder: str = None):
        """
        Initialize the status manager.
        
        Args:
            network_root: Root directory of the network drive
            logs_folder: Optional folder for the CSV file. If None, auto-detected from settings.
        """
        self.path_mapper = PathMapper(network_root)
        self.lock_manager = FileLockManager(network_root)
        
        # Determine CSV location: prefer logs_folder, fallback to settings, then network_root
        resolved_logs = logs_folder
        if resolved_logs is None:
            try:
                from utilities.settings_dialog import SettingsDialog
                settings = SettingsDialog.get_cloudinary_settings()
                candidate = settings.get('log_folder', '').strip()
                if candidate and Path(candidate).is_dir():
                    resolved_logs = candidate
            except Exception:
                pass
        
        if resolved_logs and Path(resolved_logs).is_dir():
            self.csv_path = Path(resolved_logs) / self.CSV_FILENAME
        else:
            self.csv_path = Path(network_root) / self.CSV_FILENAME
        
        # In-memory cache of status data
        self._status_cache: Dict[str, Dict] = {}
        self._cache_loaded = False
        self.is_fresh_db = False  # True only when CSV was just created (first launch)
        
        debug("folder_status", f"FolderStatusManager initialized: csv={self.csv_path}")
    
    def load_status_db(self) -> Tuple[bool, str]:
        """
        Load status database from CSV file into memory.
        
        Returns:
            Tuple of (success, message)
        """
        debug("folder_status", "Loading status database")
        
        try:
            if not self.csv_path.exists():
                debug("folder_status", "CSV file does not exist, creating new")
                self._create_csv_file()
                self._status_cache = {}
                self._cache_loaded = True
                self.is_fresh_db = True
                return True, "New status database created"
            
            # Read CSV file
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self._status_cache = {}
                migrated_count = 0
                
                for row in reader:
                    rel_path = row['relative_path']
                    status = row['status']
                    
                    # Get item_type, default to 'folder' for backward compatibility
                    item_type = row.get('item_type', 'folder')
                    
                    # Migrate legacy statuses
                    if status == 'not_evaluated':
                        status = STATUS_WATCHED
                        migrated_count += 1
                        debug("folder_status", f"Migrated {rel_path}: not_evaluated -> watched")
                    elif status == 'discarded':
                        status = STATUS_DISMISSED
                        migrated_count += 1
                        debug("folder_status", f"Migrated {rel_path}: discarded -> dismissed")
                    
                    self._status_cache[rel_path] = {
                        'item_type': item_type,
                        'status': status,
                        'cloudinary_id': row.get('cloudinary_id', ''),
                        'cloudinary_url': row.get('cloudinary_url', ''),
                        'original_size': row.get('original_size', ''),
                        'upload_size': row.get('upload_size', ''),
                        'upload_date': row.get('upload_date', ''),
                        'last_modified': row.get('last_modified', ''),
                        'notes': row.get('notes', '')
                    }
            
            self._cache_loaded = True
            count = len(self._status_cache)
            
            # Save immediately if migrations were performed
            if migrated_count > 0:
                debug("folder_status", f"Migrated {migrated_count} entries, saving database")
                self.save_status_db()
            
            debug("folder_status", f"Loaded {count} entries from CSV")
            return True, f"Loaded {count} entries" + (f" (migrated {migrated_count})" if migrated_count > 0 else "")
            
        except Exception as e:
            msg = f"Failed to load status database: {e}"
            debug("errors", msg)
            return False, msg
    
    def save_status_db(self) -> Tuple[bool, str]:
        """
        Save status database from memory to CSV file.
        
        Returns:
            Tuple of (success, message)
        """
        debug("folder_status", "Saving status database")
        
        try:
            # Write to temporary file first
            temp_path = self.csv_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
                
                for rel_path, data in self._status_cache.items():
                    writer.writerow({
                        'relative_path': rel_path,
                        'item_type': data.get('item_type', 'folder'),
                        'status': data['status'],
                        'cloudinary_id': data.get('cloudinary_id', ''),
                        'cloudinary_url': data.get('cloudinary_url', ''),
                        'original_size': data.get('original_size', ''),
                        'upload_size': data.get('upload_size', ''),
                        'upload_date': data.get('upload_date', ''),
                        'last_modified': data.get('last_modified', ''),
                        'notes': data.get('notes', '')
                    })
            
            # Replace original file with temp file
            temp_path.replace(self.csv_path)
            
            count = len(self._status_cache)
            debug("folder_status", f"Saved {count} entries to CSV")
            return True, f"Saved {count} entries"
            
        except Exception as e:
            msg = f"Failed to save status database: {e}"
            debug("errors", msg)
            return False, msg
    
    def get_status(self, relative_path: str) -> str:
        """
        Get status for a path.
        
        Args:
            relative_path: Path relative to network root
            
        Returns:
            Status string, or STATUS_NEW if not found
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        # Normalize path
        rel_path = self.path_mapper.normalize_path(relative_path)
        
        if rel_path in self._status_cache:
            status = self._status_cache[rel_path]['status']
            debug("folder_status", f"get_status: {rel_path} -> {status}")
            return status
        
        # Check if path exists on filesystem
        if not self.path_mapper.exists(rel_path):
            debug("folder_status", f"get_status: {rel_path} -> {STATUS_NOT_FOUND}")
            return STATUS_NOT_FOUND
        
        debug("folder_status", f"get_status: {rel_path} -> {STATUS_NEW} (default)")
        return STATUS_NEW
    
    def set_status(self, relative_path: str, status: str, 
                   cloudinary_id: str = "", notes: str = "") -> Tuple[bool, str]:
        """
        Set status for a path.
        
        Args:
            relative_path: Path relative to network root
            status: Status to set
            cloudinary_id: Optional Cloudinary ID
            notes: Optional notes
            
        Returns:
            Tuple of (success, message)
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        if status not in ALL_VALID_STATUSES:
            msg = f"Invalid status: {status}"
            debug("errors", msg)
            return False, msg
        
        # Normalize path
        rel_path = self.path_mapper.normalize_path(relative_path)
        
        now = datetime.now().isoformat()
        
        # Preserve existing cloudinary fields if not explicitly overriding
        existing = self._status_cache.get(rel_path, {})
        
        # Update cache
        self._status_cache[rel_path] = {
            'item_type': existing.get('item_type', 'folder'),
            'status': status,
            'cloudinary_id': cloudinary_id or existing.get('cloudinary_id', ''),
            'cloudinary_url': existing.get('cloudinary_url', ''),
            'original_size': existing.get('original_size', ''),
            'upload_size': existing.get('upload_size', ''),
            'upload_date': existing.get('upload_date', ''),
            'last_modified': now,
            'notes': notes or existing.get('notes', '')
        }
        
        debug("folder_status", f"set_status: {rel_path} -> {status}")
        
        # Save to disk
        return self.save_status_db()
    
    def set_folder_recursive(self, relative_path: str, status: str, 
                            scan_filesystem: bool = True) -> Tuple[bool, str, int]:
        """
        Set status for a folder and all its contents recursively.
        
        Args:
            relative_path: Folder path relative to network root
            status: Status to set
            scan_filesystem: If True, scan filesystem for actual files/folders
            
        Returns:
            Tuple of (success, message, count_updated)
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        debug("folder_status", f"set_folder_recursive: {relative_path} -> {status}")
        
        # Normalize path
        rel_path = self.path_mapper.normalize_path(relative_path)
        
        # Set status for the folder itself
        self.set_status(rel_path, status)
        
        count = 1  # Count the folder itself
        
        # Find all children in cache and update them
        prefix = rel_path + '/'
        for cached_path in list(self._status_cache.keys()):
            if cached_path.startswith(prefix):
                self.set_status(cached_path, status)
                count += 1
        
        # If scan_filesystem is True, also scan and add any files not in cache
        if scan_filesystem:
            abs_path = self.path_mapper.to_absolute(rel_path)
            if os.path.exists(abs_path) and os.path.isdir(abs_path):
                for root, dirs, files in os.walk(abs_path):
                    # Process files
                    for filename in files:
                        if self.is_image_file(filename):
                            file_abs = os.path.join(root, filename)
                            file_rel = self.path_mapper.to_relative(file_abs)
                            if file_rel and file_rel not in self._status_cache:
                                self.set_status(file_rel, status)
                                count += 1
                    
                    # Process directories
                    for dirname in dirs:
                        dir_abs = os.path.join(root, dirname)
                        dir_rel = self.path_mapper.to_relative(dir_abs)
                        if dir_rel and dir_rel not in self._status_cache:
                            self.set_status(dir_rel, status)
                            count += 1
        
        # Save changes
        success, msg = self.save_status_db()
        
        debug("folder_status", f"Updated {count} items recursively")
        return success, f"Updated {count} items", count
    
    def get_folder_status_summary(self, relative_path: str) -> Dict[str, int]:
        """
        Get summary of statuses for all items in a folder.
        
        Args:
            relative_path: Folder path relative to network root
            
        Returns:
            Dictionary with status counts
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        # Normalize path
        rel_path = self.path_mapper.normalize_path(relative_path)
        prefix = rel_path + '/'
        
        # Count statuses of direct children only
        summary = {status: 0 for status in ALL_STATUSES}
        
        for cached_path, data in self._status_cache.items():
            if cached_path.startswith(prefix):
                # Check if it's a direct child (no more slashes after prefix)
                remainder = cached_path[len(prefix):]
                if '/' not in remainder:
                    status = data['status']
                    summary[status] = summary.get(status, 0) + 1
        
        debug("folder_status", f"Folder summary for {rel_path}: {summary}")
        return summary
    
    def is_folder_mixed(self, relative_path: str) -> bool:
        """
        Check if a folder has children with different statuses.
        
        Args:
            relative_path: Folder path relative to network root
            
        Returns:
            True if folder has mixed statuses, False otherwise
        """
        summary = self.get_folder_status_summary(relative_path)
        
        # Count how many different statuses are present
        non_zero_statuses = sum(1 for count in summary.values() if count > 0)
        
        is_mixed = non_zero_statuses > 1
        debug("folder_status", f"is_folder_mixed: {relative_path} -> {is_mixed}")
        return is_mixed
    
    def get_all_paths_with_status(self, status: str) -> List[str]:
        """
        Get all paths that have a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of relative paths
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        paths = [
            rel_path for rel_path, data in self._status_cache.items()
            if data['status'] == status
        ]
        
        debug("folder_status", f"Found {len(paths)} paths with status {status}")
        return paths
    
    def is_image_file(self, filename: str) -> bool:
        """
        Check if a filename is a supported image type.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if supported image type, False otherwise
        """
        ext = Path(filename).suffix.lower()
        is_img = ext in SUPPORTED_IMAGE_EXTENSIONS
        return is_img
    
    def mark_as_not_found(self, relative_path: str) -> Tuple[bool, str]:
        """
        Mark a path as not found (missing from filesystem).
        
        Args:
            relative_path: Path relative to network root
            
        Returns:
            Tuple of (success, message)
        """
        return self.set_status(relative_path, STATUS_NOT_FOUND, 
                              notes=f"Not found as of {datetime.now().isoformat()}")
    
    def remap_path(self, old_path: str, new_path: str) -> Tuple[bool, str]:
        """
        Remap a path that has been moved or renamed.
        
        Args:
            old_path: Old relative path
            new_path: New relative path
            
        Returns:
            Tuple of (success, message)
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        old_normalized = self.path_mapper.normalize_path(old_path)
        new_normalized = self.path_mapper.normalize_path(new_path)
        
        if old_normalized not in self._status_cache:
            return False, f"Path not found in database: {old_path}"
        
        # Move the entry
        self._status_cache[new_normalized] = self._status_cache[old_normalized]
        del self._status_cache[old_normalized]
        
        # Update timestamp
        self._status_cache[new_normalized]['last_modified'] = datetime.now().isoformat()
        
        debug("folder_status", f"Remapped: {old_path} -> {new_path}")
        
        return self.save_status_db()
    
    def _create_csv_file(self):
        """Create a new CSV file with headers."""
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
        debug("folder_status", f"Created new CSV file: {self.csv_path}")
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the status database.
        
        Returns:
            Dictionary with statistics
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        stats = {
            'total_entries': len(self._status_cache),
            'by_status': {status: 0 for status in ALL_STATUSES}
        }
        
        for data in self._status_cache.values():
            status = data['status']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        debug("folder_status", f"Statistics: {stats}")
        return stats
    
    def reconcile_folder_with_filesystem(self, folder_rel_path: str, progress_callback=None):
        """
        Reconcile a folder between filesystem and repository.
        Implements all 5 scenarios for folder status management.
        
        Args:
            folder_rel_path: Relative path to the folder
            progress_callback: Optional callback(current, total, message) for progress updates
            
        Returns:
            Dict with keys: total_images, on_cloud, dismissed, new, folders, status
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        absolute_path = self.path_mapper.to_absolute(folder_rel_path)
        folder_exists = Path(absolute_path).exists()
        folder_in_repo = folder_rel_path in self._status_cache
        
        debug("folder_status", f"Reconciling: {folder_rel_path}")
        debug("folder_status", f"  Exists in FS: {folder_exists}, In repo: {folder_in_repo}")
        
        # Get or create folder status
        if folder_in_repo:
            folder_status = self._status_cache[folder_rel_path]['status']
        else:
            folder_status = STATUS_NEW
        
        # SCENARIO 1: Folder is DISMISSED
        if folder_status == STATUS_DISMISSED:
            debug("folder_status", f"  Scenario 1: Folder is DISMISSED - skipping")
            return {
                'direct': None,
                'nested': None,
                'on_cloud': None,
                'dismissed': None,
                'new': None,
                'status': STATUS_DISMISSED
            }
        
        # SCENARIO 3: Folder in repo but NOT FOUND in filesystem
        if folder_in_repo and not folder_exists:
            debug("folder_status", f"  Scenario 3: Folder NOT FOUND in filesystem")
            # Mark as not found
            self._status_cache[folder_rel_path]['status'] = STATUS_NOT_FOUND
            self._status_cache[folder_rel_path]['item_type'] = 'folder'
            return {
                'direct': 0,
                'nested': 0,
                'on_cloud': 0,
                'dismissed': 0,
                'new': 0,
                'status': STATUS_NOT_FOUND
            }
        
        # SCENARIO 2: Folder in filesystem but NOT in repo
        if not folder_in_repo and folder_exists:
            debug("folder_status", f"  Scenario 2: Folder is NEW (not in repo)")
            return self._scan_new_folder(folder_rel_path, absolute_path, progress_callback)
        
        # SCENARIO 4: Folder is marked as NEW
        if folder_status == STATUS_NEW and folder_exists:
            debug("folder_status", f"  Scenario 4: Folder marked as NEW - rescanning from scratch")
            # Delete all repo info about this folder and its contents
            self._delete_folder_and_contents_from_repo(folder_rel_path)
            return self._scan_new_folder(folder_rel_path, absolute_path, progress_callback)
        
        # SCENARIO 5: Folder is WATCHED
        if folder_status == STATUS_WATCHED and folder_exists:
            debug("folder_status", f"  Scenario 5: Folder is WATCHED - reconciling contents")
            return self._reconcile_watched_folder(folder_rel_path, absolute_path, progress_callback)
        
        # Default case
        debug("folder_status", f"  Default case - treating as new")
        return self._scan_new_folder(folder_rel_path, absolute_path, progress_callback)
    
    def _scan_new_folder(self, folder_rel_path: str, absolute_path: str, progress_callback=None):
        """Scan a NEW folder recursively and mark everything as new.
        
        This scans RECURSIVELY through all subfolders to count and register all images.
        """
        debug("folder_status", f"Scanning NEW folder: {folder_rel_path}")
        
        direct_images = 0
        nested_images = 0
        
        try:
            folder_path = Path(absolute_path)
            
            # Add folder itself as NEW
            self._status_cache[folder_rel_path] = {
                'item_type': 'folder',
                'status': STATUS_NEW,
                'cloudinary_id': '',
                'cloudinary_url': '',
                'original_size': '',
                'upload_size': '',
                'upload_date': '',
                'last_modified': datetime.now().isoformat(),
                'notes': 'Auto-discovered'
            }
            
            # Scan all items in folder RECURSIVELY
            items = list(folder_path.rglob('*'))
            
            for idx, item in enumerate(items):
                if progress_callback:
                    progress_callback(idx + 1, len(items), f"Scanning {item.name}")
                
                item_rel_path = self.path_mapper.to_relative(str(item))
                
                if item.is_dir():
                    # Subfolder - mark as NEW
                    self._status_cache[item_rel_path] = {
                        'item_type': 'folder',
                        'status': STATUS_NEW,
                        'cloudinary_id': '',
                        'cloudinary_url': '',
                        'original_size': '',
                        'upload_size': '',
                        'upload_date': '',
                        'last_modified': datetime.now().isoformat(),
                        'notes': 'Auto-discovered'
                    }
                else:
                    # Check if it's an image file
                    if item.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                        if item.parent == folder_path:
                            direct_images += 1
                        else:
                            nested_images += 1
                        # Add file as NEW
                        self._status_cache[item_rel_path] = {
                            'item_type': 'file',
                            'status': FILE_STATUS_NEW,
                            'cloudinary_id': '',
                            'cloudinary_url': '',
                            'original_size': '',
                            'upload_size': '',
                            'upload_date': '',
                            'last_modified': datetime.now().isoformat(),
                            'notes': 'Auto-discovered'
                        }
            
            # Save after scanning
            self.save_status_db()
            
            return {
                'direct': direct_images,
                'nested': nested_images,
                'on_cloud': 0,
                'dismissed': 0,
                'new': direct_images,  # status counts are for direct images only
                'status': STATUS_NEW
            }
            
        except Exception as e:
            debug("errors", f"Error scanning new folder {folder_rel_path}: {e}")
            return {
                'direct': 0,
                'nested': 0,
                'on_cloud': 0,
                'dismissed': 0,
                'new': 0,
                'status': STATUS_NEW
            }
    
    def _reconcile_watched_folder(self, folder_rel_path: str, absolute_path: str, progress_callback=None):
        """Reconcile a WATCHED folder with expected watched/dismissed states.
        
        This scans RECURSIVELY through all subfolders to count all images.
        Direct counts (on_cloud, dismissed, new) apply to images directly in this folder only.
        """
        debug("folder_status", f"Reconciling WATCHED folder: {folder_rel_path}")
        
        folder_path = Path(absolute_path)
        
        # Counters - direct images are in this exact folder; nested are in subfolders
        direct_count = 0
        nested_count = 0
        on_cloud_count = 0    # direct images only
        dismissed_count = 0   # direct images only
        new_count = 0         # direct images only
        
        # Get all items currently in repo under this folder
        repo_items = {
            path: data for path, data in self._status_cache.items()
            if path.startswith(folder_rel_path + '/') or path == folder_rel_path
        }
        
        # Get all items currently in filesystem (RECURSIVELY)
        try:
            fs_items = list(folder_path.rglob('*'))
            
            # Track which repo items we've seen
            seen_repo_items = set()
            
            for idx, item in enumerate(fs_items):
                if progress_callback:
                    progress_callback(idx + 1, len(fs_items), f"Checking {item.name}")
                
                item_rel_path = self.path_mapper.to_relative(str(item))
                seen_repo_items.add(item_rel_path)
                
                if item.is_dir():
                    # Check if folder is in repo
                    if item_rel_path not in self._status_cache:
                        debug("folder_status", f"  New subfolder discovered: {item.name}")
                        self._status_cache[item_rel_path] = {
                            'item_type': 'folder',
                            'status': STATUS_NEW,
                            'cloudinary_id': '',
                            'cloudinary_url': '',
                            'original_size': '',
                            'upload_size': '',
                            'upload_date': '',
                            'last_modified': datetime.now().isoformat(),
                            'notes': 'Auto-discovered in watched folder'
                        }
                else:
                    # Check if it's an image file
                    if item.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                        is_direct = (item.parent == folder_path)
                        
                        if is_direct:
                            direct_count += 1
                        else:
                            nested_count += 1
                        
                        # Check if file is in repo
                        if item_rel_path in self._status_cache:
                            file_status = self._status_cache[item_rel_path]['status']
                            
                            # Track status counts for direct images only
                            if is_direct:
                                if file_status == FILE_STATUS_ON_CLOUD:
                                    on_cloud_count += 1
                                elif file_status == FILE_STATUS_DISMISSED:
                                    dismissed_count += 1
                                else:
                                    new_count += 1
                        else:
                            # New file discovered in watched folder
                            debug("folder_status", f"  New file discovered: {item.name}")
                            self._status_cache[item_rel_path] = {
                                'item_type': 'file',
                                'status': FILE_STATUS_NEW,
                                'cloudinary_id': '',
                                'cloudinary_url': '',
                                'original_size': '',
                                'upload_size': '',
                                'upload_date': '',
                                'last_modified': datetime.now().isoformat(),
                                'notes': 'Auto-discovered in watched folder'
                            }
                            if is_direct:
                                new_count += 1
            
            # Check for items in repo that are no longer in filesystem
            for repo_path, repo_data in repo_items.items():
                if repo_path not in seen_repo_items and repo_path != folder_rel_path:
                    debug("folder_status", f"  Item not found in FS: {repo_path}")
                    # Mark as not found
                    self._status_cache[repo_path]['status'] = FILE_STATUS_NOT_FOUND
            
            # Save changes
            self.save_status_db()
            
            return {
                'direct': direct_count,
                'nested': nested_count,
                'on_cloud': on_cloud_count,
                'dismissed': dismissed_count,
                'new': new_count,
                'status': STATUS_WATCHED
            }
            
        except Exception as e:
            debug("errors", f"Error reconciling watched folder {folder_rel_path}: {e}")
            return {
                'direct': 0,
                'nested': 0,
                'on_cloud': 0,
                'dismissed': 0,
                'new': 0,
                'status': STATUS_WATCHED
            }
    
    def dismiss_folder(self, relative_path: str) -> Tuple[bool, str]:
        """
        Mark a folder as dismissed and remove all its descendants from the database.
        
        This is a clean-slate dismiss: the folder entry is kept (as dismissed),
        but all tracked child images and subfolders are deleted from the CSV.
        
        Args:
            relative_path: Folder path relative to network root
            
        Returns:
            Tuple of (success, message)
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        rel_path = self.path_mapper.normalize_path(relative_path)
        
        # Delete this folder and all its descendants from cache
        self._delete_folder_and_contents_from_repo(rel_path)
        
        # Add back just the folder itself as dismissed
        self._status_cache[rel_path] = {
            'item_type': 'folder',
            'status': STATUS_DISMISSED,
            'cloudinary_id': '',
            'cloudinary_url': '',
            'original_size': '',
            'upload_size': '',
            'upload_date': '',
            'last_modified': datetime.now().isoformat(),
            'notes': ''
        }
        
        debug("folder_status", f"Dismissed folder: {rel_path}")
        return self.save_status_db()
    
    def set_file_on_cloud(self, relative_path: str, cloudinary_id: str = '',
                          cloudinary_url: str = '', original_size: str = '',
                          upload_size: str = '') -> Tuple[bool, str]:
        """
        Mark a file as uploaded to Cloudinary with metadata.
        
        Args:
            relative_path: File path relative to network root
            cloudinary_id: Cloudinary public ID
            cloudinary_url: Cloudinary secure URL
            original_size: Original file size (bytes or human-readable)
            upload_size: Size after upload/resizing
            
        Returns:
            Tuple of (success, message)
        """
        if not self._cache_loaded:
            self.load_status_db()
        
        rel_path = self.path_mapper.normalize_path(relative_path)
        now = datetime.now().isoformat()
        
        existing = self._status_cache.get(rel_path, {})
        
        self._status_cache[rel_path] = {
            'item_type': 'file',
            'status': FILE_STATUS_ON_CLOUD,
            'cloudinary_id': cloudinary_id,
            'cloudinary_url': cloudinary_url,
            'original_size': str(original_size),
            'upload_size': str(upload_size),
            'upload_date': now,
            'last_modified': now,
            'notes': existing.get('notes', '')
        }
        
        debug("folder_status", f"File marked as on_cloud: {rel_path} -> {cloudinary_id}")
        return self.save_status_db()
    
    def _delete_folder_and_contents_from_repo(self, folder_rel_path: str):
        """Delete a folder and all its contents from the repository."""
        debug("folder_status", f"Deleting folder and contents from repo: {folder_rel_path}")
        
        # Find all items that start with this folder path
        items_to_delete = [
            path for path in self._status_cache.keys()
            if path.startswith(folder_rel_path + '/') or path == folder_rel_path
        ]
        
        for item_path in items_to_delete:
            del self._status_cache[item_path]
            debug("folder_status", f"  Deleted: {item_path}")
        
        debug("folder_status", f"Deleted {len(items_to_delete)} items")
    
    def seed_folder_structure(self, progress_callback=None) -> Tuple[int, int]:
        """
        First-launch seeding: recursively walks all directories under network_root,
        adding each unseen folder as 'dismissed'. Saves once at the end.
        Existing entries are never overwritten.

        Args:
            progress_callback: Optional callable(rel_path: str) called for each new folder.

        Returns:
            Tuple of (added, skipped) counts.
        """
        if not self._cache_loaded:
            self.load_status_db()

        network_root = str(self.path_mapper.network_root)
        now = datetime.now().isoformat()
        added = 0
        skipped = 0

        for dirpath, dirnames, _files in os.walk(network_root):
            # Skip hidden directories and don't descend into them
            dirnames[:] = sorted([d for d in dirnames if not d.startswith('.')])

            rel = self.path_mapper.to_relative(dirpath)
            if not rel or rel == '.':
                continue  # Skip the root itself

            if rel in self._status_cache:
                skipped += 1
            else:
                self._status_cache[rel] = {
                    'item_type': 'folder',
                    'status': STATUS_DISMISSED,
                    'cloudinary_id': '',
                    'cloudinary_url': '',
                    'original_size': '',
                    'upload_size': '',
                    'upload_date': '',
                    'last_modified': now,
                    'notes': 'Seeded on first launch'
                }
                added += 1
                if progress_callback:
                    progress_callback(rel)

        if added > 0:
            self.save_status_db()

        debug("folder_status", f"seed_folder_structure: {added} added, {skipped} skipped")
        return added, skipped

    def has_child_folders(self, rel_path: str) -> bool:
        """
        Return True if any immediate child folder of rel_path is in the CSV cache.
        Does not touch the filesystem.
        """
        if not self._cache_loaded:
            self.load_status_db()
        prefix = rel_path + "/"
        for key, data in self._status_cache.items():
            if key.startswith(prefix) and data.get('item_type') == 'folder':
                remainder = key[len(prefix):]
                if '/' not in remainder:
                    return True
        return False

    def has_watched_descendant(self, rel_path: str) -> bool:
        """
        Return True if any descendant folder of rel_path has STATUS_WATCHED in the
        CSV cache.  Used to compute the auto STATUS_PART_WATCHED display state.
        Does not touch the filesystem.
        """
        if not self._cache_loaded:
            self.load_status_db()
        prefix = rel_path + "/"
        for key, data in self._status_cache.items():
            if key.startswith(prefix) and data.get('item_type') == 'folder':
                if data.get('status') == STATUS_WATCHED:
                    return True
        return False

    def get_immediate_child_folders(self, rel_path: str) -> List[Dict]:
        """
        Return all immediate child folders of rel_path from the CSV cache.
        Does not touch the filesystem.

        Returns:
            List of dicts with keys: 'rel_path', 'name', 'status'
        """
        if not self._cache_loaded:
            self.load_status_db()
        prefix = rel_path + "/"
        results = []
        for key, data in self._status_cache.items():
            if not key.startswith(prefix):
                continue
            remainder = key[len(prefix):]
            if '/' in remainder or data.get('item_type') != 'folder':
                continue
            results.append({
                'rel_path': key,
                'name': remainder,
                'status': data['status']
            })
        return sorted(results, key=lambda x: x['name'].lower())

    def __str__(self) -> str:
        if self._cache_loaded:
            return f"FolderStatusManager(entries={len(self._status_cache)}, csv={self.csv_path})"
        return f"FolderStatusManager(not loaded, csv={self.csv_path})"
    
    def __repr__(self) -> str:
        return self.__str__()
