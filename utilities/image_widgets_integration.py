# utilities/image_widgets_integration.py
"""
Integration example showing how to replace the current image widget system
with the new ImageCardWidget and ImageGridManager classes
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSignal
from .image_grid_manager_fixed import ImageGridManager

class ImageDisplayWidget(QWidget):
    """
    New image display widget that replaces the scattered image widget logic
    in main.py. Provides a clean interface for image management.
    """
    
    # Signals to communicate with main application
    image_tags_changed = pyqtSignal(str, str)  # file_path, tags
    selection_changed = pyqtSignal(list)       # selected_file_paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Grid manager for organizing images
        self.grid_manager = None
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Image grid
        self.grid_manager = ImageGridManager()
        layout.addWidget(self.grid_manager)
        
        # Connect signals
        self.grid_manager.tags_changed.connect(self._on_tags_changed)
        self.grid_manager.selection_changed.connect(self._on_selection_changed)
        self.grid_manager.image_double_clicked.connect(self._on_image_double_clicked)
        
    def _create_control_panel(self):
        """Create control panel with selection and action buttons"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Selection info
        self.selection_label = QLabel("No images loaded")
        layout.addWidget(self.selection_label)
        
        layout.addStretch()
        
        # Selection buttons
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_images)
        layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_images)
        layout.addWidget(select_none_btn)
        
        return panel
        
    # Public interface methods
    
    def load_images(self, file_paths, metadata_dict=None):
        """
        Load images into the grid
        
        Args:
            file_paths: List of image file paths
            metadata_dict: Dictionary of {file_path: {'tags': [...], 'metadata': {...}}}
        """
        # Clear existing images
        self.grid_manager.clear_all()
        
        # Load new images
        for file_path in file_paths:
            tags = None
            metadata = None
            
            if metadata_dict and file_path in metadata_dict:
                data = metadata_dict[file_path]
                tags = data.get('tags', [])
                metadata = data.get('metadata', {})
            
            self.grid_manager.add_image(file_path, tags=tags, metadata=metadata)
        
        self._update_selection_label()
        print(f"[DEBUG] Loaded {len(file_paths)} images into grid")
    
    def get_all_tags(self):
        """Get current tags for all images"""
        return self.grid_manager.get_all_tags()
    
    def get_selected_files(self):
        """Get list of currently selected file paths"""
        return self.grid_manager.get_selected_files()
    
    def select_all_images(self):
        """Select all images"""
        self.grid_manager.select_all()
    
    def select_no_images(self):
        """Deselect all images"""
        self.grid_manager.select_none()
    
    def set_tags_for_selected(self, tags):
        """Set tags for all selected images"""
        self.grid_manager.set_tags_for_selected(tags)
    
    def clear_all_images(self):
        """Remove all images from the display"""
        self.grid_manager.clear_all()
        self._update_selection_label()
    
    def refresh_layout(self):
        """Refresh the grid layout (useful after window resize)"""
        self.grid_manager.update_layout()
    
    # Event handlers
    
    def _on_tags_changed(self, file_path, new_tags):
        """Handle tags change from grid manager"""
        self.image_tags_changed.emit(file_path, new_tags)
    
    def _on_selection_changed(self, selected_files):
        """Handle selection change from grid manager"""
        self._update_selection_label()
        self.selection_changed.emit(selected_files)
    
    def _on_image_double_clicked(self, file_path):
        """Handle image double click"""
        print(f"[DEBUG] Image double-clicked: {file_path}")
        # You can add custom double-click behavior here
    
    def _update_selection_label(self):
        """Update the selection info label"""
        total = self.grid_manager.get_widget_count()
        selected = self.grid_manager.get_selected_count()
        
        if total == 0:
            self.selection_label.setText("No images loaded")
        elif selected == 0:
            self.selection_label.setText(f"{total} images (none selected)")
        else:
            self.selection_label.setText(f"{total} images ({selected} selected)")


# Example integration function for main.py
def integrate_new_image_system(main_window):
    """
    Example function showing how to integrate the new image system
    into your existing main.py
    
    This would replace the current scattered image widget logic
    """
    
    # Create the new image display widget
    image_display = ImageDisplayWidget()
    
    # Connect to existing tag management system
    image_display.image_tags_changed.connect(main_window.on_tag_changed)
    
    # Replace the existing image loading logic
    def new_load_images(file_paths):
        """New image loading function using the widget system"""
        
        # Perform assessment if needed (existing logic)
        assessed_files = []
        metadata_dict = {}
        
        for file_path in file_paths:
            # Extract existing metadata/tags (from your existing system)
            tags = main_window.extract_tags_for_file(file_path)  # Your existing method
            metadata = main_window.extract_metadata_for_file(file_path)  # Your existing method
            
            assessed_files.append(file_path)
            metadata_dict[file_path] = {
                'tags': tags,
                'metadata': metadata
            }
        
        # Load into new system
        image_display.load_images(assessed_files, metadata_dict)
    
    # Replace the old image widget container with the new one
    # This would replace your existing scrollArea or image container
    main_window.setCentralWidget(image_display)  # or however you structure your UI
    
    return image_display
