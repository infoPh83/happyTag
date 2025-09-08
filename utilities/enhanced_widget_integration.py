# utilities/enhanced_widget_integration.py
"""
Enhanced Widget Integration - Non-disruptive approach

This integration enhances the existing widget system without breaking
the current workflow. It adds new capabilities on top of the existing
create_image_widget method.
"""

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QPixmap

class EnhancedImageWidget(QWidget):
    """
    Enhanced version of the image widget that wraps around the existing
    widget structure and adds new capabilities.
    """
    
    # Signals for enhanced functionality
    enhanced_tags_changed = pyqtSignal(str, list)  # file_path, tags_list
    enhanced_selection_changed = pyqtSignal(str, bool)  # file_path, selected
    
    def __init__(self, original_widget, file_path):
        super().__init__()
        
        self.file_path = file_path
        self.original_widget = original_widget
        self.input_field = original_widget.input_field  # Maintain compatibility
        self.is_selected = False
        
        # Setup enhanced layout
        self._setup_enhanced_layout()
        
        # Connect to existing input field
        self._connect_existing_input()
        
        # Setup selection handling
        self._setup_selection_handling()
    
    def _setup_enhanced_layout(self):
        """Setup the enhanced layout wrapping the original widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add the original widget
        layout.addWidget(self.original_widget)
        
        # Add enhancement panel (initially hidden)
        self.enhancement_panel = self._create_enhancement_panel()
        layout.addWidget(self.enhancement_panel)
        self.enhancement_panel.hide()
    
    def _create_enhancement_panel(self):
        """Create panel with enhanced features"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 120, 212, 0.1);
                border: 1px solid #0078D4;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Quick action buttons
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self.toggle_selection)
        select_btn.setMaximumWidth(50)
        
        copy_tags_btn = QPushButton("Copy Tags")
        copy_tags_btn.clicked.connect(self.copy_tags_to_clipboard)
        copy_tags_btn.setMaximumWidth(70)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_tags)
        clear_btn.setMaximumWidth(50)
        
        layout.addWidget(select_btn)
        layout.addWidget(copy_tags_btn)
        layout.addWidget(clear_btn)
        layout.addStretch()
        
        return panel
    
    def _connect_existing_input(self):
        """Connect to the existing input field"""
        # Monitor text changes
        self.input_field.textChanged.connect(self._on_text_changed)
        
        # Add context menu for enhanced features
        self.input_field.setContextMenuPolicy(Qt.CustomContextMenu)
        self.input_field.customContextMenuRequested.connect(self._show_context_menu)
    
    def _setup_selection_handling(self):
        """Setup click handling for selection"""
        # Install event filter on the original widget to capture clicks
        self.original_widget.installEventFilter(self)
        
        # Also install on the input field
        self.input_field.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle mouse events for selection"""
        if event.type() == event.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # Check if Ctrl is pressed for multi-selection
                ctrl_pressed = event.modifiers() & Qt.ControlModifier
                
                if ctrl_pressed:
                    self.toggle_selection()
                    return True
        
        return super().eventFilter(obj, event)
    
    def _on_text_changed(self):
        """Handle text changes in the input field"""
        text = self.input_field.toPlainText()
        tags = [tag.strip() for tag in text.split(',') if tag.strip()]
        self.enhanced_tags_changed.emit(self.file_path, tags)
    
    def _show_context_menu(self, position):
        """Show enhanced context menu"""
        from PyQt5.QtWidgets import QMenu, QAction
        
        menu = QMenu(self)
        
        # Selection actions
        if self.is_selected:
            deselect_action = QAction("Deselect", self)
            deselect_action.triggered.connect(self.deselect)
            menu.addAction(deselect_action)
        else:
            select_action = QAction("Select", self)
            select_action.triggered.connect(self.select)
            menu.addAction(select_action)
        
        menu.addSeparator()
        
        # Tag actions
        copy_action = QAction("Copy Tags", self)
        copy_action.triggered.connect(self.copy_tags_to_clipboard)
        menu.addAction(copy_action)
        
        paste_action = QAction("Paste Tags", self)
        paste_action.triggered.connect(self.paste_tags_from_clipboard)
        menu.addAction(paste_action)
        
        clear_action = QAction("Clear Tags", self)
        clear_action.triggered.connect(self.clear_tags)
        menu.addAction(clear_action)
        
        menu.addSeparator()
        
        # Enhanced features
        show_panel_action = QAction("Show Tools", self)
        show_panel_action.triggered.connect(self.show_enhancement_panel)
        menu.addAction(show_panel_action)
        
        menu.exec_(self.input_field.mapToGlobal(position))
    
    # Public interface methods
    
    def select(self):
        """Select this widget"""
        if not self.is_selected:
            self.is_selected = True
            self._update_selection_style()
            self.enhanced_selection_changed.emit(self.file_path, True)
    
    def deselect(self):
        """Deselect this widget"""
        if self.is_selected:
            self.is_selected = False
            self._update_selection_style()
            self.enhanced_selection_changed.emit(self.file_path, False)
    
    def toggle_selection(self):
        """Toggle selection state"""
        if self.is_selected:
            self.deselect()
        else:
            self.select()
    
    def _update_selection_style(self):
        """Update visual style based on selection state"""
        self.input_field.setProperty("selected", self.is_selected)
        self.input_field.style().polish(self.input_field)
        
        # Also update image label if it exists
        if hasattr(self.original_widget, 'findChild'):
            image_label = self.original_widget.findChild(QLabel)
            if image_label and image_label.pixmap():
                image_label.setProperty("selected", self.is_selected)
                image_label.style().polish(image_label)
    
    def get_tags(self):
        """Get current tags as list"""
        text = self.input_field.toPlainText()
        return [tag.strip() for tag in text.split(',') if tag.strip()]
    
    def set_tags(self, tags):
        """Set tags from list"""
        text = ', '.join(tags) if tags else ''
        self.input_field.setText(text)
    
    def clear_tags(self):
        """Clear all tags"""
        self.input_field.clear()
    
    def copy_tags_to_clipboard(self):
        """Copy tags to clipboard"""
        from PyQt5.QtWidgets import QApplication
        
        text = self.input_field.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        print(f"[DEBUG] Copied tags to clipboard: {text}")
    
    def paste_tags_from_clipboard(self):
        """Paste tags from clipboard"""
        from PyQt5.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.input_field.setText(text)
            print(f"[DEBUG] Pasted tags from clipboard: {text}")
    
    def show_enhancement_panel(self):
        """Show the enhancement panel"""
        self.enhancement_panel.show()
        
        # Hide after 5 seconds
        QTimer.singleShot(5000, self.enhancement_panel.hide)


class EnhancedImageManager:
    """
    Manager for enhanced image widgets that works alongside the existing system.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.enhanced_widgets = {}  # {file_path: EnhancedImageWidget}
        self.selected_files = set()
        
        # Connect to existing update_layout to enhance widgets after they're created
        self._wrap_existing_methods()
    
    def _wrap_existing_methods(self):
        """Wrap existing methods to add enhancement"""
        # Store original update_layout method
        self.original_update_layout = self.main_window.update_layout
        
        # Replace with enhanced version
        self.main_window.update_layout = self._enhanced_update_layout
    
    def _enhanced_update_layout(self, value=None):
        """Enhanced version of update_layout that adds enhancements after layout"""
        # Call original update_layout first
        self.original_update_layout(value)
        
        # Enhance the widgets that were just created
        self._enhance_existing_widgets()
    
    def _enhance_existing_widgets(self):
        """Add enhancements to the widgets created by update_layout"""
        # Clear previous enhanced widgets
        self.enhanced_widgets.clear()
        
        # Enhance each widget created by the original system
        for widget in self.main_window.image_widgets:
            if hasattr(widget, 'file_path'):
                file_path = widget.file_path
                
                # Create enhanced wrapper
                enhanced_widget = EnhancedImageWidget(widget, file_path)
                
                # Connect signals
                enhanced_widget.enhanced_tags_changed.connect(self._on_enhanced_tags_changed)
                enhanced_widget.enhanced_selection_changed.connect(self._on_enhanced_selection_changed)
                
                # Store reference
                self.enhanced_widgets[file_path] = enhanced_widget
                
                print(f"[DEBUG] Enhanced widget created for {os.path.basename(file_path)}")
    
    def _on_enhanced_tags_changed(self, file_path, tags):
        """Handle enhanced tags changed"""
        print(f"[DEBUG] Enhanced tags changed for {os.path.basename(file_path)}: {tags}")
    
    def _on_enhanced_selection_changed(self, file_path, selected):
        """Handle enhanced selection changed"""
        if selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)
        
        print(f"[DEBUG] Enhanced selection: {len(self.selected_files)} files selected")
    
    # Public interface methods
    
    def get_enhanced_widget(self, file_path):
        """Get enhanced widget for file path"""
        return self.enhanced_widgets.get(file_path)
    
    def get_selected_files(self):
        """Get list of selected files"""
        return list(self.selected_files)
    
    def select_all(self):
        """Select all enhanced widgets"""
        for widget in self.enhanced_widgets.values():
            widget.select()
    
    def deselect_all(self):
        """Deselect all enhanced widgets"""
        for widget in self.enhanced_widgets.values():
            widget.deselect()
        self.selected_files.clear()
    
    def apply_tags_to_selected(self, tags):
        """Apply tags to all selected widgets"""
        for file_path in self.selected_files:
            widget = self.enhanced_widgets.get(file_path)
            if widget:
                widget.set_tags(tags)


# Integration function
def integrate_enhanced_widgets(main_window):
    """
    Integrate enhanced widgets with the existing system.
    
    This is a non-disruptive integration that adds new capabilities
    without breaking the existing workflow.
    """
    
    # Create enhanced manager
    enhanced_manager = EnhancedImageManager(main_window)
    
    # Add convenience methods to main window
    main_window.get_enhanced_widget = enhanced_manager.get_enhanced_widget
    main_window.get_selected_files_enhanced = enhanced_manager.get_selected_files
    main_window.select_all_enhanced = enhanced_manager.select_all
    main_window.deselect_all_enhanced = enhanced_manager.deselect_all
    main_window.apply_tags_to_selected = enhanced_manager.apply_tags_to_selected
    
    # Store reference
    main_window.enhanced_manager = enhanced_manager
    
    print("[DEBUG] Enhanced widget system integrated successfully - existing workflow preserved")
    
    return enhanced_manager
