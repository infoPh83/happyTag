"""
Folder Status Manager Dialog

A QDialog that provides a visual interface for managing folder and file statuses
on the network drive. Features include:
- Tree view of folder hierarchy with lazy loading
- Status dropdown with color coding
- Context menu for bulk operations
- Progress tracking for long operations
- Search and filter capabilities
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QComboBox, QLabel,
                             QLineEdit, QProgressDialog, QMessageBox, QMenu,
                             QHeaderView, QCheckBox, QGroupBox, QTreeWidgetItemIterator,
                             QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QIcon

import os
from typing import Optional, List, Dict, Set
from .path_mapper import PathMapper
from .folder_status_manager import (FolderStatusManager, STATUS_DISCARDED,
                                   STATUS_NOT_EVALUATED, STATUS_REQUIRING_TAGS,
                                   STATUS_TAGGED_LOCAL, STATUS_SYNCED,
                                   STATUS_NOT_FOUND)
from .folder_scanner import FolderScanner, FolderItem, ScanProgress


# Status display configuration
STATUS_CONFIG = {
    STATUS_DISCARDED: {
        'label': 'Discarded',
        'color': QColor(180, 180, 180),  # Gray
        'description': 'Won\'t be processed'
    },
    STATUS_NOT_EVALUATED: {
        'label': 'Not Evaluated',
        'color': QColor(255, 255, 200),  # Light yellow
        'description': 'Default state, needs review'
    },
    STATUS_REQUIRING_TAGS: {
        'label': 'Requiring Tags',
        'color': QColor(255, 200, 100),  # Orange
        'description': 'Selected for tagging'
    },
    STATUS_TAGGED_LOCAL: {
        'label': 'Tagged (Local)',
        'color': QColor(150, 200, 255),  # Light blue
        'description': 'Tagged but not uploaded'
    },
    STATUS_SYNCED: {
        'label': 'Synced',
        'color': QColor(150, 255, 150),  # Light green
        'description': 'Tagged and uploaded to Cloudinary'
    },
    STATUS_NOT_FOUND: {
        'label': 'Not Found',
        'color': QColor(255, 150, 150),  # Light red
        'description': 'Missing from filesystem'
    }
}


class FolderStatusDialog(QDialog):
    """
    Main dialog for managing folder and file statuses.
    
    Features:
    - Tree view with lazy loading
    - Status management with color coding
    - Bulk operations via context menu
    - Progress tracking
    - Search/filter
    """
    
    # Signal emitted when statuses are updated
    statuses_updated = pyqtSignal()
    
    def __init__(self, network_root: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Folder Status Manager")
        self.resize(1000, 700)
        
        # Initialize managers
        self.network_root = network_root
        self.path_mapper = PathMapper(network_root)
        self.status_manager = FolderStatusManager(network_root)
        self.scanner = FolderScanner(network_root, self.status_manager)
        
        # Track loaded items and their tree widget items
        self.loaded_items: Dict[str, FolderItem] = {}  # relative_path -> FolderItem
        self.tree_items: Dict[str, QTreeWidgetItem] = {}  # relative_path -> QTreeWidgetItem
        
        # Current filter settings
        self.filter_text = ""
        self.filter_status: Optional[str] = None
        
        # Selected folder path (set when double-clicking)
        self.selected_folder_path: Optional[str] = None
        
        # Setup UI
        self._setup_ui()
        
        # Load root folders
        self._load_root_folders()
    
    def _setup_ui(self):
        """Create and layout UI components."""
        layout = QVBoxLayout(self)
        
        # Tree view (create first so it can be referenced by other components)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Name', 'Status', 'Images', 'Folders'])
        self.tree.setColumnWidth(0, 350)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 80)
        self.tree.header().setStretchLastSection(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Top section: filters and controls
        top_layout = self._create_top_section()
        layout.addLayout(top_layout)
        
        # Add tree view
        layout.addWidget(self.tree)
        
        # Bottom section: status legend and buttons
        bottom_layout = self._create_bottom_section()
        layout.addLayout(bottom_layout)
    
    def _create_top_section(self) -> QHBoxLayout:
        """Create the top filter and control section."""
        layout = QHBoxLayout()
        
        # Search box
        layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by name...")
        self.search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_box, 1)
        
        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", None)
        for status_code, config in STATUS_CONFIG.items():
            self.status_filter.addItem(config['label'], status_code)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.status_filter)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_tree)
        layout.addWidget(self.refresh_btn)
        
        # Expand all / Collapse all
        self.expand_btn = QPushButton("Expand All")
        self.expand_btn.clicked.connect(self._expand_all)
        layout.addWidget(self.expand_btn)
        
        self.collapse_btn = QPushButton("Collapse All")
        self.collapse_btn.clicked.connect(self.tree.collapseAll)
        layout.addWidget(self.collapse_btn)
        
        return layout
    
    def _create_bottom_section(self) -> QVBoxLayout:
        """Create the bottom legend and button section."""
        layout = QVBoxLayout()
        
        # Status legend
        legend_group = QGroupBox("Status Legend")
        legend_layout = QHBoxLayout()
        
        for status_code, config in STATUS_CONFIG.items():
            label = QLabel(f"■ {config['label']}")
            label.setStyleSheet(f"color: rgb({config['color'].red()}, "
                              f"{config['color'].green()}, "
                              f"{config['color'].blue()});")
            label.setToolTip(config['description'])
            legend_layout.addWidget(label)
        
        legend_layout.addStretch()
        legend_group.setLayout(legend_layout)
        layout.addWidget(legend_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        return layout
    
    def _load_root_folders(self):
        """Load root folders into the tree."""
        try:
            # Show progress dialog
            progress_dlg = QProgressDialog("Scanning root folders...", "Cancel", 0, 100, self)
            progress_dlg.setWindowModality(Qt.WindowModal)
            progress_dlg.setMinimumDuration(500)
            progress_dlg.setAutoClose(False)
            progress_dlg.setAutoReset(False)
            
            # Track last update
            last_update = [0]
            update_interval = 10  # Update every 10 items for root level
            
            # Create progress callback
            def on_progress(scan_progress: ScanProgress):
                if scan_progress.is_cancelled:
                    return
                    
                if progress_dlg.wasCanceled():
                    scan_progress.is_cancelled = True
                    return
                
                # Update less frequently
                total_items = scan_progress.scanned_folders + scan_progress.scanned_files
                if total_items - last_update[0] >= update_interval or scan_progress.get_percentage() >= 100:
                    last_update[0] = total_items
                    progress_dlg.setValue(scan_progress.get_percentage())
                    progress_dlg.setLabelText(f"Scanning: {scan_progress.current_path}")
                    QApplication.processEvents()
            
            # Scan root folders
            root_items = self.scanner.scan_root_folders(progress_callback=on_progress)
            
            progress_dlg.close()
            
            # Add to tree
            self.tree.clear()
            self.loaded_items.clear()
            self.tree_items.clear()
            
            for item in root_items:
                self._add_item_to_tree(item, None)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load folders: {str(e)}")
    
    def _add_item_to_tree(self, folder_item: FolderItem, parent_tree_item: Optional[QTreeWidgetItem]) -> Optional[QTreeWidgetItem]:
        """
        Add a FolderItem to the tree (folders only, no files).
        
        Args:
            folder_item: The folder/file item to add
            parent_tree_item: Parent tree widget item (None for root)
        
        Returns:
            The created QTreeWidgetItem, or None if item is a file (skipped)
        """
        # Skip files - only show folders
        if not folder_item.is_directory:
            return None
        
        # Create tree item
        tree_item = QTreeWidgetItem()
        tree_item.setText(0, folder_item.name)
        # Store path in data for retrieval (not displayed)
        tree_item.setData(0, Qt.UserRole, folder_item.relative_path)
        
        # Store reference
        self.loaded_items[folder_item.relative_path] = folder_item
        self.tree_items[folder_item.relative_path] = tree_item
        
        # Set status
        self._update_tree_item_status(tree_item, folder_item)
        
        # Add to parent or root
        if parent_tree_item:
            parent_tree_item.addChild(tree_item)
        else:
            self.tree.addTopLevelItem(tree_item)
        
        # If it has children, add placeholder or children
        if folder_item.is_loaded:
            # Add only folder children
            for child in folder_item.children:
                if child.is_directory:
                    self._add_item_to_tree(child, tree_item)
        else:
            # Add placeholder to enable expand arrow (if not discarded)
            if folder_item.status != STATUS_DISCARDED:
                placeholder = QTreeWidgetItem()
                placeholder.setText(0, "Loading...")
                tree_item.addChild(placeholder)
        
        return tree_item
    
    def _get_item_path(self, tree_item: QTreeWidgetItem) -> str:
        """Get the relative path stored in a tree item."""
        return tree_item.data(0, Qt.UserRole) or ""
    
    def _update_tree_item_status(self, tree_item: QTreeWidgetItem, folder_item: FolderItem):
        """Update tree item's status display and color."""
        status = folder_item.status
        config = STATUS_CONFIG.get(status, STATUS_CONFIG[STATUS_NOT_EVALUATED])
        
        # Set status text
        tree_item.setText(1, config['label'])
        
        # Set status color
        for col in range(tree_item.columnCount()):
            tree_item.setBackground(col, QBrush(config['color']))
        
        # Set counts (images and folders)
        if folder_item.is_loaded:
            # Count only image files (not all files)
            image_count = sum(1 for c in folder_item.children if not c.is_directory)
            folder_count = sum(1 for c in folder_item.children if c.is_directory)
            tree_item.setText(2, str(image_count))
            tree_item.setText(3, str(folder_count))
        else:
            tree_item.setText(2, "?")
            tree_item.setText(3, "?")
    
    def _on_item_expanded(self, tree_item: QTreeWidgetItem):
        """Handle tree item expansion - load children if not loaded."""
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)
        
        if not folder_item or not folder_item.is_directory:
            return
        
        # If already loaded, nothing to do
        if folder_item.is_loaded:
            return
        
        # Remove placeholder
        tree_item.takeChildren()
        
        try:
            # Show progress dialog for large folders
            progress_dlg = QProgressDialog(f"Scanning {folder_item.name}...", "Cancel", 0, 100, self)
            progress_dlg.setWindowModality(Qt.WindowModal)
            progress_dlg.setMinimumDuration(500)
            progress_dlg.setAutoClose(False)
            progress_dlg.setAutoReset(False)
            
            # Track last update
            last_update = [0]
            update_interval = 20  # Update every 20 items
            
            # Create progress callback
            def on_progress(scan_progress: ScanProgress):
                if scan_progress.is_cancelled:
                    return
                    
                if progress_dlg.wasCanceled():
                    scan_progress.is_cancelled = True
                    return
                
                # Update less frequently
                total_items = scan_progress.scanned_folders + scan_progress.scanned_files
                if total_items - last_update[0] >= update_interval or scan_progress.get_percentage() >= 100:
                    last_update[0] = total_items
                    progress_dlg.setValue(scan_progress.get_percentage())
                    QApplication.processEvents()
            
            # Scan folder contents (non-recursive, just immediate children)
            self.scanner.scan_folder_contents(folder_item, recursive=False, progress_callback=on_progress)
            
            progress_dlg.close()
            
            # Add children to tree
            for child in folder_item.children:
                self._add_item_to_tree(child, tree_item)
            
            # Update counts
            self._update_tree_item_status(tree_item, folder_item)
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to load folder contents: {str(e)}")
    
    def _show_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Get the folder item
        relative_path = self._get_item_path(item)
        folder_item = self.loaded_items.get(relative_path)
        
        if not folder_item:
            return
        
        # Status change actions
        status_menu = menu.addMenu("Set Status")
        for status_code, config in STATUS_CONFIG.items():
            action = status_menu.addAction(config['label'])
            action.triggered.connect(lambda checked, s=status_code: self._set_item_status(item, s, False))
        
        # Recursive status change (folders only)
        if folder_item.is_directory:
            menu.addSeparator()
            recursive_menu = menu.addMenu("Set Folder and Contents")
            for status_code, config in STATUS_CONFIG.items():
                action = recursive_menu.addAction(config['label'])
                action.triggered.connect(lambda checked, s=status_code: self._set_item_status(item, s, True))
        
        # Scan actions
        if folder_item.is_directory:
            menu.addSeparator()
            scan_action = menu.addAction("Deep Scan (Recursive)")
            scan_action.triggered.connect(lambda: self._deep_scan_folder(item))
        
        # Show menu
        menu.exec_(self.tree.viewport().mapToGlobal(position))
    
    def _set_item_status(self, tree_item: QTreeWidgetItem, status: str, recursive: bool):
        """Set status for an item, optionally recursive."""
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)
        
        if not folder_item:
            return
        
        try:
            if recursive and folder_item.is_directory:
                # Show confirmation
                reply = QMessageBox.question(
                    self, 
                    "Confirm Recursive Status Change",
                    f"Set '{folder_item.name}' and all its contents to '{STATUS_CONFIG[status]['label']}'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
                
                # Show progress dialog
                progress_dlg = QProgressDialog(f"Updating statuses for '{folder_item.name}' and contents...", None, 0, 0, self)
                progress_dlg.setWindowModality(Qt.WindowModal)
                progress_dlg.setMinimumDuration(0)
                progress_dlg.setCancelButton(None)  # Can't cancel this operation
                progress_dlg.setAutoClose(True)
                progress_dlg.show()
                QApplication.processEvents()
                
                # Set status recursively
                self.status_manager.set_folder_recursive(relative_path, status, scan_filesystem=True)
                
                progress_dlg.close()
                
                # Reload this folder
                self._reload_folder_item(folder_item, tree_item)
                
            else:
                # Set single item status
                self.status_manager.set_status(relative_path, status)
                folder_item.status = status
                self._update_tree_item_status(tree_item, folder_item)
            
            # Emit signal
            self.statuses_updated.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update status: {str(e)}")
    
    def _deep_scan_folder(self, tree_item: QTreeWidgetItem):
        """Perform a deep recursive scan of a folder."""
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)
        
        if not folder_item or not folder_item.is_directory:
            return
        
        try:
            # Show progress dialog - create once before scanning
            progress_dlg = QProgressDialog(f"Deep scanning {folder_item.name}...", "Cancel", 0, 100, self)
            progress_dlg.setWindowModality(Qt.WindowModal)
            progress_dlg.setMinimumDuration(0)  # Show immediately
            progress_dlg.setAutoClose(False)  # Don't auto-close
            progress_dlg.setAutoReset(False)  # Don't auto-reset
            progress_dlg.show()  # Force show immediately
            
            # Track last update to avoid too frequent updates
            last_update = [0]  # Use list for closure modification
            update_interval = 50  # Update every 50 items
            
            # Create progress callback
            def on_progress(scan_progress: ScanProgress):
                if scan_progress.is_cancelled:
                    return
                    
                # Check if cancelled by user
                if progress_dlg.wasCanceled():
                    scan_progress.is_cancelled = True
                    return
                
                # Update less frequently to avoid UI lag
                total_items = scan_progress.scanned_folders + scan_progress.scanned_files
                if total_items - last_update[0] >= update_interval or scan_progress.get_percentage() >= 100:
                    last_update[0] = total_items
                    progress_dlg.setValue(scan_progress.get_percentage())
                    progress_dlg.setLabelText(f"Scanning: {scan_progress.current_path}\n"
                                            f"Folders: {scan_progress.scanned_folders}/{scan_progress.total_folders} | "
                                            f"Files: {scan_progress.scanned_files}/{scan_progress.total_files}")
                    QApplication.processEvents()  # Allow UI to update
            
            # Scan recursively
            self.scanner.scan_folder_contents(folder_item, recursive=True, progress_callback=on_progress)
            
            progress_dlg.close()
            
            # Rebuild tree for this folder
            tree_item.takeChildren()
            for child in folder_item.children:
                self._add_item_to_tree(child, tree_item)
            
            # Update counts
            self._update_tree_item_status(tree_item, folder_item)
            
            QMessageBox.information(
                self,
                "Scan Complete",
                f"Found {len([c for c in folder_item.children if c.is_directory])} folders "
                f"and {len([c for c in folder_item.children if not c.is_directory])} files."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to scan folder: {str(e)}")
    
    def _reload_folder_item(self, folder_item: FolderItem, tree_item: QTreeWidgetItem):
        """Reload a folder item and update tree."""
        if not folder_item.is_directory:
            return
        
        # Clear children
        folder_item.children.clear()
        folder_item.is_loaded = False
        tree_item.takeChildren()
        
        # Add placeholder
        placeholder = QTreeWidgetItem()
        placeholder.setText(0, "Loading...")
        tree_item.addChild(placeholder)
        
        # Update status
        folder_item.status = self.status_manager.get_status(folder_item.relative_path)
        self._update_tree_item_status(tree_item, folder_item)
    
    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self.filter_text = text.lower()
        self._apply_filters()
    
    def _on_filter_changed(self, index: int):
        """Handle status filter change."""
        self.filter_status = self.status_filter.currentData()
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply current filters to tree."""
        # Simple implementation: show/hide items based on filters
        # For better UX, you could rebuild the tree with filtered results
        
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            relative_path = self._get_item_path(item)
            folder_item = self.loaded_items.get(relative_path)
            
            visible = True
            
            # Text filter
            if self.filter_text and folder_item:
                if self.filter_text not in folder_item.name.lower():
                    visible = False
            
            # Status filter
            if self.filter_status and folder_item:
                if folder_item.status != self.filter_status:
                    visible = False
            
            item.setHidden(not visible)
            iterator += 1
    
    def _refresh_tree(self):
        """Refresh the entire tree."""
        reply = QMessageBox.question(
            self,
            "Confirm Refresh",
            "Reload all folders from network drive? Expanded folders will be collapsed.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._load_root_folders()
    
    def _expand_all(self):
        """Expand all items in the tree."""
        reply = QMessageBox.question(
            self,
            "Confirm Expand All",
            "This will scan all folders recursively. For large folder structures, this may take a while. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tree.expandAll()
    
    def get_selected_paths(self) -> List[str]:
        """Get list of currently selected relative paths."""
        selected_items = self.tree.selectedItems()
        return [self._get_item_path(item) for item in selected_items]
    
    def _on_item_double_clicked(self, tree_item: QTreeWidgetItem, column: int):
        """Handle double-click on folder - load images into main window."""
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)
        
        if not folder_item:
            return
        
        # Get absolute path
        absolute_path = self.path_mapper.to_absolute(relative_path)
        
        if not absolute_path.exists():
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"The folder does not exist:\n\n{absolute_path}"
            )
            return
        
        # Close dialog and signal parent to load folder
        self.accept()
        
        # Emit signal with folder path for parent to handle
        # (Main window will catch this via the accepted signal and load the folder)
        self.selected_folder_path = str(absolute_path)
