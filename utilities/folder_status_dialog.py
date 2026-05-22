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
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Set
from .path_mapper import PathMapper
from .folder_status_manager import (FolderStatusManager,
                                   STATUS_DISMISSED, STATUS_NEW, STATUS_WATCHED,
                                   STATUS_NOT_FOUND,
                                   FILE_STATUS_ON_CLOUD, FILE_STATUS_DISMISSED,
                                   FILE_STATUS_NEW, FILE_STATUS_NOT_FOUND)
from .folder_scanner import FolderScanner, FolderItem, ScanProgress


# Status display configuration
STATUS_CONFIG = {
    STATUS_DISMISSED: {
        'label': 'Dismissed',
        'color': QColor(180, 180, 180),  # Gray
        'description': 'Folder dismissed from workflow'
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
        
        # Defer loading root folders until dialog is shown
        QTimer.singleShot(0, self._load_root_folders)
    
    def _setup_ui(self):
        """Create and layout UI components."""
        layout = QVBoxLayout(self)
        
        # Tree view (create first so it can be referenced by other components)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Name', 'Status', 'Direct', 'Nested', 'On Cloud', 'Dismissed', 'New'])
        self.tree.setColumnWidth(0, 300)  # Name
        self.tree.setColumnWidth(1, 120)  # Status
        self.tree.setColumnWidth(2, 70)   # Direct
        self.tree.setColumnWidth(3, 70)   # Nested
        self.tree.setColumnWidth(4, 80)   # On Cloud
        self.tree.setColumnWidth(5, 80)   # Dismissed
        self.tree.setColumnWidth(6, 60)   # New
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
        """Load root folders into the tree.
        
        On first launch (no CSV): seeds the full folder hierarchy (dirs only)
        as dismissed, then loads.  On subsequent launches: only reconciles
        watched folders; dismissed folders are shown as-is from CSV.
        """
        try:
            # Ensure DB is loaded (sets is_fresh_db flag)
            self.status_manager.load_status_db()

            # First launch: seed entire folder structure
            if self.status_manager.is_fresh_db:
                self._run_first_launch_seed()

            # Collect root items from CSV + quick filesystem check for new folders
            root_items = self._collect_root_items()

            # Reconcile watched folders only
            watched = [item for item in root_items if item.status == STATUS_WATCHED]
            if watched:
                progress_dlg = QProgressDialog("Reconciling watched folders...", "Cancel",
                                               0, len(watched), self)
                progress_dlg.setWindowModality(Qt.WindowModal)
                progress_dlg.setMinimumDuration(300)

                for idx, item in enumerate(watched):
                    if progress_dlg.wasCanceled():
                        break
                    progress_dlg.setValue(idx)
                    progress_dlg.setLabelText(f"Reconciling: {item.name}...")
                    QApplication.processEvents()
                    try:
                        item.recon_result = self.status_manager.reconcile_folder_with_filesystem(
                            item.relative_path, progress_callback=None
                        )
                    except Exception as e:
                        item.recon_result = None

                progress_dlg.close()

            # Build tree
            self.tree.clear()
            self.loaded_items.clear()
            self.tree_items.clear()

            for item in root_items:
                self._add_item_to_tree(item, None)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load folders: {str(e)}")

    def _run_first_launch_seed(self):
        """Show progress and run seed_folder_structure on first launch."""
        progress_dlg = QProgressDialog(
            "First launch: building folder structure...", None, 0, 0, self)
        progress_dlg.setWindowModality(Qt.WindowModal)
        progress_dlg.setMinimumDuration(0)
        progress_dlg.setCancelButton(None)
        progress_dlg.show()
        QApplication.processEvents()

        counter = [0]

        def on_progress(rel_path):
            counter[0] += 1
            if counter[0] % 50 == 0:
                label = rel_path if len(rel_path) <= 70 else '...' + rel_path[-67:]
                progress_dlg.setLabelText(f"Scanning: {label}")
                QApplication.processEvents()

        added, skipped = self.status_manager.seed_folder_structure(on_progress)
        progress_dlg.close()

    def _collect_root_items(self) -> List[FolderItem]:
        """Build root-level FolderItems from CSV + filesystem check.
        
        Folders in CSV: shown with their CSV status.
        New folders found on filesystem (not in CSV): added as STATUS_NEW.
        CSV folders no longer on filesystem: shown as STATUS_NOT_FOUND.
        """
        cache = self.status_manager._status_cache
        network_root = Path(self.network_root)
        new_added = False

        # What's on the filesystem at root level
        fs_folders: Dict[str, str] = {}  # rel_path -> name
        try:
            for p in sorted(network_root.iterdir(), key=lambda x: x.name.lower()):
                if p.is_dir() and not p.name.startswith('.'):
                    rel = self.path_mapper.to_relative(str(p))
                    if rel:
                        fs_folders[rel] = p.name
        except Exception:
            pass

        # CSV root entries (immediate children = no '/' in path)
        csv_roots = {
            k: v for k, v in cache.items()
            if '/' not in k and v.get('item_type') == 'folder'
        }

        root_items: List[FolderItem] = []

        # Filesystem folders first
        for rel_path, name in fs_folders.items():
            csv_data = csv_roots.get(rel_path)
            if csv_data:
                status = csv_data['status']
            else:
                # Brand-new folder — add to cache as new
                cache[rel_path] = {
                    'item_type': 'folder',
                    'status': STATUS_NEW,
                    'cloudinary_id': '', 'cloudinary_url': '',
                    'original_size': '', 'upload_size': '',
                    'upload_date': '',
                    'last_modified': datetime.now().isoformat(),
                    'notes': 'Auto-discovered'
                }
                status = STATUS_NEW
                new_added = True

            item = FolderItem(relative_path=rel_path, is_directory=True,
                              name=name, parent_path=None)
            item.status = status
            item.is_loaded = False
            item.recon_result = None
            root_items.append(item)

        # CSV-only roots (no longer on filesystem)
        for rel_path, csv_data in csv_roots.items():
            if rel_path not in fs_folders:
                item = FolderItem(relative_path=rel_path, is_directory=True,
                                  name=rel_path.split('/')[-1], parent_path=None)
                item.status = STATUS_NOT_FOUND
                item.is_loaded = False
                item.recon_result = None
                root_items.append(item)

        if new_added:
            self.status_manager.save_status_db()

        return sorted(root_items, key=lambda x: x.name.lower())
    
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
            # Add expand arrow if:
            #   - non-dismissed folder (will scan filesystem on expand), OR
            #   - dismissed folder that has known children in the CSV cache
            needs_arrow = (
                folder_item.status != STATUS_DISMISSED
                or self.status_manager.has_child_folders(folder_item.relative_path)
            )
            if needs_arrow:
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
        
        config = STATUS_CONFIG.get(status, STATUS_CONFIG[STATUS_WATCHED])
        
        # Set status text
        tree_item.setText(1, config['label'])
        
        # Set status color
        for col in range(tree_item.columnCount()):
            tree_item.setBackground(col, QBrush(config['color']))
        
        # Dismissed folders show only name + status; count columns are left blank
        if folder_item.status == STATUS_DISMISSED:
            for col in range(2, 7):
                tree_item.setText(col, '')
            return
        
        # Set counts based on reconciliation results
        if hasattr(folder_item, 'recon_result') and folder_item.recon_result is not None:
            recon = folder_item.recon_result
            
            if isinstance(recon, dict):
                direct = recon.get('direct')
                nested = recon.get('nested')
                on_cloud = recon.get('on_cloud')
                dismissed = recon.get('dismissed')
                new = recon.get('new')
                
                tree_item.setText(2, '' if direct is None else str(direct))
                tree_item.setText(3, '' if nested is None else str(nested))
                tree_item.setText(4, '' if on_cloud is None else str(on_cloud))
                tree_item.setText(5, '' if dismissed is None else str(dismissed))
                tree_item.setText(6, '' if new is None else str(new))
            else:
                for col in range(2, 7):
                    tree_item.setText(col, '?')
        else:
            # Not yet reconciled
            for col in range(2, 7):
                tree_item.setText(col, '?')
    
    def _on_item_expanded(self, tree_item: QTreeWidgetItem):
        """Handle tree item expansion - load children if not loaded.
        
        Dismissed folders: children are loaded from the CSV cache (no filesystem access).
        Watched/New folders: immediate children are scanned from the filesystem;
          only non-dismissed children are reconciled.
        """
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)

        if not folder_item or not folder_item.is_directory:
            return

        if folder_item.is_loaded:
            return

        tree_item.takeChildren()

        try:
            if folder_item.status == STATUS_DISMISSED:
                # ── Dismissed: load sub-folders from CSV cache (no filesystem) ──
                children = self.status_manager.get_immediate_child_folders(
                    folder_item.relative_path
                )
                for child_data in children:
                    child_item = FolderItem(
                        relative_path=child_data['rel_path'],
                        is_directory=True,
                        name=child_data['name'],
                        parent_path=folder_item.relative_path
                    )
                    child_item.status = child_data['status']
                    child_item.recon_result = None
                    child_item.is_loaded = False
                    folder_item.add_child(child_item)

            else:
                # ── Watched / New: scan filesystem ──
                folder_path = Path(self.path_mapper.to_absolute(folder_item.relative_path))

                for child_path in sorted(folder_path.iterdir(),
                                         key=lambda p: p.name.lower()):
                    if child_path.name.startswith('.'):
                        continue
                    if not child_path.is_dir():
                        continue  # tree shows folders only

                    child_rel = self.path_mapper.to_relative(str(child_path))
                    if not child_rel:
                        continue

                    child_item = FolderItem(
                        relative_path=child_rel,
                        is_directory=True,
                        name=child_path.name,
                        parent_path=folder_item.relative_path
                    )
                    child_item.status = self.status_manager.get_status(child_rel)

                    # Only reconcile non-dismissed children (dismissed have no counts)
                    if child_item.status != STATUS_DISMISSED:
                        try:
                            child_item.recon_result = (
                                self.status_manager.reconcile_folder_with_filesystem(
                                    child_rel, progress_callback=None
                                )
                            )
                        except Exception:
                            child_item.recon_result = None
                    else:
                        child_item.recon_result = None

                    folder_item.add_child(child_item)

            folder_item.is_loaded = True

            for child in folder_item.children:
                self._add_item_to_tree(child, tree_item)

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
            rescan_action = menu.addAction("Re-scan Folder Structure")
            rescan_action.setToolTip("Add any new sub-folders (as Dismissed) without full image scan")
            rescan_action.triggered.connect(lambda: self._rescan_folder_structure(item))

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
            if status == STATUS_DISMISSED and folder_item.is_directory:
                # Dismissing a folder deletes all its tracked descendants from the DB
                reply = QMessageBox.question(
                    self,
                    "Confirm Dismiss",
                    f"Dismiss '{folder_item.name}'?\n\nThis will remove all its tracked images from the database.",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                
                success, msg = self.status_manager.dismiss_folder(relative_path)
                if success:
                    folder_item.status = STATUS_DISMISSED
                    self._update_tree_item_status(tree_item, folder_item)
                
            elif recursive and folder_item.is_directory:
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
                progress_dlg.setCancelButton(None)
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
    
    def _rescan_folder_structure(self, tree_item: QTreeWidgetItem):
        """Walk a folder on the filesystem and add any new sub-folders as dismissed.
        
        Does NOT scan for images — it only updates the folder hierarchy in the CSV.
        Existing entries (including watched sub-folders) are never overwritten.
        """
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)
        if not folder_item or not folder_item.is_directory:
            return

        abs_path = self.path_mapper.to_absolute(relative_path)

        progress_dlg = QProgressDialog(
            f"Scanning folder structure: {folder_item.name}...",
            "Cancel", 0, 0, self
        )
        progress_dlg.setWindowModality(Qt.WindowModal)
        progress_dlg.setMinimumDuration(0)
        progress_dlg.show()
        QApplication.processEvents()

        cache = self.status_manager._status_cache
        now = datetime.now().isoformat()
        added = 0
        cancelled = False

        for dirpath, dirnames, _ in os.walk(abs_path):
            dirnames[:] = sorted([d for d in dirnames if not d.startswith('.')])

            rel = self.path_mapper.to_relative(dirpath)
            if not rel or rel == '.' or rel == relative_path:
                continue  # skip the folder itself

            if rel not in cache:
                cache[rel] = {
                    'item_type': 'folder',
                    'status': STATUS_DISMISSED,
                    'cloudinary_id': '', 'cloudinary_url': '',
                    'original_size': '', 'upload_size': '',
                    'upload_date': '',
                    'last_modified': now,
                    'notes': 'Discovered on rescan'
                }
                added += 1

            label = rel if len(rel) <= 70 else '...' + rel[-67:]
            progress_dlg.setLabelText(f"Scanning: {label}")
            QApplication.processEvents()

            if progress_dlg.wasCanceled():
                cancelled = True
                break

        progress_dlg.close()

        if added > 0:
            self.status_manager.save_status_db()

        # Refresh this folder's expand state in the tree
        folder_item.children.clear()
        folder_item.is_loaded = False
        tree_item.takeChildren()
        if self.status_manager.has_child_folders(folder_item.relative_path) \
                or folder_item.status != STATUS_DISMISSED:
            placeholder = QTreeWidgetItem()
            placeholder.setText(0, "Loading...")
            tree_item.addChild(placeholder)

        msg = f"Added {added} new folder(s) to the structure."
        if cancelled:
            msg += " (scan was cancelled)"
        QMessageBox.information(self, "Re-scan Complete", msg)

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
