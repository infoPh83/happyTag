# utilities/image_card_widget.py
"""
ImageCardWidget - A comprehensive widget for displaying image with metadata and tags
Encapsulates all image card functionality in a reusable component
"""

import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QFrame, QSizePolicy, QMenu, QAction,
                            QAbstractScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics, QPalette, QContextMenuEvent

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
    
    def __init__(self, file_path, max_width=300, preview_pixmap=None, parent=None):
        super().__init__(parent)
        
        print(f"[DEBUG] Creating ImageCardWidget for {os.path.basename(file_path)}")
        
        # Core data
        self.file_path = file_path
        self.max_width = max_width
        self.preview_pixmap = preview_pixmap  # Store preview pixmap if provided
        self.is_selected = False
        self.metadata = {}
        self.tags = []
        
        # UI components
        self.image_label = None
        self.text_edit = None
        self.container_frame = None
        
        # Configuration
        self.image_margin = 5
        self.text_min_height = 30  # Reduced from 60 to just fit one line of text
        self.text_max_height = 300  # Keep max height for text to prevent excessive height
        self.selection_border_width = 3
        
        # Initialize the widget
        self._setup_ui()
        self._load_image()
        self._setup_connections()
        
        print(f"[DEBUG] ImageCardWidget created for {os.path.basename(file_path)}, calling set_tags with empty list to ensure proper initialization")
        # Always call set_tags to ensure text height is properly initialized
        self.set_tags([])
        
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
        
        # Text edit for tags/metadata
        self.text_edit = QTextEdit()
        # Remove maximum height constraint for full dynamic sizing
        self.text_edit.setMinimumHeight(self.text_min_height)
        # Never show scroll bars - text should auto-resize within limits
        from PyQt5.QtCore import Qt as QtCore
        self.text_edit.setVerticalScrollBarPolicy(QtCore.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(QtCore.ScrollBarAlwaysOff)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 4px;
                font-size: 10px;
                line-height: 1.2;
            }
            QTextEdit:focus {
                border: 2px solid #0078d4;
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
        
    def _load_image(self):
        """Load and scale the image for display"""
        try:
            # Use preview pixmap if available, otherwise load from file
            if self.preview_pixmap:
                print(f"[DEBUG] Using preview pixmap for {os.path.basename(self.file_path)}")
                pixmap = self.preview_pixmap
            else:
                print(f"[DEBUG] Loading from file: {os.path.basename(self.file_path)}")
                if not os.path.exists(self.file_path):
                    self._set_error_image("File not found")
                    return
                    
                pixmap = QPixmap(self.file_path)
                if pixmap.isNull():
                    self._set_error_image("Invalid image")
                    return
                
            # Calculate scaled size maintaining aspect ratio
            # Use the passed max_width directly - don't try to get widget width during initialization
            available_width = self.max_width - (2 * self.image_margin)
            
            print(f"[DEBUG] Scaling image {os.path.basename(self.file_path)}: max_width={self.max_width}, available_width={available_width}")
            scaled_pixmap = self._scale_pixmap(pixmap, available_width)
            print(f"[DEBUG] Scaled pixmap size: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
            # Set the pixmap and force the label to match the pixmap size exactly
            self.image_label.setPixmap(scaled_pixmap)
            # Force the image label to be exactly the size of the scaled pixmap
            self.image_label.setFixedSize(scaled_pixmap.size())
            print(f"[DEBUG] Set image label size to: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
            # After image is loaded, calculate and set minimum height to prevent overlapping
            QTimer.singleShot(50, lambda: self._safe_minimum_height_calculation())
            
            # The image label will size to match the pixmap automatically
            
        except Exception as e:
            print(f"[ERROR] Failed to load image {self.file_path}: {e}")
            self._set_error_image(f"Load error: {str(e)}")
    
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
        
    def _on_text_changed(self):
        """Handle text changes in the text edit"""
        new_text = self.text_edit.toPlainText()
        self.text_changed.emit(self.file_path, new_text)
        
        # Auto-adjust text height based on content
        self._adjust_text_height()
    
    def _adjust_text_height(self):
        """Automatically adjust text edit height based on content using document layout"""
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
            
            print(f"[DEBUG] Text height set to minimum ({dynamic_min_height}px) for empty content")
            QTimer.singleShot(100, lambda: self._check_actual_height("empty content"))
            return
        
        # Use document-based height calculation for accurate text wrapping
        current_width = self.text_edit.width()
        if current_width <= 0:
            # If widget hasn't been fully laid out yet, use max_width as fallback
            current_width = self.max_width - 30  # Account for margins
        
        available_width = current_width - 10  # Account for text edit margins
        
        # Get the document and ensure it has the correct width for wrapping
        document = self.text_edit.document()
        if document:
            # Set the document width to force proper wrapping calculation
            document.setTextWidth(available_width)
            
            # Force document to recalculate size with proper width
            document.adjustSize()
            
            # Get the actual document size after wrapping
            doc_size = document.size()
            doc_height = int(doc_size.height())
            
            # Calculate actual line count by measuring text layout
            block_count = document.blockCount()
            
            # Use font metrics to estimate actual wrapped lines
            line_height = font_metrics.height()
            estimated_lines = max(1, doc_height // line_height) if line_height > 0 else 1
            
            # Calculate final height with margins and padding
            margins = self.text_edit.contentsMargins()
            padding = 8
            new_height = doc_height + margins.top() + margins.bottom() + padding
            
            # Apply bounds - ensure minimum height and respect maximum
            optimal_height = max(dynamic_min_height, min(self.text_max_height, new_height))
            
            self.text_edit.setFixedHeight(optimal_height)
            self.text_edit.setMaximumHeight(optimal_height)
            self.text_edit.setMinimumHeight(optimal_height)
            self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            print(f"[DEBUG] Document-based height calculation for {os.path.basename(self.file_path)}:")
            print(f"[DEBUG]   width: {current_width} | available_width: {available_width}")
            print(f"[DEBUG]   content_chars: {len(text_content)} | doc_height: {doc_height} | estimated_lines: {estimated_lines} | final_height: {optimal_height}")
            print(f"[DEBUG]   block_count: {block_count} | line_height: {line_height}")
            
            QTimer.singleShot(100, lambda: self._safe_check_actual_height(f"{len(text_content)} chars ({estimated_lines} lines)"))
            
            # Also update the minimum height to prevent overlapping
            QTimer.singleShot(150, lambda: self._safe_minimum_height_calculation())
        else:
            # Fallback if document is not available - use old method
            print(f"[DEBUG] Document not available, using fallback height calculation")
            self.text_edit.setFixedHeight(dynamic_min_height)
            self.text_edit.setMaximumHeight(dynamic_min_height)
            self.text_edit.setMinimumHeight(dynamic_min_height)
            self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def _safe_check_actual_height(self, description):
        """Safely check actual height with additional widget existence validation"""
        try:
            # Check if this widget instance still exists and is valid
            if hasattr(self, 'text_edit') and self.text_edit is not None:
                # Additional check to see if the widget is still part of a valid parent hierarchy
                if self.text_edit.parent() is not None or not self.text_edit.isHidden():
                    self._check_actual_height(description)
                else:
                    print(f"[DEBUG] Widget orphaned before height check for {description}")
            else:
                print(f"[DEBUG] Widget destroyed before height check for {description}")
        except Exception as e:
            print(f"[DEBUG] Error in safe height check for {description}: {e}")

    def _check_actual_height(self, description):
        """Check and report the actual rendered height of the text edit"""
        # Safety check: ensure the widget still exists and hasn't been deleted
        try:
            if self.text_edit and not self.text_edit.isHidden():
                actual_height = self.text_edit.height()
                size_hint = self.text_edit.sizeHint().height()
                minimum_size = self.text_edit.minimumHeight()
                print(f"[DEBUG] ACTUAL HEIGHT CHECK for {description}:")
                print(f"[DEBUG]   - Set height: {self.text_edit.minimumHeight() if hasattr(self.text_edit, 'minimumHeight') else 'unknown'}")
                print(f"[DEBUG]   - Actual rendered height: {actual_height}px")
                print(f"[DEBUG]   - Size hint: {size_hint}px")
        except RuntimeError:
            # Widget has been deleted, ignore the callback
            print(f"[DEBUG] Widget deleted before height check could complete for {description}")
        except Exception as e:
            print(f"[DEBUG] Error during height check for {description}: {e}")
            print(f"[DEBUG]   - Minimum height: {minimum_size}px")
    
    # Public interface methods
    
    def set_tags(self, tags):
        """Set the tags/metadata text"""
        # Handle various empty tag scenarios
        if not tags or (isinstance(tags, list) and len(tags) == 0):
            tags_text = ""
            print(f"[DEBUG] Setting EMPTY tags for {os.path.basename(self.file_path)}: no tags provided")
        elif isinstance(tags, list):
            # Filter out empty/whitespace-only tags
            valid_tags = [tag.strip() for tag in tags if tag and str(tag).strip()]
            tags_text = ', '.join(valid_tags) if valid_tags else ""
            if not tags_text:
                print(f"[DEBUG] Setting EMPTY tags for {os.path.basename(self.file_path)}: all tags were empty/whitespace")
        else:
            tags_text = str(tags).strip() if tags else ""
            if not tags_text:
                print(f"[DEBUG] Setting EMPTY tags for {os.path.basename(self.file_path)}: tag was empty/whitespace")
            
        self.tags = tags if isinstance(tags, list) else ([tags] if tags else [])
        
        # Debug what we're actually setting
        if tags_text:
            print(f"[DEBUG] Setting tags for {os.path.basename(self.file_path)}: '{tags_text}' (length: {len(tags_text)})")
        
        # Block signals to prevent recursive updates
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(tags_text)
        self.text_edit.blockSignals(False)
        
        # Adjust height after setting text
        QTimer.singleShot(0, self._adjust_text_height)
    
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
        self._update_selection_style()
        self.selection_changed.emit(self.file_path, selected)
    
    def is_selected_state(self):
        """Get current selection state"""
        return self.is_selected
    
    def _update_selection_style(self):
        """Update visual style based on selection state"""
        if self.is_selected:
            self.container_frame.setStyleSheet(f"""
                QFrame {{
                    border: {self.selection_border_width}px solid #0078d4;
                    border-radius: 4px;
                    background-color: #f0f8ff;
                }}
            """)
        else:
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
        """Handle widget resize - disabled to prevent stretching issues"""
        super().resizeEvent(event)
        # Disabled automatic image reloading on resize to prevent stretching
        # Images will be resized when the grid layout changes instead
        pass
    
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
                    print(f"[DEBUG] Widget orphaned before minimum height calculation")
            else:
                print(f"[DEBUG] Widget destroyed before minimum height calculation")
        except Exception as e:
            print(f"[DEBUG] Error in safe minimum height calculation: {e}")

    def _calculate_and_set_minimum_height(self):
        """Calculate and set the minimum height to prevent overlapping"""
        try:
            # Safety check: ensure the widget still exists and hasn't been deleted
            if not hasattr(self, 'image_label') or self.image_label is None:
                print(f"[DEBUG] Widget destroyed before minimum height calculation")
                return
                
            # Additional safety check for widget validity
            if not hasattr(self, 'file_path'):
                print(f"[DEBUG] Widget missing file_path, skipping height calculation")
                return
                
            # Check if image_label has been deleted
            try:
                pixmap_check = self.image_label.pixmap()  # This will throw RuntimeError if deleted
            except RuntimeError:
                print(f"[DEBUG] Image label deleted before height calculation for {os.path.basename(self.file_path) if hasattr(self, 'file_path') else 'unknown'}")
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
                    
                    print(f"[DEBUG] Setting minimum height for {os.path.basename(self.file_path)}: {total_min_height}px (image: {image_height}, text: {text_height})")
                    
                    # Set the minimum height to prevent compression
                    self.setMinimumHeight(total_min_height)
                    if hasattr(self, 'container_frame') and self.container_frame:
                        try:
                            self.container_frame.setMinimumHeight(total_min_height - 10)  # Account for main margins
                        except RuntimeError:
                            print(f"[DEBUG] Container frame deleted during height calculation")
                            
                except RuntimeError as e:
                    print(f"[DEBUG] Widget deleted during height calculation: {e}")
                    
            else:
                # Fallback minimum height
                default_height = 180
                try:
                    self.setMinimumHeight(default_height)
                except RuntimeError:
                    print(f"[DEBUG] Widget deleted before setting default height")
                    
        except Exception as e:
            print(f"[DEBUG] Error in minimum height calculation: {e}")

    def sizeHint(self):
        """Provide size hint for layout"""
        if self.image_label.pixmap():
            image_size = self.image_label.pixmap().size()
            total_height = (image_size.height() + 
                          self.text_edit.height() + 
                          (2 * self.image_margin) + 10)  # spacing + margins
            return QSize(self.max_width, total_height)
        else:
            return QSize(self.max_width, 200)  # default size
    
    def minimumSizeHint(self):
        """Provide minimum size hint"""
        return QSize(150, 150)
    
    # Utility methods
    
    def cleanup(self):
        """Clean up resources and disconnect signals to prevent timer callbacks"""
        try:
            if hasattr(self, 'text_edit') and self.text_edit:
                self.text_edit.textChanged.disconnect()
                self.text_edit = None
            print(f"[DEBUG] Cleaned up ImageCardWidget for {os.path.basename(self.file_path) if hasattr(self, 'file_path') else 'unknown'}")
        except Exception as e:
            print(f"[DEBUG] Error during cleanup: {e}")
    
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
