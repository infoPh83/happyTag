"""
Image Sorter - Sort image widgets by various criteria

Provides sorting functionality for ImageFlowManager to order images by:
- Cloudinary sync status (non-synced first, then synced)
- File name, modification date, file size, etc.
"""

import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
from .debug_utils import debug


class ImageSorter:
    """Handles sorting of image widgets by various criteria"""
    
    # Sort criteria constants
    SORT_BY_CLOUDINARY = "cloudinary_status"
    SORT_BY_FILENAME = "filename"
    SORT_BY_DATE_MODIFIED = "date_modified"
    SORT_BY_FILE_SIZE = "file_size"
    
    def __init__(self):
        self.last_sort_criteria = None
        self.last_sort_reverse = False
    
    def sort_images_by_cloudinary_status(self, image_widgets_dict: Dict[str, Any], reverse: bool = False) -> List[Tuple[str, Any]]:
        """
        Sort images by Cloudinary sync status.
        
        Args:
            image_widgets_dict: Dictionary of {file_path: widget}
            reverse: If True, synced images come first
            
        Returns:
            List of (file_path, widget) tuples in sorted order
        """
        debug("layout", f"Sorting {len(image_widgets_dict)} images by Cloudinary status (reverse={reverse})")
        
        def sort_key(item):
            file_path, widget = item
            # Get Cloudinary status from widget
            is_synced = False
            if hasattr(widget, 'get_cloudinary_status'):
                is_synced = widget.get_cloudinary_status()
            elif hasattr(widget, 'is_on_cloudinary'):
                is_synced = widget.is_on_cloudinary
            
            # Primary sort: Cloudinary status (False comes first unless reversed)
            # Secondary sort: Filename for stable ordering
            filename = os.path.basename(file_path).lower()
            
            if reverse:
                return (not is_synced, filename)  # Synced first when reversed
            else:
                return (is_synced, filename)      # Non-synced first when normal
        
        # Convert dict to list of tuples and sort
        items = list(image_widgets_dict.items())
        sorted_items = sorted(items, key=sort_key)
        
        # Debug output
        synced_count = sum(1 for _, widget in sorted_items 
                          if getattr(widget, 'get_cloudinary_status', lambda: False)() or 
                             getattr(widget, 'is_on_cloudinary', False))
        non_synced_count = len(sorted_items) - synced_count
        
        if reverse:
            debug("layout", f"Cloudinary sort result: {synced_count} synced first, {non_synced_count} non-synced after")
        else:
            debug("layout", f"Cloudinary sort result: {non_synced_count} non-synced first, {synced_count} synced after")
        
        self.last_sort_criteria = self.SORT_BY_CLOUDINARY
        self.last_sort_reverse = reverse
        
        return sorted_items
    
    def sort_images_by_filename(self, image_widgets_dict: Dict[str, Any], reverse: bool = False) -> List[Tuple[str, Any]]:
        """Sort images alphabetically by filename"""
        debug("layout", f"Sorting {len(image_widgets_dict)} images by filename (reverse={reverse})")
        
        def sort_key(item):
            file_path, widget = item
            return os.path.basename(file_path).lower()
        
        items = list(image_widgets_dict.items())
        sorted_items = sorted(items, key=sort_key, reverse=reverse)
        
        self.last_sort_criteria = self.SORT_BY_FILENAME
        self.last_sort_reverse = reverse
        
        return sorted_items
    
    def sort_images_by_date_modified(self, image_widgets_dict: Dict[str, Any], reverse: bool = False) -> List[Tuple[str, Any]]:
        """Sort images by modification date (newest first by default)"""
        debug("layout", f"Sorting {len(image_widgets_dict)} images by date modified (reverse={reverse})")
        
        def sort_key(item):
            file_path, widget = item
            try:
                return os.path.getmtime(file_path)
            except OSError:
                return 0  # Default for files that can't be accessed
        
        items = list(image_widgets_dict.items())
        # Default is newest first (reverse=True for modification time)
        sorted_items = sorted(items, key=sort_key, reverse=not reverse)
        
        self.last_sort_criteria = self.SORT_BY_DATE_MODIFIED
        self.last_sort_reverse = reverse
        
        return sorted_items
    
    def sort_images_by_file_size(self, image_widgets_dict: Dict[str, Any], reverse: bool = False) -> List[Tuple[str, Any]]:
        """Sort images by file size (largest first by default)"""
        debug("layout", f"Sorting {len(image_widgets_dict)} images by file size (reverse={reverse})")
        
        def sort_key(item):
            file_path, widget = item
            try:
                return os.path.getsize(file_path)
            except OSError:
                return 0  # Default for files that can't be accessed
        
        items = list(image_widgets_dict.items())
        # Default is largest first (reverse=True for file size)
        sorted_items = sorted(items, key=sort_key, reverse=not reverse)
        
        self.last_sort_criteria = self.SORT_BY_FILE_SIZE
        self.last_sort_reverse = reverse
        
        return sorted_items
    
    def get_sort_criteria_display_name(self, criteria: str) -> str:
        """Get human-readable name for sort criteria"""
        names = {
            self.SORT_BY_CLOUDINARY: "Cloudinary Status",
            self.SORT_BY_FILENAME: "Filename",
            self.SORT_BY_DATE_MODIFIED: "Date Modified",
            self.SORT_BY_FILE_SIZE: "File Size"
        }
        return names.get(criteria, criteria)
