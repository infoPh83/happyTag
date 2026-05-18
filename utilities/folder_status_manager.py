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


# Status constants
STATUS_DISCARDED = "discarded"
STATUS_NOT_EVALUATED = "not_evaluated"
STATUS_REQUIRING_TAGS = "requiring_tags"
STATUS_TAGGED_LOCAL = "tagged_local"
STATUS_SYNCED = "synced"
STATUS_NOT_FOUND = "not_found"

ALL_STATUSES = [
    STATUS_DISCARDED,
    STATUS_NOT_EVALUATED,
    STATUS_REQUIRING_TAGS,
    STATUS_TAGGED_LOCAL,
    STATUS_SYNCED,
    STATUS_NOT_FOUND
]

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
    relative_path,status,last_modified,cloudinary_id,date_tagged,date_synced,notes
    """
    
    CSV_FILENAME = "folder_status.csv"
    CSV_HEADERS = [
        'relative_path',
        'status',
        'last_modified',
        'cloudinary_id',
        'date_tagged',
        'date_synced',
        'notes'
    ]
    
    def __init__(self, network_root: str):
        """
        Initialize the status manager.
        
        Args:
            network_root: Root directory of the network drive
        """
        self.path_mapper = PathMapper(network_root)
        self.csv_path = Path(network_root) / self.CSV_FILENAME
        self.lock_manager = FileLockManager(network_root)
        
        # In-memory cache of status data
        self._status_cache: Dict[str, Dict] = {}
        self._cache_loaded = False
        
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
                return True, "New status database created"
            
            # Read CSV file
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self._status_cache = {}
                
                for row in reader:
                    rel_path = row['relative_path']
                    self._status_cache[rel_path] = {
                        'status': row['status'],
                        'last_modified': row['last_modified'],
                        'cloudinary_id': row['cloudinary_id'],
                        'date_tagged': row['date_tagged'],
                        'date_synced': row['date_synced'],
                        'notes': row['notes']
                    }
            
            self._cache_loaded = True
            count = len(self._status_cache)
            debug("folder_status", f"Loaded {count} entries from CSV")
            return True, f"Loaded {count} entries"
            
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
                        'status': data['status'],
                        'last_modified': data['last_modified'],
                        'cloudinary_id': data['cloudinary_id'],
                        'date_tagged': data['date_tagged'],
                        'date_synced': data['date_synced'],
                        'notes': data['notes']
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
            Status string, or STATUS_NOT_EVALUATED if not found
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
        
        debug("folder_status", f"get_status: {rel_path} -> {STATUS_NOT_EVALUATED} (default)")
        return STATUS_NOT_EVALUATED
    
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
        
        if status not in ALL_STATUSES:
            msg = f"Invalid status: {status}"
            debug("errors", msg)
            return False, msg
        
        # Normalize path
        rel_path = self.path_mapper.normalize_path(relative_path)
        
        # Update timestamp fields based on status
        now = datetime.now().isoformat()
        date_tagged = ""
        date_synced = ""
        
        if status == STATUS_TAGGED_LOCAL:
            date_tagged = now
        elif status == STATUS_SYNCED:
            date_tagged = now
            date_synced = now
        
        # Update cache
        self._status_cache[rel_path] = {
            'status': status,
            'last_modified': now,
            'cloudinary_id': cloudinary_id,
            'date_tagged': date_tagged,
            'date_synced': date_synced,
            'notes': notes
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
    
    def __str__(self) -> str:
        if self._cache_loaded:
            return f"FolderStatusManager(entries={len(self._status_cache)}, csv={self.csv_path})"
        return f"FolderStatusManager(not loaded, csv={self.csv_path})"
    
    def __repr__(self) -> str:
        return self.__str__()
