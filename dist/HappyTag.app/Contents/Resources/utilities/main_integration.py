# utilities/main_integration.py
"""
Practical integration of ImageCardWidget system into main.py

This module provides a drop-in replacement for the current scattered
image widget creation logic in main.py, maintaining compatibility with
existing functionality while providing better organization.
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                           QPushButton, QLabel, QGridLayout, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QPixmap

from .image_card_widget import ImageCardWidget


class ImageGridWidget(QWidget):
    """
    Drop-in replacement for the current image widget system in main.py.
    
    This widget maintains the same interface as the current system but uses
    the new ImageCardWidget internally for better organization and maintainability.
    """
    
    # Signals that match current main.py expectations
    tags_changed = pyqtSignal(str, str)  # file_path, new_tags
    selection_changed = pyqtSignal(list)  # selected_file_paths
    
    def __init__(self, parent=None, max_preview_size=350):
        super().__init__(parent)
        
        self.max_preview_size = max_preview_size
        self.columns = 3  # Default columns, will be calculated based on width
        
        # Data storage matching current main.py structure
        self.image_widgets = []  # List of ImageCardWidget instances
        self.selected_images = set()  # Set of selected file paths
        self.image_previews = {}  # {file_path: QPixmap} - maintains compatibility
        self.image_metadata = {}  # {file_path: {'year': year, 'keywords': keywords}}
        self.original_keywords = {}  # {file_path: [keywords]} - for change tracking
        self.new_files_with_year = set()  # Files that need year added
        
        # Setup UI
        self._setup_ui()
        
        # Timer for responsive layout updates
        self._layout_timer = QTimer()
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._update_grid_layout)
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area (matching current main.py structure)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create scrollable content widget
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
    def create_preview(self, file_path):
        """
        Create preview - maintains compatibility with existing main.py function.
        
        Returns QPixmap for compatibility, but also creates ImageCardWidget internally.
        """
        try:
            print(f"Creating preview from file: {file_path}")
            
            # Check file extension (matching existing logic)
            _, ext = os.path.splitext(file_path.lower())
            if ext == '.psd':
                print(f"Warning: PSD files are not currently supported for preview: {file_path}")
                return None
            
            # Create QPixmap for preview (matching existing logic)
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                print(f"Error: Could not create preview for {file_path}")
                return None
                
            orig_width, orig_height = pixmap.width(), pixmap.height()
            print(f"Original size: {orig_width}x{orig_height}")
            
            # Calculate preview size (matching existing logic)
            if orig_width > orig_height:
                if orig_width > self.max_preview_size:
                    width = self.max_preview_size
                    height = int(orig_height * (self.max_preview_size / orig_width))
                else:
                    width = orig_width
                    height = orig_height
            else:
                if orig_height > self.max_preview_size:
                    height = self.max_preview_size
                    width = int(orig_width * (self.max_preview_size / orig_height))
                else:
                    width = orig_width
                    height = orig_height
            
            # Scale pixmap
            scaled_pixmap = pixmap.scaled(
                width, height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            print(f"Preview size: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
            # Store preview for compatibility
            self.image_previews[file_path] = scaled_pixmap
            
            return scaled_pixmap
            
        except Exception as e:
            print(f"Error creating preview for {file_path}: {e}")
            return None
    
    def add_image_widget(self, file_path, pixmap=None, metadata=None):
        """
        Add an image widget to the grid.
        
        Args:
            file_path: Path to the image file
            pixmap: Optional QPixmap (if None, will be created)
            metadata: Optional metadata dict with 'year' and 'keywords'
        """
        if pixmap is None:
            pixmap = self.create_preview(file_path)
            if pixmap is None:
                return None
        
        # Extract/prepare metadata
        if metadata is None:
            # This would call your existing get_image_metadata function
            metadata = {'year': None, 'keywords': []}
        
        year = metadata.get('year')
        keywords = metadata.get('keywords', [])
        
        # Store metadata (matching existing structure)
        self.image_metadata[file_path] = {
            'year': year,
            'keywords': keywords
        }
        
        # Setup original keywords tracking (matching existing logic)
        if not keywords and year:
            self.new_files_with_year.add(file_path)
            self.original_keywords[file_path] = []
        else:
            self.original_keywords[file_path] = keywords.copy() if keywords else []
        
        # Create ImageCardWidget
        image_widget = ImageCardWidget(
            file_path=file_path,
            pixmap=pixmap,
            tags=keywords,
            metadata=metadata
        )
        
        # Connect signals
        image_widget.tags_changed.connect(self._on_widget_tags_changed)
        image_widget.selection_changed.connect(self._on_widget_selection_changed)
        image_widget.text_sync_requested.connect(self._on_text_sync_requested)
        
        # Store widget
        self.image_widgets.append(image_widget)
        
        # Add to layout
        self._add_widget_to_grid(image_widget)
        
        return image_widget
    
    def _add_widget_to_grid(self, widget):
        """Add widget to the grid layout"""
        # Calculate position
        index = len(self.image_widgets) - 1
        row = index // self.columns
        col = index % self.columns
        
        # Add to layout
        self.scroll_layout.addWidget(widget, row, col)
        
        # Update layout if needed
        self._schedule_layout_update()
    
    def _schedule_layout_update(self):
        """Schedule a layout update"""
        self._layout_timer.start(100)  # 100ms delay
    
    def _update_grid_layout(self):
        """Update grid layout based on current width"""
        if not self.image_widgets:
            return
            
        # Calculate optimal columns based on widget width
        available_width = self.scroll_area.viewport().width() - 40  # Account for margins
        widget_width = 300  # Approximate widget width
        new_columns = max(1, available_width // widget_width)
        
        if new_columns != self.columns:
            self.columns = new_columns
            self._reorganize_grid()
    
    def _reorganize_grid(self):
        """Reorganize widgets in the grid"""
        # Clear layout
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)
        
        # Re-add widgets
        for index, widget in enumerate(self.image_widgets):
            row = index // self.columns
            col = index % self.columns
            self.scroll_layout.addWidget(widget, row, col)
    
    def _on_widget_tags_changed(self, file_path, new_tags):
        """Handle tags change from an ImageCardWidget"""
        # Update stored metadata
        if file_path in self.image_metadata:
            self.image_metadata[file_path]['keywords'] = new_tags
        
        # Emit signal for main.py compatibility
        tags_string = ', '.join(new_tags) if isinstance(new_tags, list) else str(new_tags)
        self.tags_changed.emit(file_path, tags_string)
    
    def _on_widget_selection_changed(self, file_path, is_selected):
        """Handle selection change from an ImageCardWidget"""
        if is_selected:
            self.selected_images.add(file_path)
        else:
            self.selected_images.discard(file_path)
        
        # Emit signal with current selection
        self.selection_changed.emit(list(self.selected_images))
    
    def _on_text_sync_requested(self, file_path, text):
        """Handle text sync request from an ImageCardWidget"""
        # Sync text to all selected widgets (matching existing sync_tags logic)
        if file_path not in self.selected_images:
            return
        
        current_text = text.strip()
        if not current_text:
            return
        
        # Get the last word/tag
        words = [w.strip() for w in current_text.split(',')]
        last_word = words[-1].strip() if words else ""
        
        if not last_word:
            return
        
        print(f"[DEBUG] Text sync requested | last_word: '{last_word}' | source: {file_path}")
        
        # Sync to other selected widgets
        for widget in self.image_widgets:
            if (widget.file_path in self.selected_images and 
                widget.file_path != file_path):
                
                widget.append_tag_text(last_word)
    
    # Public interface methods (for compatibility with main.py)
    
    def get_all_tag_changes(self):
        """Get all tag changes - compatible with existing main.py logic"""
        changes = {}
        for widget in self.image_widgets:
            file_path = widget.file_path
            current_tags = widget.get_tags()
            original_tags = self.original_keywords.get(file_path, [])
            
            # Check if tags have changed
            if set(current_tags) != set(original_tags):
                changes[file_path] = current_tags
        
        return changes
    
    def clear_all_tags(self):
        """Clear all tags from all widgets"""
        for widget in self.image_widgets:
            widget.set_tags([])
    
    def select_all(self):
        """Select all image widgets"""
        for widget in self.image_widgets:
            widget.set_selected(True)
    
    def select_none(self):
        """Deselect all image widgets"""
        for widget in self.image_widgets:
            widget.set_selected(False)
        self.selected_images.clear()
    
    def get_selected_file_paths(self):
        """Get list of selected file paths"""
        return list(self.selected_images)
    
    def clear_all_images(self):
        """Remove all image widgets"""
        for widget in self.image_widgets:
            widget.setParent(None)
        
        self.image_widgets.clear()
        self.selected_images.clear()
        self.image_previews.clear()
        self.image_metadata.clear()
        self.original_keywords.clear()
        self.new_files_with_year.clear()
    
    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        self._schedule_layout_update()


# Integration helper functions for main.py

def replace_image_widget_system(main_window):
    """
    Helper function to replace the current image widget system in main.py
    with the new ImageGridWidget.
    
    This would be called during main window initialization.
    """
    
    # Create new image grid widget
    image_grid = ImageGridWidget(parent=main_window, 
                                max_preview_size=main_window.MAX_PREVIEW_SIZE)
    
    # Connect signals to existing main.py methods
    image_grid.tags_changed.connect(main_window.on_tag_changed)  # If this method exists
    image_grid.selection_changed.connect(main_window.on_selection_changed)  # If this method exists
    
    # Replace the existing scroll area or image container
    # This would depend on your current main.py structure
    return image_grid

def migrate_existing_image_widgets(main_window, new_image_grid):
    """
    Helper function to migrate existing image widgets to the new system.
    
    Call this after loading images to transfer data from old system to new.
    """
    
    # If main_window has existing image data, migrate it
    if hasattr(main_window, 'image_previews'):
        for file_path, pixmap in main_window.image_previews.items():
            metadata = {}
            if hasattr(main_window, 'image_metadata') and file_path in main_window.image_metadata:
                metadata = main_window.image_metadata[file_path]
            
            new_image_grid.add_image_widget(file_path, pixmap, metadata)
    
    print(f"[DEBUG] Migrated {len(new_image_grid.image_widgets)} image widgets to new system")
