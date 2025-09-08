# utilities/image_flow_manager.py
"""
ImageFlowManager - Manages layout and organization of ImageCardWidget instances using FlowLayout
Handles responsive flow layout, selection management, and bulk operations
"""

from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QSizePolicy, QRubberBand, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QRect
from PyQt5.QtGui import QMouseEvent
from .image_card_widget import ImageCardWidget
from .tag_widgets import FlowLayout

# Debug control flag
DEBUG_FLOW = False  # Set to True for flow layout debugging

# Debug control - set to False to reduce console output
DEBUG_FLOW = False  # Set to True for flow layout debugging

class ImageFlowManager(QWidget):
    """
    Manages a responsive flow layout of ImageCardWidget instances.
    Widgets flow like text, wrapping to the next line when needed.
    """
    
    # Signals
    selection_changed = pyqtSignal(list)  # List of selected file paths
    image_double_clicked = pyqtSignal(str)  # file_path
    tags_changed = pyqtSignal(str, str)  # file_path, new_tags
    context_menu_requested = pyqtSignal(str, object)  # file_path, position
    
    def __init__(self, parent=None, use_internal_scroll=False):
        super().__init__(parent)
        
        # Configuration
        self.widget_width = 200  # Default widget width (controlled by slider)
        self.flow_spacing = 8  # Spacing between widgets
        self.flow_margin = 6  # Margin around the flow layout
        self.use_internal_scroll = use_internal_scroll
        
        # Data
        self.image_widgets = {}  # file_path -> ImageCardWidget
        self.selected_files = set()
        
        # Rubber band selection
        self.rubber_band = None
        self.selection_start = None
        self.is_selecting = False
        
        # UI setup
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Flow container widget
        self.flow_widget = QWidget()
        self.flow_layout = FlowLayout(self.flow_widget, margin=self.flow_margin, spacing=self.flow_spacing)
        
        # Ensure the flow widget resizes properly
        self.flow_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        if self.use_internal_scroll:
            # Create internal scroll area for standalone use
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setWidget(self.flow_widget)
            main_layout.addWidget(self.scroll_area)
        else:
            # For use within external scroll area - add flow widget directly
            self.scroll_area = None
            main_layout.addWidget(self.flow_widget)
        
        # Install event filter for mouse interactions
        self.flow_widget.installEventFilter(self)
        self.flow_widget.setMouseTracking(True)
        
    def set_widget_width(self, width):
        """Set the width for all image widgets"""
        self.widget_width = max(100, min(400, width))  # Constrain between 100-400px
        print(f"[DEBUG] Setting widget width to {self.widget_width}px")
        
        # Update all existing widgets
        for widget in self.image_widgets.values():
            widget.set_max_width(self.widget_width)
            
    def add_image(self, file_path, tags=None, metadata=None, preview_pixmap=None):
        """Add an image to the flow layout"""
        if file_path in self.image_widgets:
            print(f"[WARNING] Image already exists in flow: {file_path}")
            return
        
        # Create image widget with current width
        widget = ImageCardWidget(file_path, max_width=self.widget_width, preview_pixmap=preview_pixmap)
        
        # Set initial data
        if tags:
            widget.set_tags(tags)
        if metadata:
            widget.set_metadata(metadata)
        
        # Connect signals
        widget.selection_changed.connect(self._on_selection_changed)
        widget.text_changed.connect(self._on_tags_changed)
        widget.context_menu_requested.connect(self._on_context_menu)
        widget.double_clicked.connect(self._on_double_clicked)
        widget.clear_other_selections.connect(self._on_clear_other_selections)
        
        # Store widget
        self.image_widgets[file_path] = widget
        
        # Add to flow layout
        self.flow_layout.addWidget(widget)
        
        if DEBUG_FLOW:
            print(f"[DEBUG] Added image to flow: {file_path}")
    
    def remove_image(self, file_path):
        """Remove an image from the flow layout"""
        if file_path in self.image_widgets:
            widget = self.image_widgets[file_path]
            self.flow_layout.removeWidget(widget)
            widget.setParent(None)
            del self.image_widgets[file_path]
            
            # Remove from selection if selected
            self.selected_files.discard(file_path)
            self.selection_changed.emit(list(self.selected_files))
            
            if DEBUG_FLOW:
                print(f"[DEBUG] Removed image from flow: {file_path}")
    
    def clear_all(self):
        """Remove all images from the flow layout"""
        if DEBUG_FLOW:
            print("[DEBUG] Clearing all images from flow")
        
        # Clear selection
        self.selected_files.clear()
        
        # Remove all widgets
        for file_path in list(self.image_widgets.keys()):
            self.remove_image(file_path)
        
        # Emit selection change
        self.selection_changed.emit([])
        
        if DEBUG_FLOW:
            print(f"[DEBUG] Flow cleared - {len(self.image_widgets)} widgets remaining")
    
    def update_layout(self):
        """Update the flow layout - much simpler than grid layout"""
        print("[DEBUG] Updating flow layout...")
        
        # Flow layout handles everything automatically - just trigger a repaint
        self.flow_widget.updateGeometry()
        self.flow_layout.invalidate()
        
        # Update widget widths in case slider changed
        for widget in self.image_widgets.values():
            widget.set_max_width(self.widget_width)
        
        print(f"[DEBUG] Flow layout updated - {len(self.image_widgets)} widgets")
    
    # Signal handlers
    def _on_selection_changed(self, file_path, is_selected):
        """Handle selection change from individual widgets"""
        if is_selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)
        
        self.selection_changed.emit(list(self.selected_files))
    
    def _on_clear_other_selections(self, keep_selected_file):
        """Clear all selections except the specified file"""
        for file_path, widget in self.image_widgets.items():
            if file_path != keep_selected_file and widget.is_selected_state():
                widget.set_selected(False)
    
    def _on_tags_changed(self, file_path, new_tags):
        """Handle tags change from individual widgets"""
        self.tags_changed.emit(file_path, new_tags)
    
    def _on_context_menu(self, file_path, position):
        """Handle context menu request from individual widgets"""
        self.context_menu_requested.emit(file_path, position)
    
    def _on_double_clicked(self, file_path):
        """Handle double click from individual widgets"""
        self.image_double_clicked.emit(file_path)
    
    # Selection methods
    def select_all(self):
        """Select all images"""
        for widget in self.image_widgets.values():
            if not widget.is_selected_state():
                widget.set_selected(True)
    
    def select_none(self):
        """Deselect all images"""
        for widget in self.image_widgets.values():
            if widget.is_selected_state():
                widget.set_selected(False)
    
    def select_files(self, file_paths):
        """Select specific files"""
        for file_path, widget in self.image_widgets.items():
            should_select = file_path in file_paths
            if widget.is_selected_state() != should_select:
                widget.set_selected(should_select)
    
    # Bulk loading method
    def load_images(self, image_data_list):
        """Load multiple images at once - much more efficient than grid approach"""
        print(f"[DEBUG] ImageFlowManager: Loading {len(image_data_list)} images")
        
        # Clear existing images
        self.clear_all()
        
        # Add each image - flow layout handles positioning automatically
        for image_data in image_data_list:
            file_path = image_data['file_path']
            tags = image_data.get('tags', '')
            metadata = image_data.get('metadata', {})
            preview_pixmap = image_data.get('preview', None)
            
            # Add the image with preview pixmap
            self.add_image(file_path, tags=tags, metadata=metadata, preview_pixmap=preview_pixmap)
            
        print(f"[DEBUG] ImageFlowManager: Successfully loaded {len(self.image_widgets)} images")
        
        # Update layout after loading all images (very lightweight)
        self.update_layout()
    
    def eventFilter(self, obj, event):
        """Handle mouse events for rubber band selection and empty area clicks"""
        if obj == self.flow_widget:
            if event.type() == 2:  # QEvent.MouseButtonPress
                if event.button() == Qt.LeftButton:
                    # Check if click is on empty area (not on any widget)
                    clicked_widget = self.flow_widget.childAt(event.pos())
                    if clicked_widget is None or clicked_widget == self.flow_widget:
                        # Click on empty area
                        modifiers = QApplication.keyboardModifiers()
                        if not (modifiers & Qt.ControlModifier):
                            # Clear selection if not holding Ctrl
                            self.select_none()
                        
                        # Start rubber band selection
                        self.selection_start = event.pos()
                        self.is_selecting = True
                        
                        # Create rubber band if it doesn't exist
                        if self.rubber_band is None:
                            self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.flow_widget)
                        
                        # Position and show rubber band
                        self.rubber_band.setGeometry(QRect(self.selection_start, QSize()))
                        self.rubber_band.show()
                        return True
            
            elif event.type() == 5:  # QEvent.MouseMove
                if self.is_selecting and self.selection_start is not None:
                    # Update rubber band geometry
                    current_pos = event.pos()
                    rect = QRect(self.selection_start, current_pos).normalized()
                    self.rubber_band.setGeometry(rect)
                    return True
            
            elif event.type() == 3:  # QEvent.MouseButtonRelease
                if event.button() == Qt.LeftButton and self.is_selecting:
                    # End rubber band selection
                    self.is_selecting = False
                    
                    if self.rubber_band:
                        # Get final selection rectangle
                        selection_rect = self.rubber_band.geometry()
                        self.rubber_band.hide()
                        
                        # Find widgets within selection rectangle
                        self._select_widgets_in_rect(selection_rect)
                    
                    return True
        
        return super().eventFilter(obj, event)
    
    def _select_widgets_in_rect(self, rect):
        """Select all image widgets that intersect with the selection rectangle"""
        # Check modifier keys
        modifiers = QApplication.keyboardModifiers()
        
        # If not holding Ctrl, clear current selection first
        if not (modifiers & Qt.ControlModifier):
            self.select_none()
        
        # Find widgets that intersect with selection rect
        newly_selected = []
        for file_path, widget in self.image_widgets.items():
            widget_rect = widget.geometry()
            if rect.intersects(widget_rect):
                if modifiers & Qt.ControlModifier:
                    # Toggle selection with Ctrl
                    if widget.is_selected_state():
                        widget.set_selected(False)
                    else:
                        widget.set_selected(True)
                        newly_selected.append(file_path)
                else:
                    # Add to selection
                    if not widget.is_selected_state():
                        widget.set_selected(True)
                        newly_selected.append(file_path)
        
        print(f"[DEBUG] Rubber band selection: {len(newly_selected)} images selected")
