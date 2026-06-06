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
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QIcon

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Set
from .path_mapper import PathMapper
from .folder_status_manager import (FolderStatusManager,
                                   STATUS_DISMISSED, STATUS_NEW, STATUS_WATCHED,
                                   STATUS_NOT_FOUND, STATUS_PART_WATCHED,
                                   FILE_STATUS_ON_CLOUD, FILE_STATUS_DISMISSED,
                                   FILE_STATUS_NEW, FILE_STATUS_NOT_FOUND)
from .folder_scanner import FolderScanner, FolderItem, ScanProgress


# ---------------------------------------------------------------------------
# Background worker threads
# ---------------------------------------------------------------------------

class RootLoadWorker(QThread):
    """Reconciles watched/new root folders in the background.

    Emits ``item_reconciled`` for each folder as it completes so the tree
    updates incrementally rather than waiting for the full batch.
    """
    item_reconciled = pyqtSignal(str, object)  # relative_path, recon_result (dict or None)
    finished = pyqtSignal()

    def __init__(self, status_manager, items):
        super().__init__()
        self._status_manager = status_manager
        self._items = items  # list of FolderItem (watched/new only)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        for item in self._items:
            if self._cancelled:
                break
            try:
                recon = self._status_manager.reconcile_folder_with_filesystem(
                    item.relative_path, progress_callback=None
                )
            except Exception:
                recon = None
            self.item_reconciled.emit(item.relative_path, recon)
        self.finished.emit()


class FolderExpandWorker(QThread):
    """Scans and reconciles children of a folder in the background.

    Emits ``children_ready`` with a list of populated FolderItems once done.
    """
    children_ready = pyqtSignal(str, list)  # parent_rel_path, list[FolderItem]
    error = pyqtSignal(str, str)            # parent_rel_path, error_message

    def __init__(self, folder_item, status_manager, path_mapper):
        super().__init__()
        self._folder = folder_item
        self._status_manager = status_manager
        self._path_mapper = path_mapper
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        children = []
        try:
            if self._folder.status == STATUS_DISMISSED:
                child_data_list = self._status_manager.get_immediate_child_folders(
                    self._folder.relative_path
                )
                for child_data in child_data_list:
                    if self._cancelled:
                        break
                    child_item = FolderItem(
                        relative_path=child_data['rel_path'],
                        is_directory=True,
                        name=child_data['name'],
                        parent_path=self._folder.relative_path
                    )
                    child_item.status = child_data['status']
                    child_item.is_loaded = False
                    if child_item.status != STATUS_DISMISSED:
                        try:
                            child_item.recon_result = (
                                self._status_manager.reconcile_folder_with_filesystem(
                                    child_data['rel_path'], progress_callback=None
                                )
                            )
                        except Exception:
                            child_item.recon_result = None
                    else:
                        child_item.recon_result = None
                    children.append(child_item)
            else:
                folder_path = Path(self._path_mapper.to_absolute(self._folder.relative_path))
                for child_path in sorted(folder_path.iterdir(), key=lambda p: p.name.lower()):
                    if self._cancelled:
                        break
                    if child_path.name.startswith('.') or not child_path.is_dir():
                        continue
                    child_rel = self._path_mapper.to_relative(str(child_path))
                    if not child_rel:
                        continue
                    child_item = FolderItem(
                        relative_path=child_rel,
                        is_directory=True,
                        name=child_path.name,
                        parent_path=self._folder.relative_path
                    )
                    child_item.status = self._status_manager.get_status(child_rel)
                    if child_item.status != STATUS_DISMISSED:
                        try:
                            child_item.recon_result = (
                                self._status_manager.reconcile_folder_with_filesystem(
                                    child_rel, progress_callback=None
                                )
                            )
                        except Exception:
                            child_item.recon_result = None
                    else:
                        child_item.recon_result = None
                    children.append(child_item)

            if not self._cancelled:
                self.children_ready.emit(self._folder.relative_path, children)
        except Exception as e:
            self.error.emit(self._folder.relative_path, str(e))


