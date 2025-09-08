# utilities/image_grid_manager.py
"""
ImageGridManager - Manages layout and organization of ImageCardWidget instances
Handles responsive grid layout, selection management, and bulk operations
"""

from PyQt5.QtWidgets import QWidget, QGridLayout, QScrollArea, QVBoxLayout, QSizePolicy, QRubberBand, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QRect
from PyQt5.QtGui import QMouseEvent
from .image_card_widget import ImageCardWidget

class ImageGridManager(QWidget):
    """
    Manages a responsive grid of ImageCardWidget instances.
    Handles layout, selection, and provides bulk operations.
    """
    
    # Signals
    selection_changed = pyqtSignal(list)  # List of selected file paths
    image_double_clicked = pyqtSignal(str)  # file_path
    tags_changed = pyqtSignal(str, str)  # file_path, new_tags
    context_menu_requested = pyqtSignal(str, object)  # file_path, position
    
    def __init__(self, parent=None, use_internal_scroll=False):
        super().__init__(parent)
        
        # Configuration
        self.min_column_width = 130  # Minimum width to prevent too narrow columns
        self.max_column_width = 16777215  # Remove artificial width limit - let widgets use full available space
        self.grid_spacing = 4  # Further reduced from 6 to eliminate any horizontal scroll
        self.viewport_margin = 2  # Keep at 2 for minimal edge spacing
        self.use_internal_scroll = use_internal_scroll
        
        # Data
        self.image_widgets = {}  # file_path -> ImageCardWidget
        self.selected_files = set()
        self.current_columns = 0
        self._updating_height = False  # Flag to prevent infinite loops
        self._last_update_time = 0  # Track last update to prevent rapid succession
        self._update_in_progress = False  # Global flag to prevent any overlapping updates
        
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
        
        # Grid container widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(self.grid_spacing)
        
        # Ensure the grid widget resizes properly and respects minimum heights
        self.grid_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        if self.use_internal_scroll:
            # Create internal scroll area for standalone use
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setWidget(self.grid_widget)
            main_layout.addWidget(self.scroll_area)
        else:
            # For use within external scroll area - add grid widget directly
            self.scroll_area = None
            main_layout.addWidget(self.grid_widget)
        
        # Install event filter for mouse interactions
        self.grid_widget.installEventFilter(self)
        self.grid_widget.setMouseTracking(True)
        
    def add_image(self, file_path, tags=None, metadata=None, preview_pixmap=None):
        """Add an image to the grid"""
        if file_path in self.image_widgets:
            print(f"[WARNING] Image already exists in grid: {file_path}")
            return
        
        # Calculate widget width based on current layout
        widget_width = self._calculate_widget_width()
        
        # Create image widget with preview pixmap if available
        widget = ImageCardWidget(file_path, max_width=widget_width, preview_pixmap=preview_pixmap)
        
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
        
        # Add to layout
        self._add_widget_to_grid(widget)
        
        print(f"[DEBUG] Added image to grid: {file_path}")
    
    def remove_image(self, file_path):
        """Remove an image from the grid"""
        if file_path not in self.image_widgets:
            return
        
        widget = self.image_widgets[file_path]
        
        # Remove from layout
        self.grid_layout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()
        
        # Remove from data structures
        del self.image_widgets[file_path]
        self.selected_files.discard(file_path)
        
        # Refresh layout
        self._refresh_layout()
        
        print(f"[DEBUG] Removed image from grid: {file_path}")
    
    def clear_all(self):
        """Remove all images from the grid"""
        for file_path in list(self.image_widgets.keys()):
            self.remove_image(file_path)
        
        self.selected_files.clear()
        print("[DEBUG] Cleared all images from grid")
    
    def update_layout(self):
        """Recalculate and update the grid layout"""
        import time
        current_time = time.time()
        
        # Prevent rapid succession updates (less than 150ms apart)
        if current_time - self._last_update_time < 0.15:
            print(f"[DEBUG] Skipping update_layout - too soon ({current_time - self._last_update_time:.3f}s since last)")
            return
            
        # Prevent overlapping updates
        if self._update_in_progress:
            print("[DEBUG] Skipping update_layout - update already in progress")
            return
            
        if not self.image_widgets:
            return
        
        self._update_in_progress = True
        self._last_update_time = current_time
        
        try:
            print(f"[DEBUG] Starting update_layout at {current_time:.3f}")
            
            # Calculate new layout parameters
            widget_width = self._calculate_widget_width()
            new_columns = self._calculate_columns()
            
            # Update widget widths if needed
            if widget_width != self._get_current_widget_width():
                for widget in self.image_widgets.values():
                    widget.set_max_width(widget_width)
            
            # Refresh layout if column count changed
            if new_columns != self.current_columns:
                self._refresh_layout()
                
        finally:
            self._update_in_progress = False
    
    def _calculate_widget_width(self):
        """Calculate optimal widget width based on available space"""
        try:
            if self.scroll_area:
                viewport = self.scroll_area.viewport()
                if viewport:
                    # Account for scroll bar width and any other hidden margins
                    scroll_bar_allowance = 30  # More conservative to ensure no horizontal scroll
                    available_width = viewport.width() - (2 * self.viewport_margin) - scroll_bar_allowance
                else:
                    available_width = 770  # fallback reduced further
            else:
                # When no internal scroll area, use parent widget size
                available_width = self.width() - (2 * self.viewport_margin) - 30
                if available_width <= 0:
                    available_width = 770  # fallback
        except:
            available_width = 770  # fallback reduced further
            
        columns = self._calculate_columns()
        
        if columns == 0:
            return self.max_column_width
        
        # Calculate width accounting for spacing
        total_spacing = (columns - 1) * self.grid_spacing
        widget_width = (available_width - total_spacing) // columns
        
        # Clamp to min/max bounds
        return max(self.min_column_width, min(self.max_column_width, widget_width))
    
    def _calculate_columns(self):
        """Calculate number of columns based on desired columns or available width"""
        try:
            if self.scroll_area:
                viewport = self.scroll_area.viewport()
                if viewport:
                    # Account for scroll bar width and any other hidden margins
                    scroll_bar_allowance = 30  # More conservative to ensure no horizontal scroll
                    available_width = viewport.width() - (2 * self.viewport_margin) - scroll_bar_allowance
                else:
                    available_width = 770  # fallback reduced further
            else:
                # When no internal scroll area, use parent widget size
                available_width = self.width() - (2 * self.viewport_margin) - 30
                if available_width <= 0:
                    available_width = 770  # fallback
        except:
            available_width = 770  # fallback reduced further
        
        # Calculate maximum possible columns based on minimum width
        max_possible_columns = (available_width + self.grid_spacing) // (self.min_column_width + self.grid_spacing)
        max_possible_columns = max(1, max_possible_columns)
        
        # If we have a desired column count set by the user, respect it BUT only if it fits
        if hasattr(self, 'desired_columns') and self.desired_columns:
            if self.desired_columns <= max_possible_columns:
                print(f"[DEBUG] Using desired column count: {self.desired_columns} (fits in {available_width}px)")
                return self.desired_columns
            else:
                print(f"[DEBUG] Desired {self.desired_columns} columns won't fit in {available_width}px, using {max_possible_columns}")
                return max_possible_columns
        
        # Otherwise use calculated columns
        calculated_columns = max_possible_columns
        print(f"[DEBUG] Calculated columns from width: {calculated_columns} for {available_width}px")
        return calculated_columns
    
    def _get_current_widget_width(self):
        """Get current widget width from existing widgets"""
        if self.image_widgets:
            first_widget = next(iter(self.image_widgets.values()))
            return first_widget.max_width
        return self.max_column_width
    
    def _refresh_layout(self):
        """Rebuild the entire grid layout with proper column handling"""
        # Additional protection against rapid refresh calls
        if self._updating_height:
            print("[DEBUG] Skipping _refresh_layout - height update in progress")
            return
            
        # Calculate new columns and widget width
        new_columns = self._calculate_columns()
        new_widget_width = self._calculate_widget_width()
        
        print(f"[DEBUG] Refreshing layout: {new_columns} columns, widget width: {new_widget_width}")
        
        # Update widget widths if they've changed - this forces height recalculation
        current_width = self._get_current_widget_width()
        if new_widget_width != current_width:
            for widget in self.image_widgets.values():
                widget.set_max_width(new_widget_width)
                # Force widget to recalculate its minimum height with new width
                if hasattr(widget, '_calculate_and_set_minimum_height'):
                    widget._calculate_and_set_minimum_height()
        
        # Clear all existing row heights before rebuilding
        for row in range(self.grid_layout.rowCount()):
            self.grid_layout.setRowMinimumHeight(row, 0)
        
        # Remove all widgets from layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                self.grid_layout.removeItem(item)
        
        # Re-add widgets in new layout with bottom alignment (design requirement)
        row = 0
        col = 0
        for widget in self.image_widgets.values():
            # Ensure widget maintains its size preferences
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            
            self.grid_layout.addWidget(widget, row, col, Qt.AlignmentFlag.AlignBottom)
            
            # Set row minimum height based on widget content
            if hasattr(widget, 'minimumHeight') and widget.minimumHeight() > 0:
                current_row_height = self.grid_layout.rowMinimumHeight(row)
                widget_min_height = widget.minimumHeight()
                if widget_min_height > current_row_height:
                    self.grid_layout.setRowMinimumHeight(row, widget_min_height)
                    print(f"[DEBUG] Set row {row} minimum height to {widget_min_height}px")
            
            col += 1
            if col >= new_columns:
                col = 0
                row += 1
        
        self.current_columns = new_columns
        print(f"[DEBUG] Layout refreshed with {self.current_columns} columns, {len(self.image_widgets)} widgets")
        
        # Update grid minimum height to prevent overlapping - single call only
        QTimer.singleShot(100, self._update_grid_minimum_height)
        
    def _update_grid_minimum_height(self):
        """Calculate and set minimum height for the grid to prevent overlapping"""
        if self._updating_height:
            print("[DEBUG] Height update already in progress, skipping")
            return
            
        if not self.image_widgets:
            self.grid_widget.setMinimumHeight(100)
            return
            
        self._updating_height = True
        try:
            # Calculate how many rows we have
            num_widgets = len(self.image_widgets)
            columns = max(1, self.current_columns)
            rows = (num_widgets + columns - 1) // columns  # Ceiling division
            
            # Use consistent row height management for all column counts
            self._set_consistent_row_heights(columns, rows)
        finally:
            self._updating_height = False
    
    def _set_consistent_row_heights(self, columns, rows):
        """Set row heights based on the tallest widget in each row"""
        print(f"[DEBUG] Setting row heights for {rows} rows, {columns} columns")
        
        # Clear any existing row heights first
        for row in range(self.grid_layout.rowCount()):
            self.grid_layout.setRowMinimumHeight(row, 0)
        
        # Set consistent spacing for the grid layout
        consistent_spacing = 8
        self.grid_layout.setSpacing(consistent_spacing)
        
        # Calculate the maximum height needed for each row
        row_max_heights = {}
        widget_count = 0
        
        for widget in self.image_widgets.values():
            if widget and hasattr(widget, 'sizeHint'):
                # Find which row this widget is in
                index = self.grid_layout.indexOf(widget)
                if index >= 0:
                    row, col, _, _ = self.grid_layout.getItemPosition(index)
                    widget_height = widget.sizeHint().height()
                    
                    # Track the maximum height for this row
                    if row not in row_max_heights:
                        row_max_heights[row] = 0
                    if widget_height > row_max_heights[row]:
                        row_max_heights[row] = widget_height
                    
                    widget_count += 1
        
        # Set minimum height for each row based on its tallest widget
        for row, max_height in row_max_heights.items():
            if max_height > 0:
                self.grid_layout.setRowMinimumHeight(row, max_height)
                print(f"[DEBUG] Set row {row} minimum height to {max_height}px")
        
        # Ensure all widgets have consistent sizing policies
        for widget in self.image_widgets.values():
            if widget:
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        print(f"[DEBUG] Set heights for {len(row_max_heights)} rows based on {widget_count} widgets")
        print(f"[DEBUG] Grid spacing set to {consistent_spacing}px")
    
    def _add_widget_to_grid(self, widget):
        """Add a widget to the grid layout"""
        widget_count = self.grid_layout.count()
        columns = self._calculate_columns()
        
        row = widget_count // columns
        col = widget_count % columns
        
        # Ensure widget maintains its size preferences
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        # Add widget with bottom alignment to maintain design consistency
        self.grid_layout.addWidget(widget, row, col, Qt.AlignmentFlag.AlignBottom)
        
        # Don't set individual row minimum heights here - let the layout handle it naturally
        # This prevents the massive spacing issues we were seeing
        
        # Update grid minimum height after adding widget
        QTimer.singleShot(100, self._update_grid_minimum_height)
    
    # Selection Management
    
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
    
    def get_selected_files(self):
        """Get list of selected file paths"""
        return list(self.selected_files)
    
    def get_selected_count(self):
        """Get count of selected images"""
        return len(self.selected_files)
    
    # Data Management
    
    def get_all_tags(self):
        """Get tags for all images as dictionary {file_path: tags}"""
        return {path: widget.get_tags() for path, widget in self.image_widgets.items()}
    
    def set_tags_for_file(self, file_path, tags):
        """Set tags for a specific file"""
        if file_path in self.image_widgets:
            self.image_widgets[file_path].set_tags(tags)
    
    def set_tags_for_selected(self, tags):
        """Set tags for all selected files"""
        for file_path in self.selected_files:
            if file_path in self.image_widgets:
                self.image_widgets[file_path].set_tags(tags)
    
    def get_all_files(self):
        """Get list of all file paths in the grid"""
        return list(self.image_widgets.keys())
    
    def get_widget_count(self):
        """Get total number of widgets"""
        return len(self.image_widgets)
    
    # Event Handlers
    
    def _on_tags_changed(self, file_path, new_tags):
        """Handle tags change from individual widgets"""
        self.tags_changed.emit(file_path, new_tags)
    
    def _on_context_menu(self, file_path, position):
        """Handle context menu request from individual widgets"""
        self.context_menu_requested.emit(file_path, position)
    
    def _on_double_clicked(self, file_path):
        """Handle double click from individual widgets"""
        self.image_double_clicked.emit(file_path)
    
    def resizeEvent(self, a0):
        """Handle resize events - let main app handle layout updates to avoid conflicts"""
        super().resizeEvent(a0)
        # Don't handle layout updates here - let the main app's resize timer handle it
        # This prevents duplicate timers and cascading layout updates
    
    # Utility methods
    
    def get_grid_info(self):
        """Get information about the current grid state"""
        viewport_size = None
        try:
            if self.scroll_area and self.scroll_area.viewport():
                viewport_size = self.scroll_area.viewport().size()
        except:
            pass
            
        return {
            'total_images': len(self.image_widgets),
            'selected_count': len(self.selected_files),
            'columns': self.current_columns,
            'widget_width': self._get_current_widget_width(),
            'viewport_size': viewport_size,
        }
    
    def refresh_all_images(self):
        """Reload all images from disk"""
        for widget in self.image_widgets.values():
            widget.refresh_image()
    
    def set_column_count(self, num_columns):
        """Set the desired number of columns and refresh layout"""
        print(f"[DEBUG] ImageGridManager: Setting column count to {num_columns}")
        # Store the desired column count
        self.desired_columns = num_columns
        # Refresh the layout to apply the new column count
        self._refresh_layout()
        
    def load_images(self, image_data_list):
        """Load multiple images from a list of image data dictionaries
        
        Args:
            image_data_list: List of dicts with keys: file_path, preview, metadata, tags
        """
        print(f"[DEBUG] ImageGridManager: Loading {len(image_data_list)} images")
        
        # Clear existing images
        self.clear_all()
        
        # Add each image
        for image_data in image_data_list:
            file_path = image_data['file_path']
            tags = image_data.get('tags', '')
            metadata = image_data.get('metadata', {})
            preview_pixmap = image_data.get('preview', None)  # Get the preview pixmap
            
            # Add the image with preview pixmap
            self.add_image(file_path, tags=tags, metadata=metadata, preview_pixmap=preview_pixmap)
            
        print(f"[DEBUG] ImageGridManager: Successfully loaded {len(self.image_widgets)} images")
        
        # Update layout after loading all images
        self.update_layout()
    
    def eventFilter(self, obj, event):
        """Handle mouse events for rubber band selection and empty area clicks"""
        if obj == self.grid_widget:
            if event.type() == 2:  # QEvent.MouseButtonPress
                if event.button() == Qt.LeftButton:
                    # Check if click is on empty area (not on any widget)
                    clicked_widget = self.grid_widget.childAt(event.pos())
                    if clicked_widget is None or clicked_widget == self.grid_widget:
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
                            self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.grid_widget)
                        
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
    
    def __str__(self):
        return f"ImageGridManager({len(self.image_widgets)} images, {len(self.selected_files)} selected)"
