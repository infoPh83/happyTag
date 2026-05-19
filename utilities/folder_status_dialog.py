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
                                   STATUS_DISMISSED, STATUS_NEW, STATUS_WATCHED,
                                   STATUS_NOT_FOUND, STATUS_NOT_EVALUATED,
                                   FILE_STATUS_ON_CLOUD, FILE_STATUS_DISMISSED,
                                   FILE_STATUS_NEW, FILE_STATUS_NOT_FOUND)
from .folder_scanner import FolderScanner, FolderItem, ScanProgress


# Status display configuration
STATUS_CONFIG = {
    STATUS_DISMISSED: {
        'label': 'Dismissed',
        'color': QColor(180, 180, 180),  # Gray
        'description': 'Images dismissed from workflow'
    },
    STATUS_NEW: {
        'label': 'New',
        'color': QColor(255, 255, 200),  # Light yellow
        'description': 'New images, not yet processed'
    },
    STATUS_WATCHED: {
        'label': 'Watched',
        'color': QColor(150, 200, 255),  # Light blue
        'description': 'Folder being monitored'
    },
    STATUS_NOT_FOUND: {
        'label': 'Not Found',
        'color': QColor(255, 150, 150),  # Light red
        'description': 'Missing from filesystem'
    },
    STATUS_DISCARDED: {
        'label': 'Discarded',
        'color': QColor(220, 220, 220),  # Light gray
        'description': 'Won\'t be processed (deprecated)'
    },
    # Legacy statuses for migration
    STATUS_NOT_EVALUATED: {
        'label': 'Not Evaluated (Legacy)',
        'color': QColor(255, 230, 180),  # Pale orange
        'description': 'Will be converted to Watched'
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
        self.tree.setHeaderLabels(['Name', 'Status', 'Tot. Images', 'On Cloud', 'Dismissed', 'New', 'Folders'])
        self.tree.setColumnWidth(0, 300)  # Name
        self.tree.setColumnWidth(1, 120)  # Status
        self.tree.setColumnWidth(2, 90)   # Tot. Images
        self.tree.setColumnWidth(3, 80)   # On Cloud
        self.tree.setColumnWidth(4, 80)   # Dismissed
        self.tree.setColumnWidth(5, 60)   # New
        self.tree.setColumnWidth(6, 70)   # Folders
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
            
            # Now reconcile each root folder with the repository
            total_roots = len(root_items)
            progress_dlg.setLabelText("Reconciling with repository...")
            progress_dlg.setMaximum(total_roots)
            
            for idx, item in enumerate(root_items):
                if progress_dlg.wasCanceled():
                    break
                
                progress_dlg.setValue(idx)
                progress_dlg.setLabelText(f"Reconciling {item.name}...")
                QApplication.processEvents()
                
                # Reconcile this folder
                try:
                    recon_result = self.status_manager.reconcile_folder_with_filesystem(
                        item.relative_path, 
                        progress_callback=None  # No sub-progress for now
                    )
                    # Store reconciliation results for tree display
                    item.recon_result = recon_result
                except Exception as e:
                    print(f"Error reconciling {item.name}: {e}")
                    item.recon_result = None
            
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
        
        # Migrate legacy status
        if status == STATUS_NOT_EVALUATED:
            status = STATUS_WATCHED
            folder_item.status = STATUS_WATCHED
        
        config = STATUS_CONFIG.get(status, STATUS_CONFIG[STATUS_WATCHED])
        
        # Set status text
        tree_item.setText(1, config['label'])
        
        # Set status color
        for col in range(tree_item.columnCount()):
            tree_item.setBackground(col, QBrush(config['color']))
        
        # Set counts based on reconciliation results
        if hasattr(folder_item, 'recon_result') and folder_item.recon_result is not None:
            recon = folder_item.recon_result
            
            # Handle different scenarios based on reconciliation result
            if isinstance(recon, dict):
                # Scenario 5: WATCHED folder with detailed counts
                total_images = recon.get('total_images', 0)
                on_cloud = recon.get('on_cloud', 0)
                dismissed = recon.get('dismissed', 0)
                new = recon.get('new', 0)
                folders = recon.get('folders', 0)
                
                tree_item.setText(2, str(total_images))
                tree_item.setText(3, str(on_cloud))
                tree_item.setText(4, str(dismissed))
                tree_item.setText(5, str(new))
                tree_item.setText(6, str(folders))
                
            elif recon == "-":
                # Scenario 1: DISMISSED folder - show dashes
                tree_item.setText(2, "-")
                tree_item.setText(3, "-")
                tree_item.setText(4, "-")
                tree_item.setText(5, "-")
                tree_item.setText(6, "-")
                
            else:
                # Scenarios 2, 3, 4: NEW or NOT_FOUND folders
                # Count from filesystem (folder_item.children)
                if folder_item.is_loaded:
                    image_count = sum(1 for c in folder_item.children if not c.is_directory)
                    folder_count = sum(1 for c in folder_item.children if c.is_directory)
                    
                    tree_item.setText(2, str(image_count))
                    tree_item.setText(3, "0")  # No cloud data for new folders
                    tree_item.setText(4, "0")
                    tree_item.setText(5, str(image_count))  # All are "new"
                    tree_item.setText(6, str(folder_count))
                else:
                    tree_item.setText(2, "?")
                    tree_item.setText(3, "?")
                    tree_item.setText(4, "?")
                    tree_item.setText(5, "?")
                    tree_item.setText(6, "?")
        
        elif folder_item.is_loaded:
            # No reconciliation data yet, count from filesystem
            image_count = sum(1 for c in folder_item.children if not c.is_directory)
            folder_count = sum(1 for c in folder_item.children if c.is_directory)
            
            tree_item.setText(2, str(image_count))
            tree_item.setText(3, "0")
            tree_item.setText(4, "0")
            tree_item.setText(5, str(image_count))
            tree_item.setText(6, str(folder_count))
        else:
            # Not loaded yet
            tree_item.setText(2, "?")
            tree_item.setText(3, "?")
            tree_item.setText(4, "?")
            tree_item.setText(5, "?")
            tree_item.setText(6, "?")
    
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
            
            # Reconcile this folder with the repository
            progress_dlg.setLabelText(f"Reconciling {folder_item.name}...")
            progress_dlg.setValue(50)  # Mid-point indicator
            QApplication.processEvents()
            
            try:
                recon_result = self.status_manager.reconcile_folder_with_filesystem(
                    folder_item.relative_path,
                    progress_callback=None  # No sub-progress for now
                )
                folder_item.recon_result = recon_result
            except Exception as e:
                print(f"Error reconciling {folder_item.name}: {e}")
                folder_item.recon_result = None
            
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
        
        # Convert to Path object for checking
        from pathlib import Path
        path_obj = Path(absolute_path)
        
        if not path_obj.exists():
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"The folder does not exist:\n\n{absolute_path}"
            )
            return
        
        # Don't close dialog - keep it open for multiple folder selections
        # Instead, emit a signal that the parent can catch
        self.selected_folder_path = absolute_path
        
        # Get the parent window and call load_folder_direct
        parent = self.parent()
        if parent and hasattr(parent, 'load_folder_direct'):
            parent.load_folder_direct(absolute_path)
