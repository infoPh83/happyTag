import sys
import os
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from PyQt5.QtWidgets import (QMainWindow, QApplication, QFileDialog, 
                           QWidget, QLabel, QTextEdit,
                           QVBoxLayout, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI
        uic.loadUi('ui/mainWindow.ui', self)
        
        # Initialize resize timer
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.setInterval(250)  # 250ms delay
        self.resize_timer.timeout.connect(self.update_layout)
        
        # Configure scroll area
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        
        # Minimize margins in the scroll area
        scroll_widget = self.scrollArea.widget()
        scroll_widget.layout().setContentsMargins(5, 5, 5, 5)
        
        # Configure pictures container
        self.picturesContainer.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        
        # Setup grid layout
        self.grid_layout = QGridLayout(self.picturesContainer)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        
        # Connect signals
        self.actionOpenFiles.triggered.connect(self.open_files)
        self.horizontalSlider.valueChanged.connect(self.update_layout)
        
        # Store loaded images
        self.image_files = []
        self.image_previews = {}
        self.image_widgets = []
        
        # Initialize column slider (1-7 columns)
        self.horizontalSlider.setMinimum(1)
        self.horizontalSlider.setMaximum(7)
        self.horizontalSlider.setValue(2)
        
        self.MAX_PREVIEW_SIZE = 800
        self.selected_images = set()
        
    def create_image_widget(self, preview, max_width, file_path):
        """Create a widget containing an image and its input field"""
        print(f"Creating image widget with max_width: {max_width}")
        
        # Calculate scaled size
        ratio = preview.width() / preview.height()
        scaled_width = min(max_width, preview.width())
        scaled_height = int(scaled_width / ratio)
        print(f"Scaled dimensions: {scaled_width}x{scaled_height}")
        
        # Create container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignHCenter)
        
        # Create image container
        image_container = QWidget()
        image_container.setFixedSize(scaled_width, scaled_height)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(0)
        
        # Create image label
        image_label = QLabel()
        image_label.setMouseTracking(True)
        scaled_pixmap = preview.scaled(scaled_width, scaled_height,
                                     Qt.KeepAspectRatio,
                                     Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("""
            QLabel { border: 2px solid transparent; }
            QLabel[selected="true"] { border: 2px solid #0078D4; background-color: rgba(0, 120, 212, 0.1); }
        """)
        image_label.setProperty("selected", False)
        
        # Create filename label
        filename_label = QLabel(os.path.basename(file_path))
        filename_label.setStyleSheet("""
            QLabel { 
                background-color: rgba(0, 0, 0, 0.5);
                color: white;
                padding: 3px 6px;
                border-radius: 3px;
            }
        """)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.adjustSize()
        
        # Stack labels
        image_layout.addWidget(image_label)
        filename_label.setParent(image_container)
        filename_label.move(5, 5)
        
        # Create input field
        input_field = QTextEdit()
        input_field.setFixedWidth(scaled_width)
        input_field.setFixedHeight(28)
        input_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
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
        
        def sync_tags(source_field):
            """Sync the last tag from source field to other selected fields"""
            if not source_field.property("selected"):
                return
                
            current_text = source_field.toPlainText().strip()
            if not current_text:
                return
                
            # Get the last word/tag
            words = [w.strip() for w in current_text.split(',')]
            last_word = words[-1].strip() if words else ""
            
            if not last_word:
                return
                
            print(f"Syncing tag: {last_word}")
            for widget in self.image_widgets:
                if (hasattr(widget, 'file_path') and 
                    widget.file_path in self.selected_images and 
                    widget.input_field != source_field):
                    
                    target = widget.input_field
                    target._updating = True
                    existing = target.toPlainText().strip()
                    
                    if existing:
                        if not existing.endswith(','):
                            existing += ','
                        existing += ' '
                        target.setText(f"{existing}{last_word}")
                    else:
                        target.setText(last_word)
                        
                    target._updating = False
        
        def updateHeight():
            if not input_field.hasFocus():
                return
                
            content = input_field.toPlainText()
            if not content:
                input_field.setFixedHeight(28)
                return
                
            doc_width = input_field.viewport().width()
            text_width = input_field.fontMetrics().horizontalAdvance(content)
            current_height = input_field.height()
            
            if (text_width > (doc_width - 10) and current_height == 28) or \
               (text_width <= (doc_width - 10) and current_height > 28):
                doc_height = int(input_field.document().size().height())
                margins = input_field.contentsMargins()
                padding = 8
                new_height = doc_height + margins.top() + margins.bottom() + padding
                input_field.setFixedHeight(max(28, min(new_height, 100)))
        
        resize_timer = QTimer(input_field)
        resize_timer.setSingleShot(True)
        resize_timer.setInterval(100)
        
        def onTextChanged():
            if input_field._updating:
                return
                
            resize_timer.start()
            current_text = input_field.toPlainText()
            
            # Only sync on space, comma, or if it's a forced sync
            if current_text.endswith(' ') or current_text.endswith(','):
                sync_tags(input_field)
        
        resize_timer.timeout.connect(updateHeight)
        input_field.textChanged.connect(onTextChanged)
        
        def focusOutEvent(event):
            QTextEdit.focusOutEvent(input_field, event)
            sync_tags(input_field)  # Sync on focus loss
            
            content = input_field.toPlainText()
            if content:
                doc_width = input_field.viewport().width()
                text_width = input_field.fontMetrics().horizontalAdvance(content)
                if text_width <= (doc_width - 10):
                    input_field.setFixedHeight(28)
        
        input_field.focusOutEvent = focusOutEvent
        
        # Initial text (year)
        year = self.get_image_year(file_path)
        if year:
            input_field.setText(f"{year}, ")
        else:
            input_field.setPlaceholderText("Enter tags...")
        
        # Add widgets to layout
        layout.addWidget(image_container)
        layout.addWidget(input_field)
        
        # Store references
        container.file_path = file_path
        container.image_label = image_label
        container.input_field = input_field
        
        def update_selection_state(selected):
            image_label.setProperty("selected", selected)
            input_field.setProperty("selected", selected)
            image_label.style().polish(image_label)
            input_field.style().polish(input_field)
        
        def mousePressEvent(event):
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                if file_path in self.selected_images:
                    self.selected_images.remove(file_path)
                    update_selection_state(False)
                else:
                    self.selected_images.add(file_path)
                    update_selection_state(True)
            else:
                for widget in self.image_widgets:
                    if hasattr(widget, 'file_path'):
                        path = widget.file_path
                        if path != file_path and path in self.selected_images:
                            if hasattr(widget, 'image_label') and hasattr(widget, 'input_field'):
                                widget.image_label.setProperty("selected", False)
                                widget.input_field.setProperty("selected", False)
                                widget.image_label.style().polish(widget.image_label)
                                widget.input_field.style().polish(widget.input_field)
                
                self.selected_images = {file_path}
                update_selection_state(True)
            
            self.update_status_bar()
        
        def inputFieldMousePress(event):
            layout.clicked = True
            QTextEdit.mousePressEvent(input_field, event)
        
        def imageContainerMousePress(event):
            layout.clicked = True
            mousePressEvent(event)
        
        image_container.mousePressEvent = imageContainerMousePress
        input_field.mousePressEvent = inputFieldMousePress
        
        # Initialize updating flag
        input_field._updating = False
        
        return container
