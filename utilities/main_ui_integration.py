# utilities/main_ui_integration.py
"""
Specific integration for HappyTag main.py that works with the existing UI structure.

This module provides a minimal-change integration that replaces the current
image widget management while keeping the existing UI layout structure.
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QScrollArea, QLabel, QPushButton, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QPixmap

from .image_card_widget import ImageCardWidget


class HappyTagImageManager:
    """
    Image manager that integrates with existing HappyTag UI structure.
    
    This class replaces the scattered image widget logic while working
    with the existing scrollArea and picturesContainer from the UI file.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.max_preview_size = main_window.MAX_PREVIEW_SIZE
        
        # Data storage (maintains compatibility with existing code)
        self.image_widgets = []  # List of ImageCardWidget instances
        self.selected_images = set()  # Set of selected file paths
        self.image_previews = {}  # {file_path: QPixmap} - for compatibility
        self.image_metadata = {}  # {file_path: {'year': year, 'keywords': keywords}}
        self.original_keywords = {}  # {file_path: [keywords]} - for change tracking
        self.new_files_with_year = set()  # Files that need year added
        self.unsupported_files = []  # List of unsupported files
        
        # Grid layout settings
        self.columns = 3
        self.grid_layout = None
        
        # Timer for responsive layout
        self._layout_timer = QTimer()
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._update_responsive_layout)
        
        # Setup the image container
        self._setup_image_container()
    
    def _setup_image_container(self):
        """Setup the image container using existing UI structure"""
        # Use the existing picturesContainer from the UI
        pictures_container = self.main_window.picturesContainer
        
        # Clear any existing layout
        if pictures_container.layout():
            # Remove existing layout
            old_layout = pictures_container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            pictures_container.setLayout(None)
        
        # Create grid layout for images
        self.grid_layout = QGridLayout(pictures_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        print("[DEBUG] HappyTagImageManager: Image container setup complete")
    
    def create_preview(self, file_path):
        """
        Create preview - maintains full compatibility with existing main.py logic.
        
        This is a drop-in replacement for the current create_preview method.
        """
        try:
            print(f"Creating preview from file: {file_path}")
            
            # Check file extension first (matching existing logic exactly)
            _, ext = os.path.splitext(file_path.lower())
            if ext == '.psd':
                print(f"Warning: PSD files are not currently supported for preview: {file_path}")
                self.unsupported_files.append((file_path, "PSD format not currently supported"))
                return None
            elif ext == '.bmp':
                print(f"Warning: BMP files are not currently supported for preview: {file_path}")
                self.unsupported_files.append((file_path, "BMP format not currently supported"))
                return None
            
            # Use PIL to get actual dimensions (matching existing logic)
            from PIL import Image
            with Image.open(file_path) as img:
                orig_width, orig_height = img.size
                print(f"Original size: {orig_width}x{orig_height}")
                
                # Calculate preview size (exact match to existing logic)
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
                
                # Create QPixmap (matching existing logic)
                pixmap = QPixmap(file_path).scaled(
                    width, height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                if not pixmap.isNull():
                    print(f"Preview size: {pixmap.width()}x{pixmap.height()}")
                    self.image_previews[file_path] = pixmap
                    
                    # Check if metadata already exists to avoid duplicate reading
                    if hasattr(self.main_window, 'image_metadata') and file_path in self.main_window.image_metadata:
                        year = self.main_window.image_metadata[file_path]['year']
                        keywords = self.main_window.image_metadata[file_path]['keywords']
                    else:
                        # Read metadata during preview creation (matching existing logic)
                        year, keywords = self.main_window.get_image_metadata(file_path)
                        
                        # Store metadata in main window's cache for later use
                        if not hasattr(self.main_window, 'image_metadata'):
                            self.main_window.image_metadata = {}
                        self.main_window.image_metadata[file_path] = {
                            'year': year,
                            'keywords': keywords
                        }
                    
                    # Store metadata (matching existing structure)
                    self.image_metadata[file_path] = {
                        'year': year,
                        'keywords': keywords
                    }
                    
                    # Store original keywords for change tracking (matching existing logic)
                    if not keywords and year:
                        self.new_files_with_year.add(file_path)
                        self.original_keywords[file_path] = []
                    else:
                        self.original_keywords[file_path] = keywords.copy() if keywords else []
                    
                    return pixmap
                else:
                    print(f"Error: Could not create preview for {file_path} - QPixmap returned null")
                    return None
                    
        except Exception as e:
            # Handle exceptions exactly like existing code
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.psd', '.psb']:
                reason = "PSD/PSB format not supported"
                print(f"Error creating preview for {file_path}: {reason}")
                self.unsupported_files.append((file_path, reason))
            elif file_ext in ['.ai', '.eps']:
                reason = "Vector formats (AI/EPS) not supported"
                print(f"Error creating preview for {file_path}: {reason}")
                self.unsupported_files.append((file_path, reason))
            else:
                reason = f"File error: {str(e)}"
                print(f"Error creating preview for {file_path}: {e}")
                self.unsupported_files.append((file_path, reason))
            return None
    
    def create_image_widget(self, preview, max_width, file_path):
        """
        Create image widget - this maintains compatibility with the existing system
        while using ImageCardWidget internally for better organization.
        
        This method creates the old-style widget structure that update_layout expects,
        but uses ImageCardWidget for the actual image display.
        """
        print(f"Creating image widget with max_width: {max_width}")
        
        # Get stored metadata
        metadata = self.image_metadata.get(file_path, {'year': None, 'keywords': []})
        year = metadata.get('year')
        keywords = metadata.get('keywords', [])
        
        # Create the old-style widget structure that update_layout expects
        # This ensures compatibility with the existing codebase
        
        # Calculate scaled size (matching existing logic)
        ratio = preview.width() / preview.height()
        scaled_width = min(max_width, preview.width())
        scaled_height = int(scaled_width / ratio)
        print(f"Scaled dimensions: {scaled_width}x{scaled_height}")
        
        # Create container widget with minimal margins (matching existing structure)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Create ImageCardWidget for the actual image display
        image_card = ImageCardWidget(
            file_path=file_path,
            pixmap=preview,
            tags=keywords,
            metadata=metadata,
            max_width=scaled_width
        )
        
        # Create a compatibility input field that mirrors the ImageCardWidget's text field
        # This ensures the existing update_layout method can work with it
        input_field = QTextEdit()
        input_field.setFixedWidth(scaled_width)
        input_field.setFixedHeight(28)
        input_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Set the same text as the image card
        input_field.setText(', '.join(keywords) if keywords else '')
        
        # Style to match existing system
        input_field.setStyleSheet("""
            QTextEdit { 
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px 4px;
                background-color: white;
            }
            QTextEdit[selected="true"] {
                border: 2px solid #0078D4;
                background-color: rgba(0, 120, 212, 0.1);
            }
        """)
        
        # Add both to layout
        layout.addWidget(image_card)
        layout.addWidget(input_field)
        
        # Connect the input field to the ImageCardWidget for synchronization
        def sync_from_input_to_card():
            """Sync text from input field to image card"""
            text = input_field.toPlainText()
            tags = [tag.strip() for tag in text.split(',') if tag.strip()]
            image_card.set_tags(tags)
        
        def sync_from_card_to_input(new_tags):
            """Sync tags from image card to input field"""
            text = ', '.join(new_tags) if new_tags else ''
            input_field.setText(text)
        
        # Connect synchronization
        input_field.textChanged.connect(sync_from_input_to_card)
        image_card.tags_changed.connect(lambda fp, tags: sync_from_card_to_input(tags))
        
        # Connect selection handling
        def on_image_card_selection_changed(fp, selected):
            input_field.setProperty("selected", selected)
            input_field.style().polish(input_field)
            self._on_widget_selection_changed(fp, selected)
        
        image_card.selection_changed.connect(on_image_card_selection_changed)
        
        # Store references for compatibility
        container.file_path = file_path
        container.input_field = input_field  # This is what update_layout expects
        container.image_card = image_card    # Store reference to our enhanced widget
        
        # Store the ImageCardWidget for our new system
        self.image_widgets.append(image_card)
        
        return container
    
    def _add_widget_to_grid(self, widget):
        """Add widget to the grid layout"""
        index = len(self.image_widgets) - 1
        row = index // self.columns
        col = index % self.columns
        
        self.grid_layout.addWidget(widget, row, col)
        
        # Schedule responsive layout update
        self._layout_timer.start(100)
    
    def _update_responsive_layout(self):
        """Update grid layout based on available width"""
        if not self.image_widgets:
            return
        
        # Calculate optimal columns based on scroll area width
        scroll_area = self.main_window.scrollArea
        available_width = scroll_area.viewport().width() - 40  # Account for margins
        widget_width = 300  # Approximate widget width
        new_columns = max(1, available_width // widget_width)
        
        if new_columns != self.columns:
            self.columns = new_columns
            self._reorganize_grid()
    
    def _reorganize_grid(self):
        """Reorganize widgets in the grid"""
        # Remove all widgets from layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                self.grid_layout.removeWidget(item.widget())
        
        # Re-add widgets with new column count
        for index, widget in enumerate(self.image_widgets):
            row = index // self.columns
            col = index % self.columns
            self.grid_layout.addWidget(widget, row, col)
    
    def _on_widget_tags_changed(self, file_path, new_tags):
        """Handle tags change from ImageCardWidget"""
        # Update stored metadata
        if file_path in self.image_metadata:
            self.image_metadata[file_path]['keywords'] = new_tags
        
        print(f"[DEBUG] Tags changed for {file_path}: {new_tags}")
    
    def _on_widget_selection_changed(self, file_path, is_selected):
        """Handle selection change from ImageCardWidget"""
        if is_selected:
            self.selected_images.add(file_path)
        else:
            self.selected_images.discard(file_path)
        
        print(f"[DEBUG] Selection changed: {len(self.selected_images)} files selected")
        
        # Update main window selection if it has a method for this
        if hasattr(self.main_window, 'update_selection_ui'):
            self.main_window.update_selection_ui(list(self.selected_images))
    
    def _on_text_sync_requested(self, file_path, text):
        """Handle text sync request from ImageCardWidget"""
        # Implement tag synchronization (matching existing sync_tags logic)
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
    
    # Compatibility methods that match existing main.py expectations
    
    def clear_all_images(self):
        """Clear all images - maintains compatibility"""
        # Remove widgets from layout
        for widget in self.image_widgets:
            self.grid_layout.removeWidget(widget)
            widget.setParent(None)
        
        # Clear data structures
        self.image_widgets.clear()
        self.selected_images.clear()
        self.image_previews.clear()
        self.image_metadata.clear()
        self.original_keywords.clear()
        self.new_files_with_year.clear()
        self.unsupported_files.clear()
        
        print("[DEBUG] All images cleared")
    
    def get_tag_changes(self):
        """Get all tag changes - maintains compatibility with existing save logic"""
        changes = {}
        for widget in self.image_widgets:
            file_path = widget.file_path
            current_tags = widget.get_tags()
            original_tags = self.original_keywords.get(file_path, [])
            
            # Check if tags have changed
            if set(current_tags) != set(original_tags):
                changes[file_path] = current_tags
        
        return changes
    
    def select_all_images(self):
        """Select all images - maintains compatibility"""
        for widget in self.image_widgets:
            widget.set_selected(True)
    
    def deselect_all_images(self):
        """Deselect all images - maintains compatibility"""
        for widget in self.image_widgets:
            widget.set_selected(False)
        self.selected_images.clear()
    
    def clear_all_tags(self):
        """Clear all tags - maintains compatibility"""
        for widget in self.image_widgets:
            widget.set_tags([])


# Integration function for main.py
def integrate_image_manager(main_window):
    """
    Integration function to add the new image management system to main.py.
    
    This should be called in main.py __init__ after the UI is set up.
    
    Usage:
        from utilities.main_ui_integration import integrate_image_manager
        
        def __init__(self):
            super().__init__()
            self.setupUi(self)  # Existing UI setup
            
            # Integrate new image management
            self.image_manager = integrate_image_manager(self)
    """
    
    # Create the image manager
    image_manager = HappyTagImageManager(main_window)
    
    # Replace existing methods with manager methods
    # This maintains compatibility while using the new system
    main_window.create_preview = image_manager.create_preview
    main_window.create_image_widget = image_manager.create_image_widget
    
    # Add convenience methods to main window
    main_window.clear_all_images = image_manager.clear_all_images
    main_window.get_tag_changes = image_manager.get_tag_changes
    main_window.select_all_images = image_manager.select_all_images
    main_window.deselect_all_images = image_manager.deselect_all_images
    
    # Store reference to manager
    main_window.image_manager = image_manager
    
    print("[DEBUG] HappyTag image management system integrated successfully")
    
    return image_manager
