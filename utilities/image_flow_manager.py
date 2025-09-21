# utilities/image_flow_manager.py
"""
ImageFlowManager - Manages layout and organization of ImageCardWidget instances using FlowLayout
Handles responsive flow layout, selection management, and bulk operations
"""

from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QSizePolicy, QRubberBand, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QRect
from .image_card_widget import ImageCardWidget
from .tag_widgets import FlowLayout
from .image_sorter import ImageSorter
import gc
from .debug_utils import debug_layout, debug_memory, debug_errors, debug, debug_file_ops, debug_ui_events

# Debug control - set to False to reduce console output
DEBUG_FLOW = False  # Set to True for flow layout debugging

# Performance limits to prevent crashes
MAX_WIDGETS_SAFE = 100  # Maximum widgets before using special handling
BATCH_SIZE_DEFAULT = 25  # Default batch size for large image sets

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
        self.default_text_size = 10  # Default text size for new widgets
        
        # Data
        self.image_widgets = {}  # file_path -> ImageCardWidget
        self.selected_files = set()
        
        # Sorting
        self.image_sorter = ImageSorter()
        self.current_sort_order = []  # List of file_paths in current display order
        
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
        
        # Ensure the flow widget resizes properly but doesn't expand unnecessarily
        self.flow_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
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
        self.widget_width = max(100, width)  # Remove upper limit to support larger sizes
        debug_layout(f"Setting widget width to {self.widget_width}px (no upper limit)")
        
        # Update all existing widgets
        for widget in self.image_widgets.values():
            widget.set_max_width(self.widget_width)
    
    def set_text_size(self, text_size):
        """Set the default text size for new widgets and update existing ones"""
        self.default_text_size = text_size
        debug_layout(f"Setting default text size to {text_size}px")
        
        # Update all existing widgets
        for widget in self.image_widgets.values():
            if hasattr(widget, 'set_text_size'):
                widget.set_text_size(text_size)
            
    def add_image(self, file_path, tags=None, metadata=None, preview_pixmap=None, cloudinary_synced=False, 
                  public_id=None, original_tags=None, cloudinary_tags=None, public_id_to_be=None):
        """Add an image to the flow layout with enhanced metadata for upload optimization"""
        if file_path in self.image_widgets:
            print(f"[WARNING] Image already exists in flow: {file_path}")
            return
        
        # Create image widget with centralized metadata - pass all data at construction
        widget = ImageCardWidget(file_path, max_width=self.widget_width, preview_pixmap=preview_pixmap, 
                                cloudinary_synced=cloudinary_synced, cloudinary_public_id=public_id,
                                original_tags=original_tags, cloudinary_tags=cloudinary_tags)
        
        # Set initial UI tags
        if tags:
            widget.set_tags(tags)
        if metadata:
            widget.set_metadata(metadata)
            
        # Set enhanced metadata for upload optimization (public_id is already set in constructor)
        if original_tags:
            widget.set_original_tags(original_tags)
        if cloudinary_tags:
            widget.set_cloudinary_tags(cloudinary_tags)
        if public_id_to_be:
            widget.set_public_id_to_be(public_id_to_be)
        
        # Apply default text size to new widget
        if hasattr(widget, 'set_text_size'):
            widget.set_text_size(self.default_text_size)
        
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
            debug_layout( f"Added image to flow: {file_path}")
    
    def remove_image(self, file_path):
        """Remove an image from the flow layout"""
        if file_path in self.image_widgets:
            widget = self.image_widgets[file_path]
            # Cancel any pending timers before removing widget
            if hasattr(widget, '_cancel_pending_timers'):
                widget._cancel_pending_timers()
            # Also call cleanup if available
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
            self.flow_layout.removeWidget(widget)
            widget.setParent(None)
            del self.image_widgets[file_path]
            
            # Remove from selection if selected
            self.selected_files.discard(file_path)
            self.selection_changed.emit(list(self.selected_files))
            
            if DEBUG_FLOW:
                debug_layout( f"Removed image from flow: {file_path}")
    
    def clear_all(self):
        """Remove all images from the flow layout"""
        if DEBUG_FLOW:
            debug_layout("[DEBUG] Clearing all images from flow")
        
        # Clear selection
        self.selected_files.clear()
        
        # Remove all widgets (remove_image will handle timer cancellation)
        for file_path in list(self.image_widgets.keys()):
            self.remove_image(file_path)
        
        # Force immediate garbage collection to ensure widgets are destroyed
        import gc
        gc.collect()
        
        # Emit selection change
        self.selection_changed.emit([])
        
        if DEBUG_FLOW:
            debug_layout( f"Flow cleared - {len(self.image_widgets)} widgets remaining")
    
    def update_layout(self):
        """Update the flow layout - much simpler than grid layout"""
        # Prevent recursion during layout updates
        if getattr(self, '_updating_flow_layout', False):
            debug_layout("Skipping update_layout - already in progress")
            return
        
        self._updating_flow_layout = True
        try:
            debug_layout("Updating flow layout...")
            
            # Flow layout handles everything automatically - just trigger a repaint
            self.flow_widget.updateGeometry()
            self.flow_layout.invalidate()
            
            # Update widget widths in case slider changed
            for widget in self.image_widgets.values():
                widget.set_max_width(self.widget_width)
            
            # Debug information for scrolling issue
            flow_size = self.flow_widget.size()
            flow_hint = self.flow_widget.sizeHint()
            flow_min = self.flow_widget.minimumSizeHint()
            debug_layout(f"Flow layout updated - {len(self.image_widgets)} widgets")
            debug_layout(f"Flow widget size: {flow_size.width()}x{flow_size.height()}")
            debug_layout(f"Flow widget sizeHint: {flow_hint.width()}x{flow_hint.height()}")
            debug_layout(f"Flow widget minimumSizeHint: {flow_min.width()}x{flow_min.height()}")
            
            if hasattr(self, 'scroll_area') and self.scroll_area and self.scroll_area.viewport():
                viewport_size = self.scroll_area.viewport().size()
                debug_layout(f"Scroll area viewport: {viewport_size.width()}x{viewport_size.height()}")
            elif self.parent() and hasattr(self.parent(), 'size'):
                parent_size = self.parent().size()
                debug_layout(f"Parent size: {parent_size.width()}x{parent_size.height()}")
            
            # Force correct document widths after layout update (for resize operations)
            # QTimer.singleShot(100, self.force_all_document_widths)  # Test if still needed with QPlainTextEdit
        finally:
            self._updating_flow_layout = False
    
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
    
    # Sorting methods
    def sort_by_cloudinary_status(self, reverse=False):
        """Sort images by Cloudinary sync status (non-synced first by default)"""
        if not self.image_widgets:
            debug_layout("No images to sort")
            return
        
        debug_layout(f"Sorting images by Cloudinary status (reverse={reverse})")
        sorted_items = self.image_sorter.sort_images_by_cloudinary_status(self.image_widgets, reverse)
        self._apply_sort_order(sorted_items)
    
    def sort_by_filename(self, reverse=False):
        """Sort images alphabetically by filename"""
        if not self.image_widgets:
            debug_layout("No images to sort")
            return
        
        debug_layout(f"Sorting images by filename (reverse={reverse})")
        sorted_items = self.image_sorter.sort_images_by_filename(self.image_widgets, reverse)
        self._apply_sort_order(sorted_items)
    
    def sort_by_date_modified(self, reverse=False):
        """Sort images by modification date"""
        if not self.image_widgets:
            debug_layout("No images to sort")
            return
        
        debug_layout(f"Sorting images by date modified (reverse={reverse})")
        sorted_items = self.image_sorter.sort_images_by_date_modified(self.image_widgets, reverse)
        self._apply_sort_order(sorted_items)
    
    def sort_by_file_size(self, reverse=False):
        """Sort images by file size"""
        if not self.image_widgets:
            debug_layout("No images to sort")
            return
        
        debug_layout(f"Sorting images by file size (reverse={reverse})")
        sorted_items = self.image_sorter.sort_images_by_file_size(self.image_widgets, reverse)
        self._apply_sort_order(sorted_items)
    
    def _apply_sort_order(self, sorted_items):
        """Apply the sorted order to the flow layout"""
        debug_layout(f"Applying sort order to {len(sorted_items)} widgets")
        
        # Store the new order
        self.current_sort_order = [file_path for file_path, widget in sorted_items]
        
        # Temporarily disable updates to prevent flicker
        self.setUpdatesEnabled(False)
        
        try:
            # Remove all widgets from the layout (but don't delete them)
            while self.flow_layout.count():
                item = self.flow_layout.takeAt(0)
                if item and item.widget():
                    item.widget().setParent(None)  # Remove from layout but keep widget
            
            # Re-add widgets in new sorted order
            for file_path, widget in sorted_items:
                self.flow_layout.addWidget(widget)
            
            # Force layout update
            self.flow_layout.invalidate()
            self.flow_widget.updateGeometry()
            
        finally:
            # Re-enable updates
            self.setUpdatesEnabled(True)
            self.update()
        
        debug_layout("Sort order applied successfully")
    
    def get_current_sort_info(self):
        """Get information about current sort state"""
        return {
            'criteria': self.image_sorter.last_sort_criteria,
            'reverse': self.image_sorter.last_sort_reverse,
            'criteria_display': self.image_sorter.get_sort_criteria_display_name(
                self.image_sorter.last_sort_criteria) if self.image_sorter.last_sort_criteria else None
        }
    
    # Bulk loading method
    def load_images(self, image_data_list):
        """Load multiple images at once - with batching for large sets"""
        total_count = len(image_data_list)
        debug_file_ops( f"ImageFlowManager: Loading {total_count} images")
        
        # Clear existing images
        self.clear_all()
        
        # For large image sets, use batching to prevent memory issues
        if total_count > MAX_WIDGETS_SAFE:
            debug_file_ops( f"Large image set detected ({total_count} images), using batched loading (max safe: {MAX_WIDGETS_SAFE})")
            # Add a small delay to ensure all widget cleanup is complete, then start batching
            QTimer.singleShot(50, lambda: self._load_images_in_batches(image_data_list))
        else:
            debug_file_ops( f"Normal image set ({total_count} images), using standard loading")
            # Add a small delay to ensure all widget cleanup is complete
            QTimer.singleShot(50, lambda: self._load_images_after_cleanup(image_data_list))
        
    def _load_images_in_batches(self, image_data_list, batch_size=None, current_batch=0):
        """Load images in smaller batches to prevent memory overload"""
        if batch_size is None:
            batch_size = BATCH_SIZE_DEFAULT
            
        total_count = len(image_data_list)
        start_idx = current_batch * batch_size
        end_idx = min(start_idx + batch_size, total_count)
        
        if start_idx >= total_count:
            debug_file_ops( f"Batched loading complete: {total_count} images loaded")
            self.setUpdatesEnabled(True)
            self.update()
            self.update_layout()
            debug_memory(f"Total widgets in memory: {len(self.image_widgets)}")
            return
        
        try:
            batch_data = image_data_list[start_idx:end_idx]
            debug_file_ops( f"Loading batch {current_batch + 1}: images {start_idx + 1}-{end_idx} of {total_count}")
            
            # Temporarily disable layout updates during batch loading
            if current_batch == 0:
                self.setUpdatesEnabled(False)
            
            # Add images in this batch
            for image_data in batch_data:
                file_path = image_data['file_path']
                tags = image_data.get('tags', '')
                metadata = image_data.get('metadata', {})
                preview_pixmap = image_data.get('preview', None)
                cloudinary_synced = metadata.get('cloudinary_synced', False)  # Extract sync status from metadata
                
                # Enhanced metadata for upload optimization
                public_id = image_data.get('public_id')
                original_tags = image_data.get('original_tags', [])
                cloudinary_tags = image_data.get('cloudinary_tags', [])
                public_id_to_be = image_data.get('public_id_to_be')

                # Add the image with preview pixmap, sync status, and enhanced metadata
                self.add_image(file_path, tags=tags, metadata=metadata, preview_pixmap=preview_pixmap, 
                              cloudinary_synced=cloudinary_synced, public_id=public_id, 
                              original_tags=original_tags, cloudinary_tags=cloudinary_tags,
                              public_id_to_be=public_id_to_be)
            
            # Force garbage collection after each batch to free memory
            gc.collect()
            
            # Process next batch after a short delay to allow Qt to process events
            QTimer.singleShot(150, lambda: self._load_images_in_batches(image_data_list, batch_size, current_batch + 1))
            
        except Exception as e:
            debug_errors(f"Failed to load batch {current_batch + 1}: {e}")
            # Try to recover by continuing with the next batch
            QTimer.singleShot(300, lambda: self._load_images_in_batches(image_data_list, batch_size, current_batch + 1))
        
    def _load_images_after_cleanup(self, image_data_list):
        """Load images after cleanup delay"""
        debug_file_ops( f"ImageFlowManager: Starting delayed image load of {len(image_data_list)} images")
        
        # Temporarily disable layout updates to prevent premature size calculations
        self.setUpdatesEnabled(False)
        
        # Add each image - flow layout handles positioning automatically
        for image_data in image_data_list:
            file_path = image_data['file_path']
            tags = image_data.get('tags', '')
            metadata = image_data.get('metadata', {})
            preview_pixmap = image_data.get('preview', None)
            cloudinary_synced = metadata.get('cloudinary_synced', False)  # Extract sync status from metadata
            
            # Enhanced metadata for upload optimization
            public_id = image_data.get('public_id')
            original_tags = image_data.get('original_tags', [])
            cloudinary_tags = image_data.get('cloudinary_tags', [])
            public_id_to_be = image_data.get('public_id_to_be')

            # Add the image with preview pixmap, sync status, and enhanced metadata
            self.add_image(file_path, tags=tags, metadata=metadata, preview_pixmap=preview_pixmap, 
                          cloudinary_synced=cloudinary_synced, public_id=public_id, 
                          original_tags=original_tags, cloudinary_tags=cloudinary_tags,
                          public_id_to_be=public_id_to_be)
            
        # Re-enable updates and force a layout update
        self.setUpdatesEnabled(True)
        self.update()
            
        debug_file_ops( f"ImageFlowManager: Successfully loaded {len(self.image_widgets)} images")        # Update layout after loading all images (very lightweight)
        self.update_layout()
        
        # QPlainTextEdit should handle width correctly without forcing
        # Remove post-layout forcing to test if it's still needed
        # self.force_all_document_widths()
    
    def force_all_document_widths(self):
        """Force correct document widths for all widgets after layout is complete"""
        debug_layout( f"ImageFlowManager: Forcing document widths for {len(self.image_widgets)} widgets...")
        
        for file_path, widget in self.image_widgets.items():
            if hasattr(widget, 'force_document_width_post_layout'):
                widget.force_document_width_post_layout()
        
        debug_layout( "ImageFlowManager: Document width forcing complete")
    
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
        
        debug_ui_events( f"Rubber band selection: {len(newly_selected)} images selected")
