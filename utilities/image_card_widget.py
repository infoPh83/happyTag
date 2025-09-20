# utilities/image_card_widget.py
"""
ImageCardWidget - A comprehensive widget for displaying image with metadata and tags
Encapsulates all image card functionality in a reusable component
"""

import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QPlainTextEdit, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QTextOption
from .debug_utils import debug_layout, debug_image_display, debug_errors, debug

# Debug control - set to False to reduce console output
DEBUG_LAYOUT = False  # Set to True for layout debugging
DEBUG_HEIGHT = False  # Set to True for height calculation debugging

class ImageCardWidget(QWidget):
    """
    A comprehensive widget for displaying images with metadata and tags.
    Handles all image card functionality including layout, text management, 
    selection states, and user interactions.
    """
    
    # Signals for communication with parent
    selection_changed = pyqtSignal(str, bool)  # file_path, is_selected
    text_changed = pyqtSignal(str, str)        # file_path, new_text
    context_menu_requested = pyqtSignal(str, object)  # file_path, position
    double_clicked = pyqtSignal(str)           # file_path
    clear_other_selections = pyqtSignal(str)   # file_path of item to keep selected
    
    def __init__(self, file_path, max_width=300, preview_pixmap=None, cloudinary_synced=False, cloudinary_public_id=None, parent=None):
        super().__init__(parent)
        # Core data
        self.file_path = file_path
        self.max_width = max_width
        self.preview_pixmap = preview_pixmap  # Store preview pixmap if provided
        self.is_selected = False
        self.is_on_cloudinary = cloudinary_synced  # Set Cloudinary sync status from constructor
        self.metadata = {}
        self.tags = []
        
        # Enhanced metadata storage for upload optimization
        self.cloudinary_public_id = cloudinary_public_id  # Cloudinary public_id for this image (passed from main app)
        self.original_tags = []  # Tags as they were saved to disk/metadata
        self.cloudinary_tags = []  # Tags as they exist on Cloudinary
        
        # UI components
        self.image_label = None
        self.filename_label = None  # Add filename label
        self.text_edit = None
        self.container_frame = None
        
        # Configuration
        self.image_margin = 5
        self.text_min_height = 30  # Reduced from 60 to just fit one line of text
        self.text_max_height = 300  # Keep max height for text to prevent excessive height
        self.selection_border_width = 3
        
        # Ctrl operation suppression flag - prevents width enforcement during/after Ctrl operations
        self._ctrl_operation_in_progress = False
        self._ctrl_suppression_timer = None
        
        # Programmatic update suppression flag - prevents width enforcement during programmatic text changes
        self._programmatic_update_in_progress = False
        
        # Timer tracking for cleanup
        self.pending_timers = []  # Track active QTimer objects
        
        # Initialize the widget
        self._setup_ui()
        self._load_image()
        self._setup_connections()
        
        # Apply initial visual styling based on sync status
        self._update_visual_style()
        
        # Always call set_tags to ensure text height is properly initialized
        self.set_tags([])
    
    def _create_safe_timer(self, delay_ms, callback):
        """Create a timer that can be safely cancelled and tracks itself"""
        timer = QTimer()
        timer.setSingleShot(True)
        
        # Create a safe wrapper that checks widget validity before executing
        def safe_callback():
            try:
                # Check if widget still exists and is valid
                if hasattr(self, 'file_path') and hasattr(self, 'image_label'):
                    # Additional check for parent hierarchy
                    if self.parent() is not None:
                        callback()
                    else:
                        debug("memory", f"Timer callback skipped - widget orphaned: {os.path.basename(self.file_path) if hasattr(self, 'file_path') else 'unknown'}")
                else:
                    debug("memory", "Timer callback skipped - widget destroyed")
            except RuntimeError:
                debug("memory", "Timer callback skipped - widget deleted")
            finally:
                self._remove_timer(timer)
        
        timer.timeout.connect(safe_callback)
        self.pending_timers.append(timer)
        timer.start(delay_ms)
        return timer
    
    def _remove_timer(self, timer):
        """Remove timer from tracking list"""
        if timer in self.pending_timers:
            self.pending_timers.remove(timer)
    
    def _cancel_pending_timers(self):
        """Cancel all pending timers to prevent orphaned widget access"""
        for timer in self.pending_timers[:]:  # Create a copy of the list
            if timer.isActive():
                timer.stop()
            self.pending_timers.remove(timer)
        
        # Also cancel ctrl suppression timer if it exists
        if hasattr(self, '_ctrl_suppression_timer') and self._ctrl_suppression_timer:
            if self._ctrl_suppression_timer.isActive():
                self._ctrl_suppression_timer.stop()
            self._ctrl_suppression_timer = None
        
    def _start_ctrl_suppression(self):
        """Start temporary suppression of width enforcement during Ctrl operations"""
        if DEBUG_LAYOUT:
            print(f"[DEBUG-CTRL] Starting Ctrl suppression for {self.file_path}")
        
        self._ctrl_operation_in_progress = True
        
        # Cancel any existing timer
        if self._ctrl_suppression_timer:
            self._ctrl_suppression_timer.stop()
            
        # Set up new timer to clear suppression after 200ms
        self._ctrl_suppression_timer = QTimer()
        self._ctrl_suppression_timer.setSingleShot(True)
        self._ctrl_suppression_timer.timeout.connect(self._end_ctrl_suppression)
        self._ctrl_suppression_timer.start(200)  # 200ms should be enough for paste operation
        
    def _end_ctrl_suppression(self):
        """End temporary suppression of width enforcement"""
        if DEBUG_LAYOUT:
            print(f"[DEBUG-CTRL] Ending Ctrl suppression for {self.file_path}")
        
        self._ctrl_operation_in_progress = False
        if self._ctrl_suppression_timer:
            self._ctrl_suppression_timer.stop()
            self._ctrl_suppression_timer = None
        
    def _setup_ui(self):
        """Initialize the user interface components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container frame for selection border
        self.container_frame = QFrame()
        self.container_frame.setFrameStyle(QFrame.Box)
        self.container_frame.setLineWidth(1)
        self.container_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QFrame:hover {
                border: 1px solid #0078d4;
            }
        """)
        
        # Container layout
        container_layout = QVBoxLayout(self.container_frame)
        container_layout.setContentsMargins(self.image_margin, self.image_margin, 
                                          self.image_margin, self.image_margin)
        container_layout.setSpacing(5)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: none; background-color: transparent;")
        self.image_label.setScaledContents(False)
        # Let the image label size naturally based on its content - no constraints
        self.image_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Ensure no size constraints limit the image
        self.image_label.setMinimumSize(0, 0)
        self.image_label.setMaximumSize(16777215, 16777215)
        container_layout.addWidget(self.image_label)
        
        # Filename label - overlay on top of image
        self.filename_label = QLabel()
        self.filename_label.setText(os.path.basename(self.file_path))
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setStyleSheet("""
            QLabel { 
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 9px;
                font-weight: bold;
                margin: 0px;
            }
        """)
        self.filename_label.setWordWrap(True)
        self.filename_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        # Make filename label a child of the image label for overlay positioning
        self.filename_label.setParent(self.image_label)
        # Position will be set after image is loaded in _load_image method
        
        # Text edit for tags/metadata - using QPlainTextEdit for simpler, more predictable behavior
        self.text_edit = QPlainTextEdit()
        # Remove maximum height constraint for full dynamic sizing
        self.text_edit.setMinimumHeight(self.text_min_height)
        # Never show scroll bars - text should auto-resize within limits
        from PyQt5.QtCore import Qt as QtCore
        self.text_edit.setVerticalScrollBarPolicy(QtCore.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(QtCore.ScrollBarAlwaysOff)
        # Set content margins to ensure consistent internal layout
        self.text_edit.setContentsMargins(0, 0, 0, 0)
        # Set document margins to ensure consistent text layout
        document = self.text_edit.document()
        document.setDocumentMargin(1)  # Minimal margin for text layout
        # Enable word wrapping - QPlainTextEdit has simpler, more predictable wrapping
        self.text_edit.setWordWrapMode(QTextOption.WordWrap)
        # Use WidgetWidth mode - QPlainTextEdit handles this much better than QTextEdit
        self.text_edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                border: 2px solid #cccccc;
                border-radius: 3px;
                padding: 2px;
                font-size: 10px;
                line-height: 1.2;
            }
            QPlainTextEdit:focus {
                border: 2px solid #0078d4;
                padding: 4px;
            }
        """)
        container_layout.addWidget(self.text_edit)
        
        # Add container to main layout
        layout.addWidget(self.container_frame)
        
        # Set size policies to prevent compression and overlapping
        # Fixed height policy prevents vertical compression that causes overlapping
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Container frame should also resist compression
        self.container_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set the document width after all widgets are initialized
        def _delayed_update_text_width(this):
            # Use 'this' to avoid late binding issues in lambda
            if hasattr(this, 'text_edit') and this.text_edit is not None:
                this._update_text_width(this.max_width - (2 * this.image_margin))
                # Force document width to be set correctly for initial layout
                # This bypasses the focus/modifier checks in _enforce_document_width_immediate
                self._create_safe_timer(15, lambda: this._force_initial_document_width())
        self._create_safe_timer(0, lambda: _delayed_update_text_width(self))

    def _update_text_width(self, width):
        """Update both the text widget width and document width together"""
        if not hasattr(self, 'text_edit') or self.text_edit is None:
            return
        # Use a smaller reduction for document width - only account for actual borders/padding
        # The text widget already handles most spacing internally
        text_content_width = width - 6  # Reduced from 12 to 6 for less aggressive text wrapping
        try:
            self.text_edit.setFixedWidth(width)
            doc = self.text_edit.document()
            if doc:
                doc.setTextWidth(text_content_width)
            if DEBUG_HEIGHT:
                print(f"[DEBUG-WIDTH] Updated text widget width to {width}px, document width to {text_content_width}px")
        except Exception as e:
            print(f"[DEBUG-WIDTH] Exception in _update_text_width: {e}")
    
    def _load_image(self):
        """Load and scale the image for display"""
        try:
            # Use preview pixmap if available, otherwise load from file
            if self.preview_pixmap:
                debug_image_display(f"Using preview pixmap for {os.path.basename(self.file_path)}")
                pixmap = self.preview_pixmap
            else:
                debug_image_display(f"Loading from file: {os.path.basename(self.file_path)}")
                if not os.path.exists(self.file_path):
                    self._set_error_image("File not found")
                    return
                
                # CRITICAL FIX: Apply EXIF orientation correction when loading from file
                # This ensures portrait images display correctly even when preview_pixmap is None
                try:
                    from PIL import Image, ImageOps
                    from PyQt5.QtGui import QImage
                    
                    with Image.open(self.file_path) as img:
                        # Apply EXIF orientation correction
                        img_corrected = ImageOps.exif_transpose(img)
                        
                        # Convert to QPixmap with orientation correction
                        if img_corrected.mode == 'RGB':
                            rgb_data = img_corrected.tobytes('raw', 'RGB')
                            qimage = QImage(rgb_data, img_corrected.width, img_corrected.height, QImage.Format_RGB888)
                            pixmap = QPixmap.fromImage(qimage)
                        elif img_corrected.mode == 'RGBA':
                            qimage = QImage(img_corrected.tobytes(), img_corrected.width, img_corrected.height, QImage.Format_RGBA8888)
                            pixmap = QPixmap.fromImage(qimage)
                        else:
                            # Convert other modes to RGB first
                            img_rgb = img_corrected.convert('RGB')
                            rgb_data = img_rgb.tobytes('raw', 'RGB')
                            qimage = QImage(rgb_data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)
                            pixmap = QPixmap.fromImage(qimage)
                            
                        debug_image_display(f"Applied EXIF orientation correction for {os.path.basename(self.file_path)}: {img.size} -> {img_corrected.size}")
                        
                except Exception as e:
                    debug_image_display(f"EXIF correction failed for {os.path.basename(self.file_path)}, using QPixmap fallback: {e}")
                    # Fallback to basic QPixmap loading if EXIF correction fails
                    pixmap = QPixmap(self.file_path)
                
                if pixmap.isNull():
                    self._set_error_image("Invalid image")
                    return
                
            # Calculate scaled size maintaining aspect ratio
            # Use the passed max_width directly - don't try to get widget width during initialization
            available_width = self.max_width - (2 * self.image_margin)
            
            debug_image_display(f"Scaling image {os.path.basename(self.file_path)}: max_width={self.max_width}, available_width={available_width}")
            scaled_pixmap = self._scale_pixmap(pixmap, available_width)
            
            # Set the pixmap and force the label to match the pixmap size exactly
            self.image_label.setPixmap(scaled_pixmap)
            # Force the image label to be exactly the size of the scaled pixmap
            self.image_label.setFixedSize(scaled_pixmap.size())
            
            # Update text edit width to exactly match the image width for consistent layout
            image_width = scaled_pixmap.width()
            self.text_edit.setFixedWidth(image_width)
            self.text_edit.setMaximumWidth(image_width)
            self.text_edit.setMinimumWidth(image_width)
            
            # Also update the document width to match the widget width for consistent text wrapping
            document = self.text_edit.document()
            # Account for border (2px * 2) and padding (4px * 2) = 12px total
            text_content_width = image_width - 12
            document.setTextWidth(text_content_width)
            debug_layout(f"Set text widget width to {image_width}px, content width to {text_content_width}px")
            
            # Position filename label at top of image as overlay
            self._position_filename_label()
            
            # After image is loaded, calculate and set minimum height to prevent overlapping
            self._create_safe_timer(50, lambda: self._safe_minimum_height_calculation())
            
            # The image label will size to match the pixmap automatically
            
        except Exception as e:
            print(f"[ERROR] Failed to load image {self.file_path}: {e}")
            self._set_error_image(f"Load error: {str(e)}")
    
    def _position_filename_label(self):
        """Position the filename label as an overlay at the top of the image"""
        if self.filename_label and self.image_label:
            # Get the image label size
            image_size = self.image_label.size()
            
            # Size the filename label to fit the text
            self.filename_label.adjustSize()
            label_size = self.filename_label.size()
            
            # Position at top-left with small margin
            x = 5  # Small margin from left edge
            y = 5  # Small margin from top edge
            
            # Ensure filename doesn't extend beyond image width
            max_width = image_size.width() - 10  # Leave margins on both sides
            if label_size.width() > max_width:
                self.filename_label.setFixedWidth(max_width)
                self.filename_label.adjustSize()
                label_size = self.filename_label.size()
            
            # Position the label
            self.filename_label.move(x, y)
            self.filename_label.raise_()  # Ensure it's on top
            self.filename_label.show()
    
    def _scale_pixmap(self, pixmap, max_width):
        """Scale pixmap to exactly fill the widget width while maintaining aspect ratio"""
        # Always scale to exactly the widget width - let height be dynamic
        scaled_pixmap = pixmap.scaledToWidth(
            max_width, 
            Qt.SmoothTransformation
        )
        return scaled_pixmap
    
    def _set_error_image(self, error_message):
        """Set an error placeholder image"""
        self.image_label.setText(f"❌\n{error_message}")
        # Remove size constraints for error images too - let them size naturally
        self.image_label.setMinimumSize(0, 0)
        self.image_label.setMaximumSize(16777215, 16777215)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px dashed #cccccc;
                color: #666666;
                font-size: 10px;
            }
        """)
    
    def _setup_connections(self):
        """Setup signal connections"""
        self.text_edit.textChanged.connect(self._on_text_changed)
        # Install event filter to handle focus events
        self.text_edit.installEventFilter(self)
        
        # Connect to document content changes for immediate width enforcement
        document = self.text_edit.document()
        if document:
            # Connect to content changes to enforce width during typing
            document.contentsChanged.connect(self._on_document_content_changed)
        
    def eventFilter(self, obj, event):
        """Handle events for child widgets"""
        if obj == self.text_edit:
            # Handle focus events to ensure width consistency  
            if event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
                if event.type() == QEvent.Type.FocusOut:
                    # Only enforce width when focus is lost to avoid interfering with typing
                    self._create_safe_timer(10, self._enforce_text_width)
            # Handle key events to prevent wrapping during typing
            elif event.type() == QEvent.Type.KeyPress:
                # Only enforce width for keys that actually modify content
                # Exclude modifier keys (Ctrl, Alt, Shift) to prevent premature wrapping
                key = event.key()
                from PyQt5.QtCore import Qt
                
                # List of modifier keys and function keys that don't modify content
                non_content_keys = {
                    Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta,
                    Qt.Key.Key_CapsLock, Qt.Key.Key_NumLock, Qt.Key.Key_ScrollLock,
                    Qt.Key.Key_F1, Qt.Key.Key_F2, Qt.Key.Key_F3, Qt.Key.Key_F4,
                    Qt.Key.Key_F5, Qt.Key.Key_F6, Qt.Key.Key_F7, Qt.Key.Key_F8,
                    Qt.Key.Key_F9, Qt.Key.Key_F10, Qt.Key.Key_F11, Qt.Key.Key_F12,
                    Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Up, Qt.Key.Key_Down,
                    Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End,
                    Qt.Key.Key_PageUp, Qt.Key.Key_PageDown, Qt.Key.Key_Insert
                }
                
                # Only enforce width for content-modifying keys
                if key not in non_content_keys:
                    # Schedule immediate width enforcement after key processing
                    self._create_safe_timer(0, self._enforce_document_width_immediate)
        return super().eventFilter(obj, event)
    
    def _enforce_text_width(self):
        """Ensure text widget maintains its fixed width"""
        if hasattr(self, 'text_edit') and self.text_edit and hasattr(self, 'image_label') and self.image_label:
            if self.image_label.pixmap():
                image_width = self.image_label.pixmap().size().width()
                current_text_width = self.text_edit.width()
                print(f"[DEBUG-ENFORCE] _enforce_text_width called - Image: {image_width}px, Current TextEdit: {current_text_width}px")
                
                self.text_edit.setFixedWidth(image_width)
                self.text_edit.setMaximumWidth(image_width) 
                self.text_edit.setMinimumWidth(image_width)
                
                # Update both document width for QPlainTextEdit (simpler approach)
                if not self.text_edit.hasFocus():
                    document = self.text_edit.document()
                    if document:
                        text_content_width = image_width - 12  # Account for border + padding
                        current_doc_width = document.textWidth()
                        print(f"[DEBUG-ENFORCE] BEFORE: Document width = {current_doc_width}px, Image width = {image_width}px, Calculated content width = {text_content_width}px")
                        
                        # QPlainTextEdit should handle width much more predictably
                        document.setTextWidth(text_content_width)
                        
                        # Verify the width was actually set
                        post_set_width = document.textWidth()
                        print(f"[DEBUG-ENFORCE] AFTER: Document width = {post_set_width}px (expected {text_content_width}px)")
                        if post_set_width != text_content_width:
                            print(f"[DEBUG-ENFORCE] WARNING: Document width not set correctly! Expected {text_content_width}px but got {post_set_width}px")
                else:
                    print(f"[DEBUG-ENFORCE] Skipping document width update (has focus)")
    
    def _enforce_document_width_immediate(self):
        """Ensure correct document width during typing"""
        if hasattr(self, 'text_edit') and self.text_edit and hasattr(self, 'image_label') and self.image_label:
            if self.image_label.pixmap():
                # Check if a programmatic update is in progress
                if self._programmatic_update_in_progress:
                    print(f"[DEBUG-WIDTH] Skipping immediate width enforcement during programmatic update")
                    return
                    
                # Check if a Ctrl operation is in progress
                if self._ctrl_operation_in_progress:
                    print(f"[DEBUG-WIDTH] Skipping immediate width enforcement during Ctrl operation suppression")
                    return
                    
                # Check if Ctrl key is currently pressed - start suppression if detected
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtCore import Qt
                modifiers = QApplication.keyboardModifiers()
                
                if modifiers & Qt.ControlModifier:
                    print(f"[DEBUG-WIDTH] Ctrl detected, starting suppression period")
                    self._start_ctrl_suppression()
                    return
                
                image_width = self.image_label.pixmap().size().width()
                current_text_width = self.text_edit.width()
                
                print(f"[DEBUG-WIDTH] Image: {image_width}px, TextEdit: {current_text_width}px, HasFocus: {self.text_edit.hasFocus()}")
                
                # Keep the widget width correct
                self.text_edit.setFixedWidth(image_width)
                self.text_edit.setMaximumWidth(image_width) 
                self.text_edit.setMinimumWidth(image_width)
                
                # For live typing, set proper document width (not unlimited)
                if self.text_edit.hasFocus():
                    document = self.text_edit.document()
                    if document:
                        correct_doc_width = image_width - 12  # Account for border + padding
                        current_doc_width = document.textWidth()
                        print(f"[DEBUG-WIDTH] Document width was: {current_doc_width}px, setting to correct: {correct_doc_width}px")
                        
                        # Use proper width for wrapping, not unlimited
                        document.setTextWidth(correct_doc_width)
                        # Force immediate document layout update
                        document.adjustSize()
    
    def _force_initial_document_width(self):
        """Force correct document width during widget initialization, bypassing focus checks"""
        if hasattr(self, 'text_edit') and self.text_edit and hasattr(self, 'image_label') and self.image_label:
            if self.image_label.pixmap():
                image_width = self.image_label.pixmap().size().width()
                document = self.text_edit.document()
                if document:
                    # Use the same width calculation as the typing logic
                    correct_doc_width = image_width - 12  # Account for border + padding  
                    current_doc_width = document.textWidth()
                    # print(f"[DEBUG-WIDTH] INIT: Document width was: {current_doc_width}px, setting to correct: {correct_doc_width}px")
                    
                    # Set proper width for wrapping during initialization
                    document.setTextWidth(correct_doc_width)
                    # Force immediate document layout update
                    document.adjustSize()
                    # print(f"[DEBUG-WIDTH] INIT: Document width after setting: {document.textWidth()}px")
    
    def force_document_width_post_layout(self):
        """Force correct document width after layout is complete - simplified for QPlainTextEdit"""
        if hasattr(self, 'text_edit') and self.text_edit and hasattr(self, 'image_label') and self.image_label:
            if self.image_label.pixmap():
                image_width = self.image_label.pixmap().size().width()
                document = self.text_edit.document()
                if document:
                    text_content_width = image_width - 12  # Account for border + padding
                    current_doc_width = document.textWidth()
                    print(f"[DEBUG-WIDTH] POST-LAYOUT: Document width was: {current_doc_width}px, setting to: {text_content_width}px")
                    
                    # QPlainTextEdit should handle this more predictably than QTextEdit
                    document.setTextWidth(text_content_width)
                    
                    final_width = document.textWidth()
                    print(f"[DEBUG-WIDTH] POST-LAYOUT: Final document width: {final_width}px")
    
    def _on_document_content_changed(self):
        """Handle document content changes to maintain proper width during typing"""
        if hasattr(self, 'text_edit') and self.text_edit and self.text_edit.hasFocus():
            # Check if a programmatic update is in progress
            if self._programmatic_update_in_progress:
                print(f"[DEBUG-CONTENT] Skipping width enforcement during programmatic update")
                return
                
            # Check if a Ctrl operation is in progress
            if self._ctrl_operation_in_progress:
                print(f"[DEBUG-CONTENT] Skipping width enforcement during Ctrl operation suppression")
                return
                
            # Check if Ctrl key is currently pressed - start suppression if detected
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            modifiers = QApplication.keyboardModifiers()
            
            # If Ctrl is pressed, start suppression period to prevent interference
            if modifiers & Qt.ControlModifier:
                print(f"[DEBUG-CONTENT] Ctrl detected, starting suppression period")
                self._start_ctrl_suppression()
                return
            
            # Normal content change handling
            document = self.text_edit.document()
            if document and hasattr(self, 'image_label') and self.image_label and self.image_label.pixmap():
                image_width = self.image_label.pixmap().size().width()
                correct_doc_width = image_width - 12  # Account for border + padding
                current_width = document.textWidth()
                
                print(f"[DEBUG-CONTENT] Document content changed, current width: {current_width}px, setting to correct width: {correct_doc_width}px")
                
                # Set to proper width for wrapping (not unlimited)
                document.setTextWidth(correct_doc_width)
                
                # Ensure the widget width is correct during typing
                if self.text_edit.width() != image_width:
                    print(f"[DEBUG-CONTENT] Correcting widget width to {image_width}px during typing")
                    self.text_edit.setFixedWidth(image_width)
                    
                # CRITICAL: Prevent Qt from changing the document width again
                self._create_safe_timer(0, lambda: self._maintain_document_width_during_typing(correct_doc_width))
    
    def _maintain_document_width_during_typing(self, target_width):
        """Maintain consistent document width during typing session"""
        if hasattr(self, 'text_edit') and self.text_edit and self.text_edit.hasFocus():
            # Check if a programmatic update is in progress
            if self._programmatic_update_in_progress:
                print(f"[DEBUG-MAINTAIN] Skipping width maintenance during programmatic update")
                return
                
            # Check if a Ctrl operation is in progress
            if self._ctrl_operation_in_progress:
                print(f"[DEBUG-MAINTAIN] Skipping width maintenance during Ctrl operation suppression")
                return
                
            # Check if Ctrl key is currently pressed - start suppression if detected
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            modifiers = QApplication.keyboardModifiers()
            
            if modifiers & Qt.ControlModifier:
                print(f"[DEBUG-MAINTAIN] Ctrl detected, starting suppression period")
                self._start_ctrl_suppression()
                return
            
            document = self.text_edit.document()
            if document:
                current_width = document.textWidth()
                if abs(current_width - target_width) > 1:  # Allow small floating point differences
                    print(f"[DEBUG-MAINTAIN] Document width drifted to {current_width}px, correcting to {target_width}px")
                    document.setTextWidth(target_width)
        
    def _on_text_changed(self):
        """Handle text changes in the text edit"""
        new_text = self.text_edit.toPlainText()
        self.text_changed.emit(self.file_path, new_text)
        
        # Check if a programmatic update is in progress
        if self._programmatic_update_in_progress:
            debug("layout", "Skipping height adjustment during programmatic update (_on_text_changed)")
            return
            
        # Auto-adjust text height based on content
        self._adjust_text_height()
    
    def _adjust_text_height(self):
        """Automatically adjust text edit height based on content using document layout"""
        # Check if a Ctrl operation is in progress
        if self._ctrl_operation_in_progress:
            # print(f"[DEBUG-HEIGHT] Skipping height adjustment during Ctrl operation suppression")
            return
            
        # Check if a programmatic update is in progress
        if self._programmatic_update_in_progress:
            # print(f"[DEBUG-HEIGHT] Skipping height adjustment during programmatic update suppression")
            return
        
        # Add guard to prevent recursive calls
        if getattr(self, '_adjusting_height', False):
            return
        
        self._adjusting_height = True
        
        # Get actual text content
        text_content = self.text_edit.toPlainText().strip()
        
        # Calculate minimum height for one line of text based on font metrics
        font_metrics = self.text_edit.fontMetrics()
        single_line_height = font_metrics.height() + 10  # Add some padding
        dynamic_min_height = max(self.text_min_height, single_line_height)
        
        # If no content or just empty/whitespace, use dynamic minimum height
        if not text_content or text_content.isspace():
            self.text_edit.setFixedHeight(dynamic_min_height)
            self.text_edit.setMaximumHeight(dynamic_min_height)
            self.text_edit.setMinimumHeight(dynamic_min_height)
            self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # print(f"[DEBUG] Text height set to minimum ({dynamic_min_height}px) for empty content")
            self._create_safe_timer(100, lambda: self._check_actual_height("empty content"))
            return
        
        # Use document-based height calculation for accurate text wrapping
        # Use target width instead of current image width for consistent calculations during resize
        target_width = None
        if hasattr(self, 'max_width') and self.max_width:
            # Use the target width that the widget should be sized to
            target_width = self.max_width
            # Use consistent width reduction (same as _update_text_width)
            available_width = target_width - 6  # Reduced from 12 to 6 for consistency
            text_widget_width = target_width  # For debug output consistency
            image_width = target_width  # For debug output
        elif hasattr(self, 'image_label') and self.image_label and self.image_label.pixmap():
            # Fallback to current image width if max_width not available
            image_width = self.image_label.pixmap().size().width()
            available_width = image_width - 6  # Reduced from 12 to 6 for consistency
            text_widget_width = image_width  # For debug output consistency
        else:
            # Final fallback to text widget width if neither available
            text_widget_width = self.text_edit.width()
            available_width = text_widget_width - 6  # Reduced from 12 to 6 for consistency
            image_width = text_widget_width  # For debug output
        
        # print(f"[DEBUG-HEIGHT] Height adjustment - Target width: {target_width or 'N/A'}px, Available width: {available_width}px")
        
        # Get the document and ensure it has the correct width for wrapping
        document = self.text_edit.document()
        if document:
            current_doc_width = document.textWidth()
            # print(f"[DEBUG-HEIGHT] BEFORE height adjustment: Document width = {current_doc_width}px")
            
            # Always set the document width to ensure consistent text layout
            document.setTextWidth(available_width)
            
            # Verify the width was set correctly
            post_set_width = document.textWidth()
            # print(f"[DEBUG-HEIGHT] AFTER setting document width: Expected {available_width}px, Got {post_set_width}px")
            
            # Force document to recalculate size with proper width
            document.adjustSize()
            
            # PRECISE QPlainTextEdit height calculation - measure actual text wrapping
            # Create a temporary document with the exact same settings to measure real height
            
            # Get basic font metrics
            line_height = font_metrics.height()
            block_count = document.blockCount()  # For debug info
            
            text_content = self.text_edit.toPlainText()
            if not text_content.strip():
                doc_height = line_height  # Single line for empty content
                actual_lines = 1
            else:
                # Method: Ask QPlainTextEdit directly for its actual line count
                # First ensure the widget has been laid out properly
                self.text_edit.updateGeometry()
                # QApplication.processEvents()  # DISABLED: Let Qt finish layout - can cause recursion
                
                # Get the actual document from the QPlainTextEdit
                doc = self.text_edit.document()
                
                # Method 1: Try to get actual line count from the rendered document
                actual_lines = 0
                block = doc.firstBlock()
                while block.isValid():
                    # For each text block, count how many visual lines it takes
                    layout = block.layout()
                    if layout:
                        actual_lines += layout.lineCount()
                    else:
                        actual_lines += 1  # Fallback if no layout
                    block = block.next()
                
                # Fallback if we couldn't get layout info
                if actual_lines == 0:
                    actual_lines = max(1, doc.blockCount())
                
                # Calculate height based on actual rendered lines
                doc_height = actual_lines * line_height

                # print(f"[DEBUG-HEIGHT] QPlainTextEdit actual line count: actual_lines={actual_lines}, line_height={line_height}px, calculated_height={doc_height}px")

            # Get the actual document size for comparison
            doc_size = document.size()
            actual_doc_height = int(doc_size.height())
            # print(f"[DEBUG-HEIGHT] Document reports height={actual_doc_height}px, our precise measurement={doc_height}px")
            
            # Calculate final height with minimal additional padding
            # QTextDocument measurement already includes document margins
            margins = self.text_edit.contentsMargins()  # Should be 0,0,0,0
            padding = 4  # Small bottom padding for breathing room
            new_height = doc_height + margins.top() + margins.bottom() + padding
            
            # Apply bounds - ensure minimum height and respect maximum
            optimal_height = max(dynamic_min_height, min(self.text_max_height, new_height))
            
            # print(f"[DEBUG-HEIGHT] Height calculation: doc_height={doc_height}, new_height={new_height}, dynamic_min_height={dynamic_min_height}, optimal_height={optimal_height}")
            # print(f"[DEBUG-HEIGHT] BEFORE setFixedHeight - current height: {self.text_edit.height()}px")
            
            self.text_edit.setFixedHeight(optimal_height)
            self.text_edit.setMaximumHeight(optimal_height)
            self.text_edit.setMinimumHeight(optimal_height)
            self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # print(f"[DEBUG-HEIGHT] AFTER setFixedHeight - new height: {self.text_edit.height()}px")
            
            if DEBUG_HEIGHT:
                debug("layout", f"Document-based height calculation for {os.path.basename(self.file_path)}:")
                debug("layout", f"  text_width: {text_widget_width} | available_width: {available_width}")
                debug("layout", f"  content_chars: {len(text_content)} | doc_height: {doc_height} | actual_lines: {actual_lines} | final_height: {optimal_height}")
                debug("layout", f"  block_count: {block_count} | line_height: {line_height}")
            
            self._create_safe_timer(100, lambda: self._safe_check_actual_height(f"{len(text_content)} chars ({actual_lines} lines)"))
            
            # Also update the minimum height to prevent overlapping
            self._create_safe_timer(150, lambda: self._safe_minimum_height_calculation())
            
            # Clear the recursion guard
            self._adjusting_height = False
        else:
            # Fallback if document is not available - use old method
            debug("layout", "Document not available, using fallback height calculation")
            self.text_edit.setFixedHeight(dynamic_min_height)
            self.text_edit.setMaximumHeight(dynamic_min_height)
            self.text_edit.setMinimumHeight(dynamic_min_height)
            self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Clear the recursion guard
        self._adjusting_height = False
    
    def _safe_check_actual_height(self, description):
        """Safely check actual height with additional widget existence validation"""
        try:
            # Check if this widget instance still exists and is valid
            if hasattr(self, 'text_edit') and self.text_edit is not None:
                # Additional check to see if the widget is still part of a valid parent hierarchy
                if self.text_edit.parent() is not None or not self.text_edit.isHidden():
                    self._check_actual_height(description)
                else:
                    debug("memory", f"Widget orphaned before height check for {description}")
            else:
                debug("memory", f"Widget destroyed before height check for {description}")
        except Exception as e:
            debug_errors(f"Error in safe height check for {description}: {e}")

    def _check_actual_height(self, description):
        """Check and report the actual rendered height of the text edit"""
        # Safety check: ensure the widget still exists and hasn't been deleted
        try:
            if self.text_edit and not self.text_edit.isHidden():
                actual_height = self.text_edit.height()
                size_hint = self.text_edit.sizeHint().height()
                minimum_size = self.text_edit.minimumHeight()
                # Debug output reduced - only log significant issues
                if actual_height < minimum_size * 0.8:  # Only log if significantly different
                    debug("layout", f"Height issue for {description}: actual={actual_height}px, expected={minimum_size}px")
        except RuntimeError:
            # Widget has been deleted, ignore the callback
            pass  # Reduced debug output
        except Exception as e:
            debug_errors(f"Error during height check for {description}: {e}")
            debug_errors(f"  - Minimum height: {minimum_size}px")
    
    # Public interface methods
    
    def set_tags(self, tags):
        """Set the tags/metadata text"""
        # Handle various empty tag scenarios
        if not tags or (isinstance(tags, list) and len(tags) == 0):
            tags_text = ""
        elif isinstance(tags, list):
            # Filter out empty/whitespace-only tags
            valid_tags = [tag.strip() for tag in tags if tag and str(tag).strip()]
            tags_text = ', '.join(valid_tags) if valid_tags else ""
        else:
            tags_text = str(tags).strip() if tags else ""
            
        self.tags = tags if isinstance(tags, list) else ([tags] if tags else [])
        
        # Debug what we're actually setting
        if tags_text:
            debug("tags", f"Setting tags for {os.path.basename(self.file_path)}: '{tags_text}' (length: {len(tags_text)})")
        
        # Set programmatic update flag to suppress width enforcement
        self._programmatic_update_in_progress = True
        
        # Block signals to prevent recursive updates
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(tags_text)
        self.text_edit.blockSignals(False)
        
        # Adjust height after setting text, then clear programmatic flag
        self._create_safe_timer(0, self._adjust_text_height_and_clear_flag)
    
    def _adjust_text_height_and_clear_flag(self):
        """Clear the programmatic update flag and then adjust text height"""
        # Clear the programmatic update flag first
        self._programmatic_update_in_progress = False
        
        # Now adjust the height (flag is cleared so it will work)
        self._adjust_text_height()
    
    def get_tags(self):
        """Get current tags as a list"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            return []
        return [tag.strip() for tag in text.split(',') if tag.strip()]
    
    def set_metadata(self, metadata):
        """Set metadata dictionary"""
        self.metadata = metadata.copy() if metadata else {}
    
    def get_metadata(self):
        """Get metadata dictionary"""
        return self.metadata.copy()
    
    def set_selected(self, selected):
        """Set selection state"""
        if self.is_selected == selected:
            return
            
        self.is_selected = selected
        self._update_visual_style()
        self.selection_changed.emit(self.file_path, selected)
    
    def is_selected_state(self):
        """Get current selection state"""
        return self.is_selected
    
    def set_cloudinary_status(self, is_on_cloudinary):
        """Set Cloudinary sync status and update visual style"""
        if self.is_on_cloudinary == is_on_cloudinary:
            return
            
        self.is_on_cloudinary = is_on_cloudinary
        self._update_visual_style()
        
    def get_cloudinary_status(self):
        """Get current Cloudinary sync status"""
        return self.is_on_cloudinary
    
    # Enhanced metadata storage methods for upload optimization
    def set_cloudinary_public_id(self, public_id):
        """Set the Cloudinary public_id for this image"""
        self.cloudinary_public_id = public_id
        
    def get_cloudinary_public_id(self):
        """Get the Cloudinary public_id for this image"""
        return self.cloudinary_public_id
        
    def set_original_tags(self, tags):
        """Set the original tags as they were saved to disk/metadata"""
        self.original_tags = tags if isinstance(tags, list) else ([tags] if tags else [])
        
    def get_original_tags(self):
        """Get the original tags as they were saved to disk/metadata"""
        return self.original_tags.copy()
        
    def set_cloudinary_tags(self, tags):
        """Set the tags as they exist on Cloudinary"""
        self.cloudinary_tags = tags if isinstance(tags, list) else ([tags] if tags else [])
        
    def get_cloudinary_tags(self):
        """Get the tags as they exist on Cloudinary"""
        return self.cloudinary_tags.copy()
        
    def ui_tags_match_original(self):
        """Check if current UI tags match the original saved tags"""
        current_ui_tags = set(self.get_tags())
        original_tags_set = set(self.original_tags)
        return current_ui_tags == original_tags_set
        
    def ui_tags_match_cloudinary(self):
        """Check if current UI tags match the Cloudinary tags"""
        current_ui_tags = set(self.get_tags())
        cloudinary_tags_set = set(self.cloudinary_tags)
        return current_ui_tags == cloudinary_tags_set
    
    def _update_visual_style(self):
        """Update visual style based on selection state and Cloudinary sync status"""
        # Determine background color and border based on both states
        if self.is_on_cloudinary:
            # Dark yellow background when synced with Cloudinary
            background_color = "#DAA520"  # Dark golden rod color
            hover_color = "#B8860B"       # Darker gold for hover
        else:
            # Default white background
            background_color = "white"
            hover_color = "#f0f8ff"       # Light blue for hover
        
        if self.is_selected:
            # Selected state: blue border with appropriate background
            border_color = "#0078d4"
            border_width = self.selection_border_width
            if self.is_on_cloudinary:
                # Slightly lighter background when selected and on Cloudinary
                background_color = "#F0E68C"  # Khaki - lighter golden
            else:
                background_color = "#f0f8ff"  # Light blue
        else:
            # Non-selected state: subtle border
            border_color = "#cccccc"
            border_width = 1
        
        # Apply the calculated styles
        self.container_frame.setStyleSheet(f"""
            QFrame {{
                border: {border_width}px solid {border_color};
                border-radius: 4px;
                background-color: {background_color};
            }}
            QFrame:hover {{
                border: 1px solid #0078d4;
                background-color: {hover_color};
            }}
        """)
        
        # Force widget to repaint with new styling
        if self.container_frame:
            self.container_frame.update()
        self.update()
    
    def _update_selection_style(self):
        """Legacy method - redirects to _update_visual_style for backward compatibility"""
        self._update_visual_style()
    
    def set_max_width(self, width):
        """Update the target width for image scaling"""
        if width != self.max_width:
            self.max_width = width
            # Remove width constraints to allow expansion
            self.setMaximumWidth(16777215)  # Qt maximum
            self.setMinimumWidth(width)  # Set minimum to ensure proper sizing
            # Reload image to fit new width
            self._load_image()
    
    def get_file_path(self):
        """Get the file path"""
        return self.file_path
    
    def get_file_name(self):
        """Get just the filename"""
        return Path(self.file_path).name
    
    def refresh_image(self):
        """Reload the image from disk"""
        self._load_image()
    
    def resizeEvent(self, event):
        """Handle widget resize - update text width and height"""
        super().resizeEvent(event)
        # Update text widget and document width to new available width
        new_width = self.width() - (2 * self.image_margin)
        self._update_text_width(new_width)
        # Now adjust height based on new width
        self._adjust_text_height()
    
    # Event handlers
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection"""
        if event.button() == Qt.LeftButton:
            from PyQt5.QtWidgets import QApplication
            modifiers = QApplication.keyboardModifiers()
            
            if modifiers == Qt.ControlModifier:
                # Ctrl+click: Toggle selection without affecting others
                self.set_selected(not self.is_selected)
            else:
                # Normal click: Clear others and select this one
                # Emit a special signal to clear other selections first
                self.clear_other_selections.emit(self.file_path)
                self.set_selected(True)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click"""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.file_path)
        super().mouseDoubleClickEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        self.context_menu_requested.emit(self.file_path, event.globalPos())
        super().contextMenuEvent(event)
    
    def _safe_minimum_height_calculation(self):
        """Safely calculate minimum height with additional widget existence validation"""
        try:
            # Check if this widget instance still exists and is valid
            if hasattr(self, 'file_path') and hasattr(self, 'image_label'):
                # Additional check to see if the widget is still part of a valid parent hierarchy
                if (hasattr(self, 'parent') and (self.parent() is not None or not self.isHidden())):
                    self._calculate_and_set_minimum_height()
                else:
                    debug("memory", "Widget orphaned before minimum height calculation")
            else:
                debug("memory", "Widget destroyed before minimum height calculation")
        except Exception as e:
            debug_errors(f"Error in safe minimum height calculation: {e}")

    def _calculate_and_set_minimum_height(self):
        """Calculate and set the minimum height to prevent overlapping"""
        try:
            # Safety check: ensure the widget still exists and hasn't been deleted
            if not hasattr(self, 'image_label') or self.image_label is None:
                debug("memory", "Widget destroyed before minimum height calculation")
                return
                
            # Additional safety check for widget validity
            if not hasattr(self, 'file_path'):
                debug("memory", "Widget missing file_path, skipping height calculation")
                return
                
            # Check if image_label has been deleted
            try:
                pixmap_check = self.image_label.pixmap()  # This will throw RuntimeError if deleted
            except RuntimeError:
                debug("memory", f"Image label deleted before height calculation for {os.path.basename(self.file_path) if hasattr(self, 'file_path') else 'unknown'}")
                return
            
            if self.image_label and hasattr(self.image_label, 'pixmap') and pixmap_check:
                # Calculate minimum height based on image + text + margins + spacing
                try:
                    image_height = self.image_label.height() if self.image_label.height() > 0 else pixmap_check.height()
                    text_height = max(self.text_min_height, self.text_edit.height() if hasattr(self.text_edit, 'height') and self.text_edit else self.text_min_height)
                    
                    # Calculate total minimum height: image + text + margins + spacing
                    total_min_height = (image_height + 
                                      text_height + 
                                      (2 * self.image_margin) +  # Top and bottom margins
                                      5 +  # Spacing between image and text
                                      10)  # Additional padding for borders
                    
                    # Only log significant height changes for debugging
                    if DEBUG_HEIGHT and hasattr(self, '_last_min_height') and abs(total_min_height - self._last_min_height) > 20:
                        debug("layout", f"Height change for {os.path.basename(self.file_path)}: {self._last_min_height}px → {total_min_height}px")
                    self._last_min_height = total_min_height
                    
                    # Set the minimum height to prevent compression
                    self.setMinimumHeight(total_min_height)
                    if hasattr(self, 'container_frame') and self.container_frame:
                        try:
                            self.container_frame.setMinimumHeight(total_min_height - 10)  # Account for main margins
                        except RuntimeError:
                            debug("memory", "Container frame deleted during height calculation")
                            
                except RuntimeError as e:
                    debug("memory", f"Widget deleted during height calculation: {e}")
                    
            else:
                # Fallback minimum height
                default_height = 180
                try:
                    self.setMinimumHeight(default_height)
                except RuntimeError:
                    debug("memory", "Widget deleted before setting default height")
                    
        except Exception as e:
            debug_errors(f"Error in minimum height calculation: {e}")

    def sizeHint(self):
        """Provide size hint for layout"""
        if self.image_label.pixmap():
            image_size = self.image_label.pixmap().size()
            total_height = (image_size.height() + 
                          self.text_edit.height() + 
                          (2 * self.image_margin) + 10)  # spacing + margins
            hint = QSize(self.max_width, total_height)
            # print(f"[DEBUG-SIZEHINT] {os.path.basename(self.file_path)}: max_width={self.max_width}, total_height={total_height}, hint={hint.width()}x{hint.height()}")
            return hint
        else:
            hint = QSize(self.max_width, 200)  # default size
            # print(f"[DEBUG-SIZEHINT] {os.path.basename(self.file_path)}: NO PIXMAP - max_width={self.max_width}, hint={hint.width()}x{hint.height()}")
            return hint
    
    def minimumSizeHint(self):
        """Provide minimum size hint"""
        return QSize(150, 150)
    
    # Utility methods
    
    def cleanup(self):
        """Clean up resources and disconnect signals to prevent timer callbacks"""
        try:
            # Cancel all pending timers first
            self._cancel_pending_timers()
            
            if hasattr(self, 'text_edit') and self.text_edit:
                self.text_edit.textChanged.disconnect()
                self.text_edit = None
            debug("memory", f"Cleaned up ImageCardWidget for {os.path.basename(self.file_path) if hasattr(self, 'file_path') else 'unknown'}")
        except Exception as e:
            debug_errors(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup when widget is destroyed"""
        self.cleanup()

    def get_display_info(self):
        """Get summary information for debugging"""
        return {
            'file_path': self.file_path,
            'file_name': self.get_file_name(),
            'is_selected': self.is_selected,
            'tags_count': len(self.get_tags()),
            'has_metadata': bool(self.metadata),
            'widget_size': self.size(),
            'image_size': self.image_label.size() if self.image_label else None
        }
    
    def __str__(self):
        """String representation for debugging"""
        return f"ImageCardWidget('{self.get_file_name()}', selected={self.is_selected})"
    
    def __repr__(self):
        return self.__str__()
