"""
Folder Scanner - Lazy loading directory scanner for folder management

Scans directories with lazy loading support: initially shows only root-level
folders, then scans deeper on demand. Respects discarded folder status to
skip unnecessary scanning. Provides progress tracking for large operations.

Author: HappyTag Development Team
Date: May 2026
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Dict
from datetime import datetime
from utilities.debug_utils import debug
from utilities.path_mapper import PathMapper
from utilities.folder_status_manager import (
    FolderStatusManager,
    STATUS_DISMISSED,
    SUPPORTED_IMAGE_EXTENSIONS
)


class ScanProgress:
    """Track scanning progress"""
    def __init__(self):
        self.total_folders = 0
        self.total_files = 0
        self.scanned_folders = 0
        self.scanned_files = 0
        self.current_path = ""
        self.is_cancelled = False
        
    def reset(self):
        """Reset progress counters"""
        self.total_folders = 0
        self.total_files = 0
        self.scanned_folders = 0
        self.scanned_files = 0
        self.current_path = ""
        self.is_cancelled = False
    
    def update_current(self, path: str):
        """Update current scanning path"""
        self.current_path = path
    
    def increment_folder(self):
        """Increment scanned folder count"""
        self.scanned_folders += 1
    
    def increment_file(self):
        """Increment scanned file count"""
        self.scanned_files += 1
    
    def cancel(self):
        """Cancel the scanning operation"""
        self.is_cancelled = True
    
    def get_percentage(self) -> int:
        """
        Get scan progress percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        total = self.total_folders + self.total_files
        if total == 0:
            return 0
        scanned = self.scanned_folders + self.scanned_files
        return min(100, int((scanned / total) * 100))
    
    def __str__(self) -> str:
        return f"ScanProgress({self.scanned_folders}/{self.total_folders} folders, {self.scanned_files}/{self.total_files} files)"


class FolderItem:
    """Represents a folder or file in the scan results"""
    def __init__(self, relative_path: str, is_directory: bool, 
                 name: str, parent_path: Optional[str] = None):
        self.relative_path = relative_path
        self.is_directory = is_directory
        self.name = name
        self.parent_path = parent_path
        self.children: List['FolderItem'] = []
        self.is_loaded = False  # Whether children have been loaded
        self.status = None  # Will be filled by status manager
        
    def add_child(self, child: 'FolderItem'):
        """Add a child item"""
        self.children.append(child)
    
    def __repr__(self) -> str:
        type_str = "DIR" if self.is_directory else "FILE"
        return f"FolderItem({type_str}: {self.relative_path}, loaded={self.is_loaded})"