class _SetStatusWorker(QThread):
    """Runs set_folder_direct (+ optional reconcile) in a background thread.

    Emits ``done(success, message, recon_result)`` when finished.
    """
    done = pyqtSignal(bool, str, object)  # success, message, recon_result (dict|None)

    def __init__(self, status_manager, relative_path: str, status: str):
        super().__init__()
        self._status_manager = status_manager
        self._relative_path = relative_path
        self._status = status

    def run(self):
        success, msg = self._status_manager.set_folder_direct(
            self._relative_path, self._status
        )
        if not success:
            self.done.emit(False, msg, None)
            return

        recon_result = None
        if self._status in (STATUS_WATCHED, STATUS_PART_WATCHED, STATUS_NEW):
            try:
                recon_result = self._status_manager.reconcile_folder_with_filesystem(
                    self._relative_path, progress_callback=None
                )
            except Exception:
                recon_result = None

        self.done.emit(True, msg, recon_result)


# Status display configuration
# 'user_assignable': False means the status is auto-computed and not shown in the
#   context menu or status filter dropdown.
STATUS_CONFIG = {
    STATUS_DISMISSED: {
        'label': 'Dismissed',
        'color': QColor(180, 180, 180),  # Gray
        'description': 'Folder dismissed from workflow',
        'user_assignable': True,
    },
    STATUS_NEW: {
        'label': 'New',
        'color': QColor(255, 255, 200),  # Light yellow
        'description': 'New folder, not yet reviewed',
        'user_assignable': False,
    },
    STATUS_WATCHED: {
        'label': 'Watched',
        'color': QColor(150, 200, 255),  # Light blue
        'description': 'Folder being monitored',
        'user_assignable': True,
    },
    STATUS_NOT_FOUND: {
        'label': 'Not Found',
        'color': QColor(255, 150, 150),  # Light red
        'description': 'Missing from filesystem',
        'user_assignable': False,
    },
    STATUS_PART_WATCHED: {
        'label': 'Part Watched',
        'color': QColor(255, 210, 140),  # Amber
        'description': 'Contains a mix of watched and dismissed sub-folders',
        'user_assignable': False,
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

        # Acquire exclusive lock — raises LockError if another instance holds it
        from utilities.file_lock_manager import LockError
        lock_ok, lock_msg = self.status_manager.lock_manager.acquire_lock()
        if not lock_ok:
            raise LockError(lock_msg)

        # Refresh lock every 5 minutes to prevent it expiring while dialog is open
        self._lock_refresh_timer = QTimer(self)
        self._lock_refresh_timer.timeout.connect(self.status_manager.lock_manager.refresh_lock)
        self._lock_refresh_timer.start(5 * 60 * 1000)  # 5 minutes in ms

        # Track loaded items and their tree widget items
        self.loaded_items: Dict[str, FolderItem] = {}  # relative_path -> FolderItem
        self.tree_items: Dict[str, QTreeWidgetItem] = {}  # relative_path -> QTreeWidgetItem
        
        # Current filter settings
        self.filter_text = ""
        self.filter_status: Optional[str] = None
        
        # Selected folder path (set when double-clicking)
        self.selected_folder_path: Optional[str] = None
        
        # Track active background workers
        self._root_load_worker: Optional[RootLoadWorker] = None
        self._expand_workers: Dict[str, FolderExpandWorker] = {}

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
        # Note: STATUS_PART_WATCHED is included so users can filter by it;
        # it is stored directly in the CSV (not computed at runtime).
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

        # Reset database button (danger — styled red)
        self.reset_btn = QPushButton("Reset DB")
        self.reset_btn.setToolTip("Reset all folders to Dismissed so you can re-watch them from scratch")
        self.reset_btn.setStyleSheet("QPushButton { color: white; background-color: #c0392b; } "
                                     "QPushButton:hover { background-color: #e74c3c; }")
        self.reset_btn.clicked.connect(self._reset_database)
        layout.addWidget(self.reset_btn)

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

        The tree is populated immediately from the CSV/filesystem snapshot so
        the dialog opens without delay.  Reconciliation of watched/new folders
        (the expensive part) is then done in a background thread so the UI
        stays responsive while counts fill in.
        """
        # Cancel any in-flight workers from a previous load/refresh
        self._cancel_all_workers()

        try:
            # Ensure DB is loaded (sets is_fresh_db flag)
            self.status_manager.load_status_db()

            # First launch: seed entire folder structure (one-time, sync is acceptable)
            if self.status_manager.is_fresh_db:
                self._run_first_launch_seed()

            # Collect root items from CSV + quick filesystem check
            root_items = self._collect_root_items()

            # Build tree immediately (no counts yet for watched items)
            self.tree.clear()
            self.loaded_items.clear()
            self.tree_items.clear()
            for item in root_items:
                self._add_item_to_tree(item, None)

            # Start background reconciliation for watched/new root folders
            watched = [item for item in root_items
                       if item.status in (STATUS_WATCHED, STATUS_PART_WATCHED, STATUS_NEW)]
            if watched:
                self.refresh_btn.setEnabled(False)
                self._root_load_worker = RootLoadWorker(self.status_manager, watched)
                self._root_load_worker.item_reconciled.connect(self._on_root_item_reconciled)
                self._root_load_worker.finished.connect(self._on_root_load_finished)
                self._root_load_worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load folders: {str(e)}")

    def _on_root_item_reconciled(self, rel_path: str, recon_result):
        """Slot: update a root tree item when its reconciliation completes."""
        folder_item = self.loaded_items.get(rel_path)
        tree_item = self.tree_items.get(rel_path)
        if folder_item and tree_item:
            folder_item.recon_result = recon_result
            self._update_tree_item_status(tree_item, folder_item)

    def _on_root_load_finished(self):
        """Slot: called when all root reconciliations are done."""
        self.refresh_btn.setEnabled(True)
        self._root_load_worker = None

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
            # Add expand arrow only if the CSV cache knows this folder has
            # child folders. Dismissed folders and watched folders without
            # sub-folders both get no arrow — which also means watched leaf
            # folders paint their full row correctly without needing an expand.
            needs_arrow = self.status_manager.has_child_folders(folder_item.relative_path)
            if needs_arrow:
                placeholder = QTreeWidgetItem()
                placeholder.setText(0, "Loading...")
                tree_item.addChild(placeholder)
        
        return tree_item
    
    def _get_item_path(self, tree_item: QTreeWidgetItem) -> str:
        """Get the relative path stored in a tree item."""
        return tree_item.data(0, Qt.UserRole) or ""
    
    def _compute_row_color(self, status: str, folder_item: 'FolderItem') -> QColor:
        """Return the row background colour based on outcome rather than raw status.

        Priority:
          - Dismissed  → grey  (always, regardless of counts)
          - Not found  → red   (always)
          - recon available and new > 0           → amber  (needs work)
          - recon available and new == 0, images  → green  (all processed)
          - recon available and no images at all  → light neutral (pure container)
          - recon not yet loaded                  → STATUS_CONFIG placeholder colour
        """
        if status == STATUS_DISMISSED:
            return QColor(180, 180, 180)   # Grey
        if status == STATUS_NOT_FOUND:
            return QColor(255, 150, 150)   # Red

        if hasattr(folder_item, 'recon_result') and isinstance(folder_item.recon_result, dict):
            recon = folder_item.recon_result
            direct = recon.get('direct') or 0
            nested = recon.get('nested') or 0
            new    = recon.get('new')    or 0

            if direct == 0 and nested == 0:
                return QColor(235, 235, 235)   # Light neutral – pure container
            if new == 0:
                return QColor(140, 200, 140)   # Green – all images processed
            return QColor(255, 210, 140)       # Amber – has images needing work

        # Recon not available yet — use STATUS_CONFIG placeholder
        return STATUS_CONFIG.get(status, STATUS_CONFIG[STATUS_WATCHED])['color']

    def _update_tree_item_status(self, tree_item: QTreeWidgetItem, folder_item: FolderItem):
        """Update tree item's status display and colour.

        The status is read directly from folder_item.status, which is kept in
        sync with the CSV (part_watched is stored, not computed at display time).

        Colour rules:
          - ALL columns coloured  → watched/part-watched, direct > 0, new > 0
                                    (rows that need the user's direct attention)
          - First TWO cols only   → every other case
        """
        status = folder_item.status
        config = STATUS_CONFIG.get(status, STATUS_CONFIG[STATUS_WATCHED])

        # Set status text
        tree_item.setText(1, config['label'])

        # Determine whether this row needs direct user action
        recon = getattr(folder_item, 'recon_result', None)
        needs_action = False
        if (status in (STATUS_WATCHED, STATUS_PART_WATCHED)
                and isinstance(recon, dict)):
            direct = recon.get('direct') or 0
            new    = recon.get('new')    or 0
            needs_action = direct > 0 and new > 0

        color = self._compute_row_color(status, folder_item)
        no_color = QBrush()  # default (transparent)

        # Use the widget's column count; the item may not yet be attached to the
        # tree when this is called (e.g. during _add_item_to_tree), so
        # tree_item.columnCount() would return only the columns set so far (2),
        # not the full 7-column layout.
        col_count = self.tree.columnCount()

        if needs_action:
            # Highlight every column
            for col in range(col_count):
                tree_item.setBackground(col, QBrush(color))
        else:
            # Colour only Name + Status; clear the rest
            tree_item.setBackground(0, QBrush(color))
            tree_item.setBackground(1, QBrush(color))
            for col in range(2, col_count):
                tree_item.setBackground(col, no_color)

        # Dismissed and not_found folders carry no file counts
        if status in (STATUS_DISMISSED, STATUS_NOT_FOUND):
            for col in range(2, 7):
                tree_item.setText(col, '')
            return

        # Set counts based on reconciliation results
        if isinstance(recon, dict):
            direct   = recon.get('direct')
            nested   = recon.get('nested')
            on_cloud = recon.get('on_cloud')
            dismissed = recon.get('dismissed')
            new      = recon.get('new')

            tree_item.setText(2, '' if direct   is None else str(direct))
            tree_item.setText(3, '' if nested   is None else str(nested))
            tree_item.setText(4, '' if on_cloud is None else str(on_cloud))
            tree_item.setText(5, '' if dismissed is None else str(dismissed))
            tree_item.setText(6, '' if new       is None else str(new))
        else:
            # Not yet reconciled — blank until the folder is expanded or refreshed
            for col in range(2, 7):
                tree_item.setText(col, '')
    
    def _on_item_expanded(self, tree_item: QTreeWidgetItem):
        """Handle tree item expansion - load children in a background thread.

        The "Loading..." placeholder is kept visible until the worker finishes.
        If a worker is already running for this folder, the expand is ignored.
        """
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)

        if not folder_item or not folder_item.is_directory:
            return

        if folder_item.is_loaded:
            return

        # Already loading this folder — don't start a second worker
        if relative_path in self._expand_workers:
            return

        # Keep the "Loading..." placeholder and start a background worker
        worker = FolderExpandWorker(folder_item, self.status_manager, self.path_mapper)
        worker.children_ready.connect(self._on_children_ready)
        worker.error.connect(self._on_expand_error)
        self._expand_workers[relative_path] = worker
        worker.start()

    def _on_children_ready(self, parent_rel_path: str, children: list):
        """Slot: populate tree with children once the expand worker finishes."""
        tree_item = self.tree_items.get(parent_rel_path)
        folder_item = self.loaded_items.get(parent_rel_path)
        if not tree_item or not folder_item:
            self._expand_workers.pop(parent_rel_path, None)
            return

        tree_item.takeChildren()
        for child_item in children:
            folder_item.add_child(child_item)

        folder_item.is_loaded = True

        for child in folder_item.children:
            self._add_item_to_tree(child, tree_item)

        self._update_tree_item_status(tree_item, folder_item)
        self._expand_workers.pop(parent_rel_path, None)

    def _on_expand_error(self, parent_rel_path: str, error_msg: str):
        """Slot: handle error from expand worker."""
        tree_item = self.tree_items.get(parent_rel_path)
        if tree_item:
            tree_item.takeChildren()  # Remove "Loading..." placeholder
        self._expand_workers.pop(parent_rel_path, None)
        QMessageBox.warning(self, "Warning", f"Failed to load folder contents: {error_msg}")

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
        
        # Status change actions — only user-assignable statuses (Watched / Dismissed)
        status_menu = menu.addMenu("Set Status")
        for status_code, config in STATUS_CONFIG.items():
            if not config.get('user_assignable', False):
                continue
            action = status_menu.addAction(config['label'])
            action.triggered.connect(lambda checked, s=status_code: self._set_item_status(item, s, False))

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
    
    def _set_item_status(self, tree_item: QTreeWidgetItem, status: str, recursive: bool = False):
        """Set status for a folder. Direct assignments (watched/dismissed) propagate
        to all descendants automatically and recompute ancestor inferred statuses."""
        relative_path = self._get_item_path(tree_item)
        folder_item = self.loaded_items.get(relative_path)

        if not folder_item:
            return

        try:
            label = STATUS_CONFIG[status]['label']
            reply = QMessageBox.question(
                self,
                "Confirm Status Change",
                f"Set '{folder_item.name}' to '{label}'?\n\n"
                f"All sub-folders will be set to '{label}' as well.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

            # Run the slow work (set_folder_direct + reconcile) in a background
            # thread so the UI stays responsive.
            worker = _SetStatusWorker(self.status_manager, relative_path, status)

            # Keep a reference so the worker isn't garbage-collected.
            if not hasattr(self, '_set_status_workers'):
                self._set_status_workers = []
            self._set_status_workers.append(worker)

            # Disable the tree while the worker runs and show a busy cursor.
            self.tree.setEnabled(False)
            QApplication.setOverrideCursor(Qt.WaitCursor)

            def _on_done(success, msg, recon_result,
                         _worker=worker, _item=tree_item,
                         _folder=folder_item, _status=status,
                         _rel=relative_path):
                # Restore UI
                self.tree.setEnabled(True)
                QApplication.restoreOverrideCursor()
                if _worker in self._set_status_workers:
                    self._set_status_workers.remove(_worker)

                if not success:
                    QMessageBox.critical(self, "Error", msg)
                    return

                # Update the in-memory folder item and tree
                _folder.status = _status
                self._reload_folder_item(_folder, _item)

                if recon_result is not None:
                    _folder.recon_result = recon_result
                    self._update_tree_item_status(_item, _folder)

                # If already expanded, reload children so placeholder doesn't stick.
                if _item.isExpanded():
                    self._on_item_expanded(_item)

                self._refresh_ancestor_tree_items(_item)
                self.statuses_updated.emit()

            worker.done.connect(_on_done)
            worker.start()

        except Exception as e:
            QApplication.restoreOverrideCursor()
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
            # Recompute inferred statuses: new dismissed sub-folders may change
            # this folder's status (e.g. watched → part_watched) and its ancestors
            self.status_manager.recompute_all_inferred_statuses()
            folder_item.status = self.status_manager.get_status(relative_path)

        # Refresh this folder's expand state in the tree
        folder_item.children.clear()
        folder_item.is_loaded = False
        tree_item.takeChildren()
        if self.status_manager.has_child_folders(folder_item.relative_path):
            placeholder = QTreeWidgetItem()
            placeholder.setText(0, "Loading...")
            tree_item.addChild(placeholder)
        self._update_tree_item_status(tree_item, folder_item)
        self._refresh_ancestor_tree_items(tree_item)

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

            # Re-reconcile so counts reflect the newly scanned files
            folder_item.recon_result = self.status_manager.reconcile_folder_with_filesystem(
                relative_path
            )

            # Update counts on this item and bubble up to all ancestors
            self._update_tree_item_status(tree_item, folder_item)
            self._refresh_ancestor_tree_items(tree_item)
            
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

    def _refresh_ancestor_tree_items(self, tree_item: QTreeWidgetItem):
        """Walk up the tree and refresh each ancestor's status display.

        Called after a status change so that ancestor folders whose inferred
        status has been updated in the CSV are re-coloured in the tree.

        Intentionally skips reconcile_folder_with_filesystem so this always
        runs fast on the main thread.  Ancestor file counts (recon_result) are
        left at their current (possibly stale) values — they will be refreshed
        the next time the user expands or re-opens the ancestor folder.
        """
        parent_item = tree_item.parent()
        while parent_item is not None:
            parent_path = self._get_item_path(parent_item)
            parent_folder = self.loaded_items.get(parent_path)
            if parent_folder:
                parent_folder.status = self.status_manager.get_status(parent_path)
                # Refresh counts from cache so colour reflects current reality
                # (e.g. parent turns green when last watched sub-folder completes)
                parent_folder.recon_result = self.status_manager.count_from_cache(parent_path)
                self._update_tree_item_status(parent_item, parent_folder)
            parent_item = parent_item.parent()

    def refresh_folder_counts(self, folder_rel_paths):
        """Re-reconcile and refresh the count columns for the given folder paths.

        Called from the main window after images are dismissed or uploaded so
        that the On Cloud / Dismissed / New counters update without the user
        needing to manually reopen the dialog.

        Args:
            folder_rel_paths: Iterable of relative folder paths to refresh.
        """
        refreshed_tree_items = []
        for rel_path in folder_rel_paths:
            tree_item = self.tree_items.get(rel_path)
            folder_item = self.loaded_items.get(rel_path)
            if tree_item is None or folder_item is None:
                continue
            # Read counts straight from the cache — do NOT call reconcile here,
            # which would trigger a destructive Scenario-4 rescan for 'new' folders
            # and wipe the file statuses we just wrote.
            folder_item.recon_result = self.status_manager.count_from_cache(rel_path)
            self._update_tree_item_status(tree_item, folder_item)
            refreshed_tree_items.append(tree_item)

        # Propagate refreshed counts up to ancestors
        for tree_item in refreshed_tree_items:
            self._refresh_ancestor_tree_items(tree_item)

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

    def _reset_database(self):
        """Reset all folders to Dismissed so the user can re-watch from scratch."""
        reply = QMessageBox.warning(
            self,
            "Reset Database",
            "This will set EVERY folder to Dismissed and remove all file entries.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        if reply != QMessageBox.Yes:
            return

        # Wait for any in-flight set-status workers before resetting to avoid a
        # race condition where a background thread writes 'watched' after the reset.
        if hasattr(self, '_set_status_workers'):
            for worker in list(self._set_status_workers):
                worker.wait(5000)
            self._set_status_workers.clear()

        success, msg = self.status_manager.reset_all_folders_to_dismissed()
        if success:
            self._load_root_folders()
            self.statuses_updated.emit()
        else:
            QMessageBox.critical(self, "Reset Failed", msg)
    
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

    # ------------------------------------------------------------------
    # Worker lifecycle helpers
    # ------------------------------------------------------------------

    def _cancel_all_workers(self):
        """Cancel and wait for all active background workers."""
        if self._root_load_worker is not None:
            self._root_load_worker.cancel()
            self._root_load_worker.wait(1000)
            self._root_load_worker = None
        for worker in list(self._expand_workers.values()):
            worker.cancel()
            worker.wait(1000)
        self._expand_workers.clear()
        if hasattr(self, '_set_status_workers'):
            for worker in list(self._set_status_workers):
                worker.wait(3000)
            self._set_status_workers.clear()

    def closeEvent(self, event):
        """Ensure background workers are stopped and lock released before the dialog closes."""
        self._lock_refresh_timer.stop()
        self._cancel_all_workers()
        self.status_manager.lock_manager.release_lock()
        super().closeEvent(event)