class FolderScanner:
    """
    Scans directory structure with lazy loading support.
    
    Supports:
    - Shallow scan (root folders only)
    - Deep scan on demand
    - Skip discarded folders
    - Progress tracking
    - Cancellation
    """
    
    def __init__(self, network_root: str, status_manager: FolderStatusManager):
        """
        Initialize the folder scanner.
        
        Args:
            network_root: Root directory of network drive
            status_manager: FolderStatusManager instance
        """
        self.network_root = Path(network_root)
        self.path_mapper = PathMapper(network_root)
        self.status_manager = status_manager
        self.progress = ScanProgress()
        
        debug("scanner", f"FolderScanner initialized: root={network_root}")
    
    def scan_root_folders(self, progress_callback: Optional[Callable[[ScanProgress], None]] = None) -> List[FolderItem]:
        """
        Scan only the root-level folders (shallow scan).
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of FolderItem objects representing root folders
        """
        debug("scanner", "Starting root folder scan")
        self.progress.reset()
        root_items = []
        
        try:
            if not self.network_root.exists():
                debug("errors", f"Network root does not exist: {self.network_root}")
                return []
            
            # List immediate children only
            entries = list(self.network_root.iterdir())
            self.progress.total_folders = len([e for e in entries if e.is_dir()])
            self.progress.total_files = len([e for e in entries if e.is_file()])
            
            for entry in sorted(entries):
                if self.progress.is_cancelled:
                    debug("scanner", "Root scan cancelled by user")
                    break
                
                self.progress.update_current(entry.name)
                
                # Get relative path
                rel_path = self.path_mapper.to_relative(str(entry))
                if not rel_path:
                    continue
                
                is_dir = entry.is_dir()
                
                # For files, only include images
                if not is_dir and not self._is_image_file(entry.name):
                    self.progress.increment_file()
                    if progress_callback:
                        progress_callback(self.progress)
                    continue
                
                # Get status from status manager
                status = self.status_manager.get_status(rel_path)
                
                # Create FolderItem
                item = FolderItem(
                    relative_path=rel_path,
                    is_directory=is_dir,
                    name=entry.name,
                    parent_path=None
                )
                item.status = status
                item.is_loaded = False  # Children not loaded yet
                
                root_items.append(item)
                
                if is_dir:
                    self.progress.increment_folder()
                else:
                    self.progress.increment_file()
                
                if progress_callback:
                    progress_callback(self.progress)
            
            debug("scanner", f"Root scan complete: {len(root_items)} items found")
            return root_items
            
        except PermissionError as e:
            debug("errors", f"Permission denied scanning root: {e}")
            return []
        except Exception as e:
            debug("errors", f"Error scanning root folders: {e}")
            return []
    
    def scan_folder_contents(self, folder_item: FolderItem, 
                           recursive: bool = False,
                           progress_callback: Optional[Callable[[ScanProgress], None]] = None) -> List[FolderItem]:
        """
        Scan the contents of a specific folder (deep scan on demand).
        
        Args:
            folder_item: FolderItem to scan
            recursive: If True, scan all subfolders recursively
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of FolderItem objects representing folder contents
        """
        debug("scanner", f"Scanning folder contents: {folder_item.relative_path} (recursive={recursive})")
        
        # Check if folder is dismissed
        if folder_item.status == STATUS_DISMISSED:
            debug("scanner", f"Skipping dismissed folder: {folder_item.relative_path}")
            folder_item.is_loaded = True
            return []
        
        abs_path = self.path_mapper.to_absolute(folder_item.relative_path)
        folder_path = Path(abs_path)
        
        if not folder_path.exists() or not folder_path.is_dir():
            debug("errors", f"Folder does not exist or is not a directory: {abs_path}")
            folder_item.is_loaded = True
            return []
        
        children = []
        
        try:
            if recursive:
                # Recursive scan - walk entire tree
                children = self._scan_recursive(folder_item, progress_callback)
            else:
                # Shallow scan - immediate children only
                children = self._scan_immediate_children(folder_path, folder_item.relative_path, progress_callback)
            
            folder_item.children = children
            folder_item.is_loaded = True
            
            debug("scanner", f"Folder scan complete: {len(children)} children found")
            return children
            
        except Exception as e:
            debug("errors", f"Error scanning folder {folder_item.relative_path}: {e}")
            folder_item.is_loaded = True
            return []
    
    def _scan_immediate_children(self, folder_path: Path, parent_rel_path: str,
                                progress_callback: Optional[Callable[[ScanProgress], None]] = None) -> List[FolderItem]:
        """
        Scan immediate children of a folder (non-recursive).
        
        Args:
            folder_path: Absolute path to folder
            parent_rel_path: Relative path of parent folder
            progress_callback: Optional progress callback
            
        Returns:
            List of FolderItem objects
        """
        children = []
        
        try:
            entries = list(folder_path.iterdir())
            
            for entry in sorted(entries):
                if self.progress.is_cancelled:
                    break
                
                self.progress.update_current(entry.name)
                
                # Get relative path
                rel_path = self.path_mapper.to_relative(str(entry))
                if not rel_path:
                    continue
                
                is_dir = entry.is_dir()
                
                # For files, only include images
                if not is_dir and not self._is_image_file(entry.name):
                    if progress_callback:
                        progress_callback(self.progress)
                    continue
                
                # Get status
                status = self.status_manager.get_status(rel_path)
                
                # Create item
                item = FolderItem(
                    relative_path=rel_path,
                    is_directory=is_dir,
                    name=entry.name,
                    parent_path=parent_rel_path
                )
                item.status = status
                item.is_loaded = False
                
                children.append(item)
                
                if is_dir:
                    self.progress.increment_folder()
                else:
                    self.progress.increment_file()
                
                if progress_callback:
                    progress_callback(self.progress)
            
        except PermissionError as e:
            debug("errors", f"Permission denied scanning {folder_path}: {e}")
        except Exception as e:
            debug("errors", f"Error scanning {folder_path}: {e}")
        
        return children
    
    def _scan_recursive(self, folder_item: FolderItem,
                       progress_callback: Optional[Callable[[ScanProgress], None]] = None) -> List[FolderItem]:
        """
        Recursively scan folder and all subfolders.
        
        Args:
            folder_item: Root FolderItem to scan from
            progress_callback: Optional progress callback
            
        Returns:
            List of all FolderItem objects in tree
        """
        all_items = []
        abs_path = self.path_mapper.to_absolute(folder_item.relative_path)
        
        try:
            for root, dirs, files in os.walk(abs_path):
                if self.progress.is_cancelled:
                    break
                
                # Get relative path of current directory
                root_rel = self.path_mapper.to_relative(root)
                if not root_rel:
                    continue
                
                # Check if this folder is dismissed
                root_status = self.status_manager.get_status(root_rel)
                if root_status == STATUS_DISMISSED:
                    debug("scanner", f"Skipping dismissed folder tree: {root_rel}")
                    dirs[:] = []  # Don't descend into subdirectories
                    continue
                
                self.progress.update_current(root_rel)
                
                # Process subdirectories
                for dirname in sorted(dirs):
                    dir_abs = os.path.join(root, dirname)
                    dir_rel = self.path_mapper.to_relative(dir_abs)
                    
                    if not dir_rel:
                        continue
                    
                    # Get status
                    status = self.status_manager.get_status(dir_rel)
                    
                    # Create item
                    item = FolderItem(
                        relative_path=dir_rel,
                        is_directory=True,
                        name=dirname,
                        parent_path=root_rel
                    )
                    item.status = status
                    item.is_loaded = False
                    
                    all_items.append(item)
                    self.progress.increment_folder()
                    
                    if progress_callback:
                        progress_callback(self.progress)
                    
                    # If folder is dismissed, remove from dirs to skip scanning
                    if status == STATUS_DISMISSED:
                        dirs.remove(dirname)
                
                # Process files
                for filename in sorted(files):
                    if self.progress.is_cancelled:
                        break
                    
                    # Only include image files
                    if not self._is_image_file(filename):
                        continue
                    
                    file_abs = os.path.join(root, filename)
                    file_rel = self.path_mapper.to_relative(file_abs)
                    
                    if not file_rel:
                        continue
                    
                    # Get status
                    status = self.status_manager.get_status(file_rel)
                    
                    # Create item
                    item = FolderItem(
                        relative_path=file_rel,
                        is_directory=False,
                        name=filename,
                        parent_path=root_rel
                    )
                    item.status = status
                    item.is_loaded = True  # Files don't have children
                    
                    all_items.append(item)
                    self.progress.increment_file()
                    
                    if progress_callback:
                        progress_callback(self.progress)
        
        except Exception as e:
            debug("errors", f"Error in recursive scan: {e}")
        
        return all_items
    
    def estimate_folder_size(self, folder_path: str) -> Tuple[int, int]:
        """
        Estimate number of folders and files in a folder tree.
        Used to set progress totals before scanning.
        
        Args:
            folder_path: Relative path to folder
            
        Returns:
            Tuple of (folder_count, file_count)
        """
        abs_path = self.path_mapper.to_absolute(folder_path)
        folder_count = 0
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(abs_path):
                # Check if discarded
                root_rel = self.path_mapper.to_relative(root)
                if root_rel and self.status_manager.get_status(root_rel) == STATUS_DISMISSED:
                    dirs[:] = []  # Skip subdirectories
                    continue
                
                folder_count += len(dirs)
                # Only count image files
                image_files = [f for f in files if self._is_image_file(f)]
                file_count += len(image_files)
        
        except Exception as e:
            debug("errors", f"Error estimating folder size: {e}")
        
        debug("scanner", f"Estimated size for {folder_path}: {folder_count} folders, {file_count} files")
        return folder_count, file_count
    
    def _is_image_file(self, filename: str) -> bool:
        """
        Check if a filename is a supported image type.
        
        Args:
            filename: File name to check
            
        Returns:
            True if image file, False otherwise
        """
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_IMAGE_EXTENSIONS
    
    def cancel_scan(self):
        """Cancel the current scanning operation"""
        debug("scanner", "Scan cancellation requested")
        self.progress.cancel()
    
    def get_folder_tree(self, root_items: List[FolderItem]) -> Dict[str, FolderItem]:
        """
        Build a dictionary lookup for folder items by path.
        
        Args:
            root_items: List of root FolderItem objects
            
        Returns:
            Dictionary mapping relative_path to FolderItem
        """
        lookup = {}
        
        def add_to_lookup(items: List[FolderItem]):
            for item in items:
                lookup[item.relative_path] = item
                if item.children:
                    add_to_lookup(item.children)
        
        add_to_lookup(root_items)
        return lookup
    
    def __str__(self) -> str:
        return f"FolderScanner(root={self.network_root}, progress={self.progress})"
    
    def __repr__(self) -> str:
        return self.__str__()
