import sys
import os
import re
import gc
import subprocess
import plistlib
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

from PyQt5.QtWidgets import (QMainWindow, QApplication, QFileDialog, 
                           QWidget, QLabel, QTextEdit, QMessageBox,
                           QVBoxLayout, QGridLayout, QSizePolicy, QProgressBar, QRubberBand, QDialog)
from PyQt5.QtCore import Qt, QTimer, QSize, QRect, QPoint, QEvent
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import uic
from utilities.tag_manager import TagManager
from utilities.settings_dialog import SettingsDialog
from utilities.cloudinary_update_v13 import CloudinaryUpdater
from ui.cloudinaryCreditsBar import CloudinaryCreditsBar
from utilities.image_assessment import ImageAssessment
from utilities.image_flow_manager import ImageFlowManager
from utilities.cloudinary_upload_handler import CloudinaryUploadHandler
from utilities.debug_utils import (
    debug_startup, debug_layout, debug_image_display, debug_tags, 
    debug_metadata, debug_cloudinary, debug_memory, debug_errors,
    debug_file_ops, debug_assessment, debug_ui_events, configure_debug, print_debug_status, debug, debug_upload
)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

try:
    import exiftool
    import platform
    import struct
    import subprocess
    
    # Initialize global variables
    EXIFTOOL_AVAILABLE = False
    EXIFTOOL_PATH = None
    
    def cleanup_stale_exiftool_processes():
        """Clean up any stale ExifTool processes before starting new ones"""
        try:
            debug_startup("Cleaning up any stale ExifTool processes...")
            if platform.system().lower() == 'windows':
                # Kill any existing exiftool processes on Windows
                subprocess.run(['taskkill', '/f', '/im', 'exiftool.exe'], 
                             capture_output=True, text=True)
                subprocess.run(['taskkill', '/f', '/im', 'exiftool(-k).exe'], 
                             capture_output=True, text=True)
            else:
                # Kill any existing exiftool processes on Unix-like systems
                subprocess.run(['pkill', '-f', 'exiftool'], 
                             capture_output=True, text=True)
            debug_startup("Stale process cleanup completed")
        except Exception as e:
            debug_startup(f"Process cleanup warning (non-critical): {e}")
    
    # Clean up any stale processes first
    cleanup_stale_exiftool_processes()
    
    def detect_exiftool_path():
        """Detect the appropriate ExifTool executable based on the current system"""
        system = platform.system().lower()
        architecture = platform.machine().lower()
        is_64bit = struct.calcsize("P") * 8 == 64
        
        # Check if running from PyInstaller bundle
        is_bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        
        if is_bundled:
            debug_startup(f"Running from PyInstaller bundle, base path: {sys._MEIPASS}")
            base_path = sys._MEIPASS
        else:
            debug_startup("Running in development mode")
            base_path = os.path.abspath(".")
        
        if system == 'windows':
            # Windows: choose between 32-bit and 64-bit versions
            if is_bundled:
                # In PyInstaller bundle, ExifTool is in packages directory
                if is_64bit:
                    exiftool_path = os.path.join(base_path, 'packages', 'exiftool_win64', 'exiftool-13.34_64', 'exiftool(-k).exe')
                else:
                    exiftool_path = os.path.join(base_path, 'packages', 'exiftool_win32', 'exiftool-13.34_32', 'exiftool(-k).exe')
            else:
                # In development mode, use local packages directory
                if is_64bit:
                    exiftool_path = os.path.join(base_path, 'packages', 'exiftool_win64', 'exiftool-13.34_64', 'exiftool(-k).exe')
                else:
                    exiftool_path = os.path.join(base_path, 'packages', 'exiftool_win32', 'exiftool-13.34_32', 'exiftool(-k).exe')
            print(f"Detected Windows, looking for: {exiftool_path}")
        
        elif system == 'darwin':  # macOS
            # For Mac, we'll use the Perl version from Image-ExifTool
            if is_bundled:
                # In PyInstaller bundle, ExifTool is bundled at the root level
                exiftool_path = os.path.join(base_path, 'packages', 'Image-ExifTool-13.34', 'exiftool')
            else:
                # In development mode, use local packages directory
                exiftool_path = os.path.join(base_path, 'packages', 'Image-ExifTool-13.34', 'exiftool')
            print(f"Detected macOS, looking for: {exiftool_path}")
        
        elif system == 'linux':
            # For Linux, try the Perl version or system installation
            if is_bundled:
                exiftool_path = os.path.join(base_path, 'packages', 'Image-ExifTool-13.34', 'exiftool')
            else:
                exiftool_path = os.path.join(base_path, 'packages', 'Image-ExifTool-13.34', 'exiftool')
            print(f"Detected Linux, looking for: {exiftool_path}")
        
        else:
            print(f"Unsupported system: {system}")
            return None
        
        if os.path.exists(exiftool_path):
            debug_startup(f"ExifTool found at: {exiftool_path}")
            return exiftool_path
        else:
            debug_startup(f"ExifTool executable not found at: {exiftool_path}")
            return None
    
    # Try to find local ExifTool installation
    local_exiftool_path = detect_exiftool_path()
    
    debug_startup(f"Local ExifTool path detected: {local_exiftool_path}")
    
    if local_exiftool_path:
        # Test if local ExifTool works
        try:
            debug_startup(f"Testing local ExifTool at: {local_exiftool_path}")
            with exiftool.ExifTool(executable=local_exiftool_path) as et:
                # Simple test - try to get version
                test_result = et.execute("-ver")
                debug_startup(f"ExifTool version test result: {test_result}")
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = local_exiftool_path
            print(f"Successfully using local ExifTool from: {local_exiftool_path}")
        except Exception as e:
            print(f"Local ExifTool test failed: {e}")
            EXIFTOOL_AVAILABLE = False
            EXIFTOOL_PATH = None
    else:
        debug_startup("No local ExifTool path found")
        EXIFTOOL_AVAILABLE = False
        EXIFTOOL_PATH = None
    
    # Fallback to system ExifTool if local one doesn't work
    if not EXIFTOOL_AVAILABLE:
        debug_startup("Trying system ExifTool as fallback")
        try:
            with exiftool.ExifTool() as et:
                test_result = et.execute("-ver")
                debug_startup(f"System ExifTool version test result: {test_result}")
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = None
            print("Using system ExifTool")
        except Exception:
            EXIFTOOL_AVAILABLE = False
            EXIFTOOL_PATH = None
            print("Warning: ExifTool executable not found - using fallback metadata reading")

    debug_startup(f"Final ExifTool status: EXIFTOOL_AVAILABLE={EXIFTOOL_AVAILABLE}, EXIFTOOL_PATH={EXIFTOOL_PATH}")

except ImportError:
    EXIFTOOL_AVAILABLE = False
    EXIFTOOL_PATH = None
    print("Warning: PyExifTool not available - using fallback metadata reading")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize debug system
        debug_startup("Initializing HappyTag application")
        print_debug_status()
        
        # Check if UI file exists before loading
        ui_path = resource_path('ui/mainWindow.ui')
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")
            
        # Load the UI
        uic.loadUi(ui_path, self)
        debug_startup("UI loaded successfully")
        
        # === CORE UI SETUP (Essential for showing window) ===
        self._setup_core_ui()
        
        # === INITIALIZE BASIC STATE ===
        self._initialize_basic_state()
        
        # === SHOW WINDOW EARLY ===
        debug_startup("Core UI setup complete - showing window")
        
        # === DEFERRED INITIALIZATION (Heavy components loaded in background) ===
        # Use QTimer to initialize heavy components after window is shown
        self.initialization_timer = QTimer(self)
        self.initialization_timer.setSingleShot(True)
        self.initialization_timer.timeout.connect(self._initialize_heavy_components)
        self.initialization_timer.start(100)  # Start heavy initialization after 100ms
        
        debug_startup("Basic initialization complete - window ready to show")

    def _setup_core_ui(self):
        """Setup essential UI components needed for window display"""
        debug_startup("Setting up core UI components...")
        
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
        
        # Remove any existing layout from picturesContainer
        if self.picturesContainer.layout():
            old_layout = self.picturesContainer.layout()
            # Clear all items from the old layout
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item and item.widget():
                    item.widget().setParent(None)
            # Delete the old layout
            old_layout.setParent(None)
        
        # Connect essential signals
        self.actionOpenFiles.triggered.connect(self.open_files)
        self.actionOpen_Folder.triggered.connect(self.open_folder)
        self.horizontalSlider.valueChanged.connect(self.update_layout)
        
        # Connect Save action for metadata
        if hasattr(self, 'actionSave'):
            self.actionSave.triggered.connect(self.save_all_keywords)
        
        # Connect Settings action
        if hasattr(self, 'actionSettings'):
            self.actionSettings.triggered.connect(self.show_settings)
        
        # Connect Cloudinary Sync action (will be enabled after initialization)
        if hasattr(self, 'actionSynch_with_Cloudinary'):
            self.actionSynch_with_Cloudinary.triggered.connect(self.start_cloudinary_upload)
            self.actionSynch_with_Cloudinary.setEnabled(False)  # Disable until Cloudinary is ready
        
        # Hide Cloudinary UI area initially (shows placeholder text and confusing values)
        self._hide_cloudinary_ui_area()
        
        # Setup sort button menu (button is now defined in UI file)
        self.setup_sort_menu()
        
        debug_startup("Core UI components setup complete")

    def _initialize_basic_state(self):
        """Initialize basic application state"""
        debug_startup("Initializing basic application state...")
        
        # Create the Tags Window action if it doesn't exist
        if not hasattr(self, 'actionTags_Window'):
            from PyQt5.QtWidgets import QAction
            self.actionTags_Window = QAction("Show Tags Window", self)
            self.menuWindow.addAction(self.actionTags_Window)
        
        # Initialize tag manager as None (will be created when needed)
        self.tag_manager = None
        
        # Connect Tags Window action
        self.actionTags_Window.triggered.connect(self.show_tag_manager)
        
        # Connect the Tags Window menu action
        if hasattr(self, 'menuTags_Window'):
            self.menuTags_Window.triggered.connect(self.show_tag_manager)
        
        # Connect button actions
        self.clearTagsButton.clicked.connect(self.clear_selected_tags)
        self.SelectAlButton.clicked.connect(self.select_all_images)
        
        # Initially disable clear tags button (no images selected)
        self.clearTagsButton.setEnabled(False)
        
        # Store loaded images
        self.image_files = []
        self.image_previews = {}
        self.image_metadata = {}  # Store metadata (year, keywords) for each image
        self.original_keywords = {}  # Track original keywords for change detection
        
        # Initialize the new ImageFlowManager for responsive layout
        # Use external scroll mode since we're placing it in the main window's scroll area
        self.image_flow_manager = ImageFlowManager(use_internal_scroll=False)
        
        # Connect ImageFlowManager signals
        self.image_flow_manager.selection_changed.connect(self.on_grid_selection_changed)
        self.image_flow_manager.image_double_clicked.connect(self.on_image_double_clicked)
        self.image_flow_manager.tags_changed.connect(self.on_image_tags_changed)
        self.image_flow_manager.context_menu_requested.connect(self.on_image_context_menu)
        
        # Set the flow manager as the widget for our existing scroll area
        self.scrollArea.setWidget(self.image_flow_manager)
        
        # Backward compatibility - keep reference to image_widgets for existing code
        self.image_widgets = []  # Will be updated by flow manager
        
        # Initialize widget width slider with 5 discrete size steps
        # Maps slider positions (1-5) to specific pixel widths for modular sizing
        self.size_steps = {1: 280, 2: 360, 3: 460, 4: 560, 5: 700, 6:1000}  # 5 distinct size options
        self.horizontalSlider.setMinimum(1)     # Step 1 (smallest)
        self.horizontalSlider.setMaximum(6)     # Step 5 (largest) 
        self.horizontalSlider.setValue(1)       # Step 3 (medium, 200px default)
        self.horizontalSlider.setTickPosition(self.horizontalSlider.TicksBelow)
        self.horizontalSlider.setTickInterval(1)  # Show tick marks for each step
        
        self.MAX_PREVIEW_SIZE = 800  # Optimized preview size for better memory usage and performance
        self.selected_images = set()
        
        # Create progress bar overlay (initially hidden)
        self.progress_overlay = None
        self.progress_bar = None
        
        # Initialize component flags
        self.cloudinary_connected = False
        self.cloudinary_cache_populated = False  # Track if we've attempted to populate cache
        self.credits_bar_initialized = False
        self.exiftool_available = False
        self.components_initialized = False
        
        # Initialize placeholders for heavy components (will be created later)
        self.cloudinary_updater = None
        self.image_assessment = None
        self.upload_handler = None
        self.persistent_exiftool = None
        
        # Track metadata errors for reporting
        self.metadata_errors = []
        self.unsupported_files = []
        self.problematic_files = set()
        self.enable_metadata_reading = True
        
        debug_startup("Basic application state initialized")

    def _hide_cloudinary_ui_area(self):
        """Hide Cloudinary UI elements to prevent showing placeholder text during initialization"""
        try:
            # Hide secondary widgets but keep the main label visible for status
            secondary_widgets = [
                getattr(self, 'storageLabel', None),
                getattr(self, 'transformationsLabel', None), 
                getattr(self, 'bandwidthLabel', None),
                getattr(self, 'creditsBar', None)
            ]
            
            for widget in secondary_widgets:
                if widget:
                    widget.setVisible(False)
            
            # Show main label with "Connecting..." status
            if hasattr(self, 'label') and self.label:
                self.label.setVisible(True)
                self.label.setText("Connecting to Cloudinary...")
            
            debug_startup("Cloudinary secondary widgets hidden, main label shows 'Connecting...'")
        except Exception as e:
            debug_errors(f"Error hiding Cloudinary UI area: {e}")

    def _show_cloudinary_ui_area(self):
        """Show Cloudinary UI elements after successful initialization"""
        try:
            # Show individual widgets in the Cloudinary UI area
            cloudinary_widgets = [
                ('storageLabel', getattr(self, 'storageLabel', None)),
                ('transformationsLabel', getattr(self, 'transformationsLabel', None)), 
                ('bandwidthLabel', getattr(self, 'bandwidthLabel', None)),
                ('creditsBar', getattr(self, 'creditsBar', None)),
                ('label', getattr(self, 'label', None))  # "Current Credits Usage" label
            ]
            
            shown_widgets = []
            for widget_name, widget in cloudinary_widgets:
                if widget:
                    widget.setVisible(True)
                    shown_widgets.append(widget_name)
                    debug_startup(f"Made {widget_name} visible")
                else:
                    debug_startup(f"Widget {widget_name} not found")
            
            debug_startup(f"Shown Cloudinary widgets: {shown_widgets}")
            
            # Set proper text for the labels after making them visible
            self._update_cloudinary_label_text()
            
            # Force layout update to recalculate size after widgets become visible
            # Use a timer to ensure the visibility changes are processed first
            QTimer.singleShot(50, self._refresh_ui_layout)
            
            debug_startup("Cloudinary UI widgets shown after initialization")
        except Exception as e:
            debug_errors(f"Error showing Cloudinary UI area: {e}")

    def _update_cloudinary_label_text(self):
        """Update Cloudinary labels with proper text instead of 'TextLabel'"""
        try:
            if hasattr(self, 'storageLabel') and self.storageLabel:
                self.storageLabel.setText("Storage: 0.0%")
                debug_startup("Updated storageLabel text")
            
            if hasattr(self, 'transformationsLabel') and self.transformationsLabel:
                self.transformationsLabel.setText("Transformations: 4.9%")
                debug_startup("Updated transformationsLabel text")
                
            if hasattr(self, 'bandwidthLabel') and self.bandwidthLabel:
                self.bandwidthLabel.setText("Bandwidth: 0.0%")
                debug_startup("Updated bandwidthLabel text")
        except Exception as e:
            debug_errors(f"Error updating Cloudinary label text: {e}")

    def _refresh_ui_layout(self):
        """Force refresh of UI layout to accommodate newly visible widgets"""
        try:
            debug_startup("Starting UI layout refresh...")
            
            # Force the parent container to recalculate its layout
            if hasattr(self, 'centralwidget'):
                self.centralwidget.adjustSize()
                self.centralwidget.updateGeometry()
                self.centralwidget.update()
                debug_startup("Updated centralwidget")
            
            # Update the main window
            self.adjustSize()
            self.updateGeometry()
            self.update()
            debug_startup("Updated main window")
            
            # Force immediate layout processing on the grid layout
            if hasattr(self, 'gridLayout'):
                self.gridLayout.invalidate()
                self.gridLayout.activate()
                debug_startup("Refreshed gridLayout")
                
            # Force a repaint to ensure visual updates
            self.repaint()
            
            debug_startup("UI layout refreshed after Cloudinary widgets shown")
        except Exception as e:
            debug_errors(f"Error refreshing UI layout: {e}")

    def _force_layout_refresh_after_visibility_change(self):
        """Force layout refresh specifically after widget visibility changes"""
        try:
            print("[LAYOUT FIX] Starting forced layout refresh...")
            
            # Store current window size before refresh to prevent shrinking
            original_size = self.size()
            print(f"[LAYOUT FIX] Storing original window size: {original_size.width()}x{original_size.height()}")
            
            # Update the central widget's layout
            if hasattr(self, 'centralwidget'):
                self.centralwidget.adjustSize()
                self.centralwidget.updateGeometry()
                print("[LAYOUT FIX] Updated central widget geometry")
            
            # Force the grid layout to recalculate without changing main window size
            if hasattr(self, 'gridLayout'):
                self.gridLayout.invalidate()
                self.gridLayout.activate()
                print("[LAYOUT FIX] Invalidated and activated grid layout")
            
            # Update main window geometry but preserve size
            self.updateGeometry()
            print("[LAYOUT FIX] Updated main window geometry")
            
            # Restore the original window size to prevent shrinking
            self.resize(original_size)
            print(f"[LAYOUT FIX] Restored window size to: {original_size.width()}x{original_size.height()}")
            
            # Force immediate repaint
            self.repaint()
            print("[LAYOUT FIX] Layout refresh completed")
            
        except Exception as e:
            print(f"[LAYOUT FIX] Error in forced layout refresh: {e}")
            debug_errors(f"Error in forced layout refresh: {e}")

    def _update_cloudinary_ui_status(self, connected, status_message=""):
        """Update Cloudinary UI status and visibility"""
        try:
            debug_startup(f"_update_cloudinary_ui_status called: connected={connected}, message='{status_message}'")
            
            # Always show the main label (for status feedback)
            if hasattr(self, 'label') and self.label:
                self.label.setVisible(True)
            
            if connected:
                debug_startup("Connection successful - showing all Cloudinary UI elements")
                
                # Show all Cloudinary widgets for successful connection
                cloudinary_widgets = [
                    ('storageLabel', getattr(self, 'storageLabel', None)),
                    ('transformationsLabel', getattr(self, 'transformationsLabel', None)), 
                    ('bandwidthLabel', getattr(self, 'bandwidthLabel', None)),
                    ('creditsBar', getattr(self, 'creditsBar', None))
                ]
                
                for widget_name, widget in cloudinary_widgets:
                    if widget:
                        widget.setVisible(True)
                        print(f"[LAYOUT FIX] Made {widget_name} visible")
                
                # Set main label text for successful connection
                if hasattr(self, 'label') and self.label:
                    self.label.setText("Current Credits Usage")
                
                # NOTE: Do NOT update the other labels here - that's handled by update_credits_bar()
                # when real data arrives. This prevents showing placeholder text.
                
                # Enable Cloudinary sync action if available
                if hasattr(self, 'actionSynch_with_Cloudinary'):
                    self.actionSynch_with_Cloudinary.setEnabled(True)
                    debug_startup("Enabled Cloudinary sync action")
                    
            else:
                debug_startup(f"Connection failed - showing only main label with error message: {status_message}")
                
                # Hide secondary widgets (bar and percentage labels) when not connected
                secondary_widgets = [
                    ('storageLabel', getattr(self, 'storageLabel', None)),
                    ('transformationsLabel', getattr(self, 'transformationsLabel', None)), 
                    ('bandwidthLabel', getattr(self, 'bandwidthLabel', None)),
                    ('creditsBar', getattr(self, 'creditsBar', None))
                ]
                
                for widget_name, widget in secondary_widgets:
                    if widget:
                        widget.setVisible(False)
                        print(f"[LAYOUT FIX] Hid {widget_name}")
                
                # Set main label text based on the type of failure
                if hasattr(self, 'label') and self.label:
                    if "not configured" in status_message.lower():
                        self.label.setText("Cloudinary not configured")
                    else:
                        self.label.setText("Not connected to Cloudinary")
                
                # Disable Cloudinary sync action        
                if hasattr(self, 'actionSynch_with_Cloudinary'):
                    self.actionSynch_with_Cloudinary.setEnabled(False)
                
                debug_startup(f"Cloudinary UI updated with error status: {status_message}")
                
            # Only force layout refresh if we're showing widgets (to prevent window shrinking on hide)
            if connected:
                self._force_layout_refresh_after_visibility_change()
            else:
                # For disconnected state, just update geometry without full refresh
                if hasattr(self, 'centralwidget'):
                    self.centralwidget.updateGeometry()
                self.updateGeometry()
            
        except Exception as e:
            debug_errors(f"Error updating Cloudinary UI status: {e}")

    def _initialize_heavy_components(self):
        """Initialize heavy components in background after window is shown"""
        debug_startup("Starting heavy component initialization in background...")
        
        # Show status in the status bar
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage("Initializing components...")
        
        # Initialize components in order of importance
        try:
            # 1. Initialize Cloudinary (async)
            debug_startup("Initializing Cloudinary integration...")
            self._initialize_cloudinary_async()
            
            # 2. Initialize ExifTool (lazy - only when needed)
            debug_startup("Preparing ExifTool for lazy initialization...")
            self._prepare_exiftool_lazy()
            
            # 3. Initialize Assessment System
            debug_startup("Initializing Image Assessment System...")
            self._initialize_assessment_system()
            
            # 4. Initialize Upload Handler
            debug_startup("Initializing Upload Handler...")
            self._initialize_upload_handler()
            
            # Mark components as initialized
            self.components_initialized = True
            
            # Update UI status
            self._update_cloudinary_ui_status(self.cloudinary_connected, "Ready" if self.cloudinary_connected else "Not connected")
            
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage("Ready", 2000)  # Show for 2 seconds
            
            debug_startup("Heavy component initialization complete")
            
        except Exception as e:
            debug_errors(f"Error during heavy component initialization: {e}")
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage("Initialization error - some features may be limited", 5000)

    def _initialize_cloudinary_async(self):
        """Initialize Cloudinary integration asynchronously"""
        # Initialize as disconnected
        self.cloudinary_connected = False
        self.cloudinary_updater = None
        self.cloudinary_files_cache = []  # Global cache for Cloudinary files
        
        try:
            # Get Cloudinary settings from our unified settings system
            settings = SettingsDialog.get_saved_settings()
            cloudinary_settings = SettingsDialog.get_cloudinary_settings()
            
            debug_cloudinary(f"Retrieved settings: {cloudinary_settings}")
            
            # Check if Cloudinary is configured
            if not SettingsDialog.is_cloudinary_configured():
                debug_cloudinary("Cloudinary not configured - skipping CloudinaryUpdater setup")
                debug_cloudinary("Configure Cloudinary settings in File > Settings to enable cloud features")
                self._update_cloudinary_ui_status(False, "Not configured")
                return
            
            # Create CloudinaryUpdater instance
            self.cloudinary_updater = CloudinaryUpdater()
            debug_cloudinary("CloudinaryUpdater instance created successfully")
            
            debug_cloudinary("Cloudinary settings found - configuring CloudinaryUpdater...")
            
            # Prepare config in the format expected by CloudinaryUpdater
            cloudinary_config = [
                cloudinary_settings.get('log_folder', ''),
                cloudinary_settings.get('cloud_name', ''),
                cloudinary_settings.get('api_key', ''),
                cloudinary_settings.get('api_secret', ''),
                cloudinary_settings.get('max_size', '10')  # Default 10MB
            ]
            
            debug_cloudinary(f"Cloudinary config prepared: {[cloudinary_config[0], cloudinary_config[1], '*****', '*****', cloudinary_config[4]]}")
            
            # Configure the CloudinaryUpdater
            self.cloudinary_updater.setCloudinaryUpdaterConfig(cloudinary_config)
            debug_cloudinary("CloudinaryUpdater configured successfully")
            
            # Test initial connection asynchronously
            debug_cloudinary("Testing Cloudinary connection asynchronously...")
            try:
                # Connect signals to capture the response
                self.cloudinary_updater.beginning_signal.connect(self.on_cloudinary_status_received)
                self.cloudinary_updater.update_ui_signal.connect(self.on_cloudinary_ui_update)
                
                # Request account status (async)
                self.cloudinary_updater.cloud_status()
                debug_cloudinary("Cloudinary status request sent asynchronously")
                
            except Exception as conn_error:
                debug_errors(f"Cloudinary connection test failed: {conn_error}")
                self._update_cloudinary_ui_status(False, "Connection failed")
                
        except Exception as e:
            debug_errors(f"Failed to initialize Cloudinary integration: {e}")
            self._update_cloudinary_ui_status(False, "Initialization failed")

    def _prepare_exiftool_lazy(self):
        """Prepare ExifTool for lazy initialization (only when first needed)"""
        # Just set the flag - actual initialization happens in get_exiftool()
        self.exiftool_prepared = True
        debug_startup("ExifTool prepared for lazy initialization")

    def _initialize_assessment_system(self):
        """Initialize Image Assessment System"""
        if not hasattr(self, 'image_assessment') or self.image_assessment is None:
            self.image_assessment = ImageAssessment(cloudinary_updater=self.cloudinary_updater, main_app=self)
            self.setup_image_assessment_connections()
            debug_startup("Image Assessment System initialized")

    def _initialize_upload_handler(self):
        """Initialize Cloudinary Upload Handler"""
        if not hasattr(self, 'upload_handler') or self.upload_handler is None:
            self.upload_handler = CloudinaryUploadHandler(
                cloudinary_updater=self.cloudinary_updater,
                image_assessment=self.image_assessment
            )
            self.setup_upload_handler_connections()
            debug_startup("Upload Handler initialized")

    def get_exiftool(self):
        """Get ExifTool instance, initializing lazily if needed"""
        if not self.exiftool_available and hasattr(self, 'exiftool_prepared'):
            debug_startup("Lazy initializing ExifTool on first use...")
            self.init_persistent_exiftool()
        return self.persistent_exiftool if self.exiftool_available else None

    def ensure_components_ready(self):
        """Ensure all components are initialized before use"""
        if not hasattr(self, 'components_initialized') or not self.components_initialized:
            debug_startup("Components not ready - initializing synchronously...")
            self._initialize_heavy_components()

    def get_widget_text_field(self, widget):
        """
        Helper function to get the text field from any widget type.
        Handles both ImageCardWidget (text_edit) and legacy widgets (input_field).
        """
        if hasattr(widget, 'text_edit'):
            return widget.text_edit  # ImageCardWidget
        elif hasattr(widget, 'input_field'):
            return widget.input_field  # Legacy widget
        return None

    def get_widget_text(self, widget):
        """
        Helper function to get text content from any widget type.
        """
        text_field = self.get_widget_text_field(widget)
        if text_field:
            return text_field.toPlainText().strip()
        return ""

    def set_widget_text(self, widget, text):
        """
        Helper function to set text content for any widget type.
        Uses appropriate method for each widget type.
        """
        if hasattr(widget, 'set_tags'):
            # ImageCardWidget - use the proper method
            widget.set_tags(text)
        else:
            # Legacy widget - set text directly
            text_field = self.get_widget_text_field(widget)
            if text_field:
                text_field.setText(text)

    def init_persistent_exiftool(self):
        """Initialize a persistent ExifTool instance for better performance"""
        global EXIFTOOL_AVAILABLE, EXIFTOOL_PATH
        
        # First, ensure any existing instance is cleaned up
        self.cleanup_persistent_exiftool()
        
        try:
            # Check if exiftool module is available
            import exiftool as et_module
            
            if EXIFTOOL_AVAILABLE:
                debug_startup("Initializing persistent ExifTool...")
                
                try:
                    if EXIFTOOL_PATH:
                        debug_startup(f"Using local ExifTool: {EXIFTOOL_PATH}")
                        self.persistent_exiftool = et_module.ExifTool(executable=EXIFTOOL_PATH)
                    else:
                        debug_startup("Using system ExifTool")
                        self.persistent_exiftool = et_module.ExifTool()
                    
                    # Start the persistent process using __enter__
                    debug_startup("Starting ExifTool process...")
                    self.persistent_exiftool.__enter__()
                    
                    # Test the connection with a simple command
                    test_result = self.persistent_exiftool.execute("-ver")
                    debug_startup(f"ExifTool connection test: {test_result.strip()}")
                    
                    self.exiftool_available = True
                    debug_startup("Persistent ExifTool started successfully")
                    
                except Exception as start_error:
                    debug_errors(f"Failed to start ExifTool process: {start_error}")
                    self.exiftool_available = False
                    self.persistent_exiftool = None
                    
            else:
                debug_startup("ExifTool not available globally, skipping persistent instance")
                self.exiftool_available = False
                
        except ImportError:
            debug_startup("ExifTool module not available for persistent instance")
            self.exiftool_available = False
        except Exception as e:
            debug_errors(f"Failed to initialize persistent ExifTool: {e}")
            self.exiftool_available = False
            self.persistent_exiftool = None

    def cleanup_persistent_exiftool(self):
        """Clean up the persistent ExifTool instance"""
        if hasattr(self, 'persistent_exiftool') and self.persistent_exiftool:
            try:
                debug_startup("Terminating persistent ExifTool...")
                self.persistent_exiftool.__exit__(None, None, None)
                debug_startup("Persistent ExifTool terminated successfully")
            except Exception as e:
                debug_errors(f"Error terminating persistent ExifTool: {e}")
            finally:
                self.persistent_exiftool = None
                self.exiftool_available = False

    def closeEvent(self, event):
        """Handle application close event to clean up resources"""
        self.cleanup_persistent_exiftool()
        super().closeEvent(event)

    # ImageFlowManager Signal Handlers
    def on_grid_selection_changed(self, selected_files):
        """Handle selection changes from the ImageFlowManager"""
        debug_ui_events(f"Flow selection changed: {len(selected_files)} files selected")
        self.selected_images = set(selected_files)
        self.update_status_bar()
        
    def on_image_double_clicked(self, file_path):
        """Handle image double-click from the ImageFlowManager"""
        debug("ui_events", f"Image double-clicked: {file_path}")
        # Add your double-click logic here (e.g., open image in external viewer)
        
    def on_image_tags_changed(self, file_path, new_tags):
        """Handle tag changes from the ImageFlowManager"""
        debug("tags", f"Tags changed for {file_path}: {new_tags}")
        # Update the metadata storage
        if file_path in self.image_metadata:
            self.image_metadata[file_path]['keywords'] = new_tags
        
    def on_image_context_menu(self, file_path, position):
        """Handle context menu requests from the ImageFlowManager"""
        debug("ui_events", f"Context menu requested for {file_path} at {position}")
        # Add your context menu logic here

    def get_image_metadata(self, file_path):
        """Extract year and keywords from image metadata using persistent ExifTool (unified approach)"""
        # Check cache first to avoid duplicate work
        if hasattr(self, 'image_metadata') and file_path in self.image_metadata:
            cached_data = self.image_metadata[file_path]
            debug_metadata(f"Using cached metadata for {os.path.basename(file_path)}")
            return cached_data['year'], cached_data['keywords']
        
        year = None
        keywords = []
        filename = os.path.basename(file_path)
        
        # Skip files that previously caused issues
        if file_path in self.problematic_files:
            debug_metadata(f"Skipping problematic file: {filename}")
            return year, keywords
        
        try:
            # Try to get ExifTool instance (triggers lazy initialization if needed)
            et = self.get_exiftool()
            
            debug_metadata(f"ExifTool status check - available: {self.exiftool_available}, persistent: {et is not None}")
            
            if et is not None:
                debug_metadata(f"Reading metadata with ExifTool from: {filename}")
                
                # OPTIMIZATION: Single ExifTool call to get all metadata at once
                try:
                    # Get all needed metadata in one call
                    metadata_output = et.execute('-DateTimeOriginal', '-CreateDate', '-IPTC:Keywords', '-XMP:Keywords', '-XMP:Subject', file_path)
                    
                    if metadata_output and not metadata_output.startswith('Warning') and metadata_output.strip():
                        lines = metadata_output.strip().split('\n')
                        
                        # Parse year from date fields
                        for line in lines:
                            line_lower = line.lower()
                            if ('original' in line_lower or 'create' in line_lower) and ':' in line:
                                # Split on the first colon after the field name
                                parts = line.split(':', 2)  # Split into at most 3 parts
                                if len(parts) >= 3:
                                    date_str = f"{parts[1]}:{parts[2]}".strip()  # Rejoin the time part
                                    try:
                                        # Try parsing with fractional seconds first
                                        if '.' in date_str and date_str.count(':') == 5:
                                            # Format: 2025:08:03 19:09:13.67
                                            year = datetime.strptime(date_str.split('.')[0], '%Y:%m:%d %H:%M:%S').year
                                        else:
                                            # Standard format: 2025:08:03 19:09:13
                                            year = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').year
                                        debug_metadata(f"Found year for {filename}: {year}")
                                        break
                                    except ValueError:
                                        continue
                        
                        # Parse keywords from all keyword fields
                        if self.enable_metadata_reading:
                            for line in lines:
                                line_lower = line.lower()
                                if ('keywords' in line_lower or 'subject' in line_lower) and ':' in line:
                                    keyword_values = line.split(':', 1)[1].strip()
                                    
                                    # Skip empty values
                                    if not keyword_values or keyword_values == '-':
                                        continue
                                        
                                    # Try semicolon separator first, then comma separator
                                    if ';' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(';') if k.strip()]
                                        keywords.extend(split_keywords)
                                    elif ',' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(',') if k.strip()]
                                        keywords.extend(split_keywords)
                                    else:
                                        keywords.append(keyword_values.strip())
                        
                        debug_metadata(f"Found keywords for {filename}: {keywords}")
                        
                except Exception as e:
                    debug_errors(f"Single ExifTool call failed for {filename}: {e}")
                    # Fall back to old method if single call fails
                    debug_metadata(f"Falling back to individual ExifTool calls for {filename}")
                    year, keywords = self._get_metadata_fallback(file_path)
            
            # Fallback to PIL for date if ExifTool not available or didn't find year
            if not year:
                debug_metadata(f"Using PIL fallback for date extraction: {filename}")
                try:
                    with Image.open(file_path) as img:
                        # Try to get EXIF data for JPEG files
                        try:
                            exif = img.getexif()
                            if exif:
                                # Look for DateTimeOriginal tag (36867), DateTime (306), or DateTimeDigitized (36868)
                                datetime_original = exif.get(36867)  # DateTimeOriginal
                                if not datetime_original:
                                    datetime_original = exif.get(306)  # DateTime
                                if not datetime_original:
                                    datetime_original = exif.get(36868)  # DateTimeDigitized
                                    
                                if datetime_original:
                                    year = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S').year
                        except (AttributeError, TypeError, ValueError):
                            pass
                        
                        # Try reading XMP metadata directly from TIFF files for date
                        if not year and file_path.lower().endswith(('.tif', '.tiff')):
                            try:
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                    content_str = content.decode('utf-8', errors='ignore')
                                    
                                    create_date_match = re.search(r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>', content_str)
                                    if create_date_match:
                                        date_str = create_date_match.group(1)
                                        if 'T' in date_str:
                                            date_part = date_str.split('T')[0]
                                            year = datetime.strptime(date_part, '%Y-%m-%d').year
                            except Exception:
                                pass
                except Exception:
                    pass
            
            # Fallback to file creation time for year
            if not year:
                timestamp = os.path.getctime(file_path)
                year = datetime.fromtimestamp(timestamp).year
                debug_metadata(f"Using file creation year: {year}")
            
            # Remove duplicate keywords while preserving order
            unique_keywords = []
            seen = set()
            for keyword in keywords:
                if keyword and keyword not in seen:
                    unique_keywords.append(keyword)
                    seen.add(keyword)
            
            if year:
                debug_metadata(f"Found year for {filename}: {year}")
            if unique_keywords:
                debug_metadata(f"Found keywords for {filename}: {unique_keywords}")
            
            # Extract and cache Cloudinary public_id for upload optimization
            cloudinary_public_id = None
            try:
                from utilities.exiftool_utils import get_cloudinary_public_id_from_metadata
                cloudinary_public_id = get_cloudinary_public_id_from_metadata(file_path)
                if cloudinary_public_id:
                    debug_metadata(f"Found Cloudinary public_id for {filename}: {cloudinary_public_id}")
                else:
                    debug_metadata(f"No Cloudinary public_id found for {filename}")
            except Exception as e:
                debug_metadata(f"Failed to extract public_id for {filename}: {e}")
            
            # Cache the result for future use (including public_id for upload optimization)
            if not hasattr(self, 'image_metadata'):
                self.image_metadata = {}
            self.image_metadata[file_path] = {
                'year': year,
                'keywords': unique_keywords,
                'cloudinary_public_id': cloudinary_public_id  # Cache for upload phase optimization
            }
                
            return year, unique_keywords
                
        except Exception as e:
            error_msg = str(e)[:200]
            debug_errors(f"Metadata read failed for {filename}: {error_msg}")
            self.metadata_errors.append((file_path, [f"Metadata read error: {error_msg}"]))
            
            # Mark as problematic to avoid future attempts
            self.problematic_files.add(file_path)
            
            # Still try to get year from file creation time
            try:
                timestamp = os.path.getctime(file_path)
                year = datetime.fromtimestamp(timestamp).year
            except Exception:
                pass
                
            return year, []

    def _get_metadata_fallback(self, file_path):
        """Fallback method using individual ExifTool calls if combined call fails"""
        try:
            year = None
            keywords = []
            
            # Get creation date using individual calls
            creation_date = None
            for date_tag in ['-DateTimeOriginal', '-CreateDate']:
                try:
                    result = self.et.execute(date_tag, file_path)
                    if result and len(result) > 0:
                        creation_date = result[0].get(date_tag.replace('-', ''))
                        if creation_date and creation_date != '-':
                            break
                except Exception:
                    continue
            
            # Extract year from creation date
            if creation_date and creation_date != '-':
                try:
                    year = int(creation_date[:4])
                except (ValueError, TypeError):
                    pass
            
            # Get keywords using individual calls
            for keyword_tag in ['-IPTC:Keywords', '-XMP:Keywords', '-XMP:Subject']:
                try:
                    result = self.et.execute(keyword_tag, file_path)
                    if result and len(result) > 0:
                        tag_name = keyword_tag.replace('-', '').replace(':', '.')
                        keyword_data = result[0].get(tag_name)
                        if keyword_data:
                            if isinstance(keyword_data, list):
                                keywords.extend(keyword_data)
                            else:
                                keywords.append(keyword_data)
                except Exception:
                    continue
            
            # Remove duplicates and clean keywords
            keywords = list(set([k.strip() for k in keywords if k and k.strip()]))
            
            # Fallback to PIL for date extraction if no metadata date found
            if year is None:
                debug("metadata", f"Using PIL fallback for date extraction: {os.path.basename(file_path)}")
                try:
                    with Image.open(file_path) as img:
                        # Try to get EXIF data for JPEG files
                        try:
                            exif = img.getexif()
                            if exif:
                                # Look for DateTimeOriginal tag (36867), DateTime (306), or DateTimeDigitized (36868)
                                datetime_original = exif.get(36867)  # DateTimeOriginal
                                if not datetime_original:
                                    datetime_original = exif.get(306)  # DateTime
                                if not datetime_original:
                                    datetime_original = exif.get(36868)  # DateTimeDigitized
                                    
                                if datetime_original:
                                    year = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S').year
                        except (AttributeError, TypeError, ValueError):
                            pass
                        
                        # Try reading XMP metadata directly from TIFF files for date
                        if not year and file_path.lower().endswith(('.tif', '.tiff')):
                            try:
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                    content_str = content.decode('utf-8', errors='ignore')
                                    
                                    create_date_match = re.search(r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>', content_str)
                                    if create_date_match:
                                        date_str = create_date_match.group(1)
                                        if 'T' in date_str:
                                            date_part = date_str.split('T')[0]
                                            year = datetime.strptime(date_part, '%Y-%m-%d').year
                            except Exception:
                                pass
                except Exception:
                    pass
            
            # Final fallback to file creation date if no metadata date found
            if year is None:
                try:
                    timestamp = os.path.getctime(file_path)
                    year = datetime.fromtimestamp(timestamp).year
                except Exception:
                    pass
                    
            return year, keywords
            
        except Exception as e:
            debug("exiftool", f"Fallback metadata extraction failed for {os.path.basename(file_path)}: {e}")
            # Final fallback to file creation date
            try:
                timestamp = os.path.getctime(file_path)
                year = datetime.fromtimestamp(timestamp).year
            except Exception:
                pass
            return year, []

    def has_keywords_changed(self, file_path, current_keywords_text):
        """Check if keywords have changed compared to original"""
        # Parse current keywords from text field
        current_keywords = [k.strip() for k in current_keywords_text.split(',') if k.strip()]
        
        # Get original keywords (including year)
        original_keywords = self.original_keywords.get(file_path, [])
        
        # Check if this file has imported Cloudinary tags that differ from local
        has_cloudinary_import = hasattr(self, 'cloudinary_imported_files') and file_path in self.cloudinary_imported_files
        
        # Check if this is a new file that had the year automatically added
        is_new_file_with_year = hasattr(self, 'new_files_with_year') and file_path in self.new_files_with_year
        
        # Compare sets (order doesn't matter for keywords)
        current_set = set(current_keywords)
        original_set = set(original_keywords)
        
        changed = current_set != original_set or has_cloudinary_import
        if changed:
            debug("tags", f"Keywords changed for {os.path.basename(file_path)}")
            debug("tags", f"  Original: {sorted(original_set)}")
            debug("tags", f"  Current:  {sorted(current_set)}")
            if has_cloudinary_import:
                debug("tags", f"  ✅ Cloudinary import detected - flagged for saving")
        else:
            debug("tags", f"Keywords unchanged for {os.path.basename(file_path)}")
        
        return changed

    def _cleanup_orphaned_public_id(self, file_path):
        """
        Clean up orphaned public_id metadata for files that are no longer on Cloudinary.
        Returns: 1 if cleanup performed, 0 if no cleanup needed
        """
        try:
            # Check if Cloudinary is enabled
            if not (self.cloudinary_connected and hasattr(self, 'cloudinary_updater') and self.cloudinary_updater):
                return 0  # No cleanup if Cloudinary not available
            
            # Get public_id from file metadata
            from utilities.cloudinary_upload_handler import get_cloudinary_public_id_from_metadata
            local_public_id = get_cloudinary_public_id_from_metadata(file_path)
            
            if not local_public_id:
                return 0  # No public_id to check
            
            # Check if this public_id exists in Cloudinary
            cloudinary_files = getattr(self, 'cloudinary_files_cache', [])
            cloudinary_public_ids = {cf.get('public_id', '') for cf in cloudinary_files}
            
            debug_cloudinary(f"Checking orphaned status for {local_public_id}")
            debug_cloudinary(f"  Cloudinary cache has {len(cloudinary_files)} files")
            debug_cloudinary(f"  Looking for public_id: '{local_public_id}'")
            
            # IMPORTANT: Only consider empty cache as "all orphaned" if we have successfully
            # connected to Cloudinary AND attempted to populate the cache. This prevents
            # valid public_ids from being removed during startup before cache is populated.
            
            if len(cloudinary_files) == 0 and self.cloudinary_cache_populated:
                # We've connected and tried to populate cache, but it's empty - so any public_id is orphaned
                debug_cloudinary(f"  🔥 Cloudinary cache is EMPTY after population attempt - public_ids are orphaned!")
                debug_cloudinary(f"  ❌ {local_public_id} is orphaned (Cloudinary has no files)")
                is_orphaned = True
            elif len(cloudinary_files) == 0:
                # Cache is empty but we haven't tried to populate it yet - skip cleanup for now
                debug_cloudinary(f"  ⏳ Cloudinary cache not yet populated - skipping orphaned cleanup for now")
                return 0
            elif local_public_id not in cloudinary_public_ids:
                debug_cloudinary(f"  ❌ Public_id not found in cache - marking as orphaned")
                debug_cloudinary(f"  Available public_ids: {list(cloudinary_public_ids)[:5]}")  # Show first 5 for debugging
                is_orphaned = True
            else:
                debug_cloudinary(f"  ✅ Public_id found in cache - not orphaned")
                is_orphaned = False
            
            if is_orphaned:
                # Orphaned public_id - remove it from metadata
                debug_cloudinary(f"Found orphaned public_id {local_public_id} in {os.path.basename(file_path)} - cleaning up")
                
                # Use ExifTool to remove the public_id metadata
                if self.exiftool_available and self.persistent_exiftool:
                    try:
                        # Remove the UserComment field that contains the public_id
                        self.persistent_exiftool.execute("-UserComment=", file_path, "-overwrite_original")
                        debug_cloudinary(f"✅ Removed orphaned public_id from {os.path.basename(file_path)}")
                        return 1
                    except Exception as e:
                        debug_cloudinary(f"❌ Failed to remove orphaned public_id from {file_path}: {e}")
                        return 0
                else:
                    debug_cloudinary(f"❌ ExifTool not available for cleanup")
                    return 0
            
            return 0  # No cleanup needed
            
        except Exception as e:
            debug_cloudinary(f"Error during orphaned public_id cleanup for {file_path}: {e}")
            return 0

    def _import_cloudinary_tags_for_file(self, file_path, local_keywords):
        """
        Import Cloudinary tags for a single file if public_id matches.
        Returns: Cloudinary keywords list if found and different, None if no import needed
        """
        try:
            # Get public_id from file metadata
            from utilities.cloudinary_upload_handler import get_cloudinary_public_id_from_metadata
            local_public_id = get_cloudinary_public_id_from_metadata(file_path)
            
            if not local_public_id:
                debug_cloudinary(f"No public_id found in {os.path.basename(file_path)} - keeping local tags")
                return None
            
            # Get Cloudinary files data from main app cache
            cloudinary_files = getattr(self, 'cloudinary_files_cache', [])
            if not cloudinary_files:
                debug_cloudinary(f"No Cloudinary files data available in main app cache")
                return None
            
            debug_cloudinary(f"Searching for public_id '{local_public_id}' in {len(cloudinary_files)} Cloudinary files")
            
            # Debug: Show what we're looking for vs what's available
            debug_cloudinary(f"Target public_id: '{local_public_id}'")
            
            # Find matching Cloudinary file by public_id
            cloudinary_file = None
            for i, cf in enumerate(cloudinary_files):
                cf_public_id = cf.get('public_id', '')
                debug_cloudinary(f"  File {i+1}: public_id='{cf_public_id}', tags={cf.get('tags', [])} (type: {type(cf.get('tags', []))})")
                if cf_public_id == local_public_id:
                    cloudinary_file = cf
                    debug_cloudinary(f"Found matching Cloudinary file for public_id: {local_public_id}")
                    break
            
            if not cloudinary_file:
                debug_cloudinary(f"No Cloudinary file found for public_id: {local_public_id}")
                debug_cloudinary(f"Available public_ids: {[cf.get('public_id', 'NO_ID') for cf in cloudinary_files[:5]]}")  # Show first 5 for debugging
                return None
            
            # Extract Cloudinary tags
            cloudinary_tags = cloudinary_file.get('tags', [])
            if not cloudinary_tags:
                debug_cloudinary(f"No tags in Cloudinary for {local_public_id} - keeping local tags")
                return None
            
            debug_cloudinary(f"Found {len(cloudinary_tags)} tags in Cloudinary for {local_public_id}: {cloudinary_tags}")
            
            # Convert to same format as local keywords (list of strings)
            cloudinary_keywords = [str(tag).strip() for tag in cloudinary_tags if str(tag).strip()]
            
            # Compare with local keywords to see if import is needed
            local_set = set(local_keywords) if local_keywords else set()
            cloudinary_set = set(cloudinary_keywords)
            
            if local_set == cloudinary_set:
                debug_cloudinary(f"Cloudinary tags match local tags for {os.path.basename(file_path)} - no import needed")
                return None
            
            debug_cloudinary(f"Importing Cloudinary tags for {os.path.basename(file_path)}: {cloudinary_keywords}")
            debug_cloudinary(f"  Local tags: {local_keywords}")
            debug_cloudinary(f"  Cloudinary tags: {cloudinary_keywords}")
            
            return cloudinary_keywords
            
        except Exception as e:
            debug_cloudinary(f"Error importing Cloudinary tags for {file_path}: {e}")
            return None

    # NOTE: Platform-specific tag writing methods removed to prevent duplication
    # The streamlined metadata strategy in save_keywords_to_image() now handles
    # cross-platform compatibility without redundant field writing

    def write_platform_specific_tags(self, file_path, keywords):
        """Write platform-specific tags for enhanced OS integration"""
        import platform
        
        current_platform = platform.system().lower()
        
        if current_platform == 'darwin':
            # macOS: Write Finder tags and extended attributes
            return self.write_macos_finder_tags(file_path, keywords)
        elif current_platform == 'windows':
            # Windows: Write Windows Explorer compatible metadata
            return self.write_windows_explorer_tags(file_path, keywords)
        else:
            # Linux or other: No platform-specific handling needed
            return True, "No platform-specific tags needed"

    def write_windows_explorer_tags(self, file_path, keywords):
        """Write Windows Explorer compatible tags using ExifTool (avoiding duplication with standard fields)"""
        try:
            if not keywords:
                return True, "No keywords to write"
            
            if not self.exiftool_available or not self.persistent_exiftool:
                return False, "ExifTool not available for Windows Explorer tags"
            
            debug("tags", f"Writing Windows Explorer tags to {os.path.basename(file_path)}")
            
            # Use the persistent ExifTool instance
            et = self.persistent_exiftool
            
            # Windows Explorer-specific fields that DON'T overlap with standard metadata
            # Note: We avoid Subject and Keywords to prevent duplication with XMP-dc:Subject and IPTC:Keywords
            cmd_args = []
            
            # 1. Windows Tags field (Windows 10+ specific - separate from standard fields)
            cmd_args.append('-Tags=')  # Clear existing
            if keywords:
                keywords_str = ';'.join(keywords)
                cmd_args.append(f'-Tags={keywords_str}')
            
            # 2. XMP-microsoft:Category (Windows-specific category field)
            cmd_args.append('-XMP-microsoft:Category=')  # Clear existing
            if keywords:
                for keyword in keywords:
                    cmd_args.append(f'-XMP-microsoft:Category={keyword}')
            
            # 3. Write to Windows File Properties via XMP
            cmd_args.append('-XMP-xmp:Label=')  # Clear existing
            if keywords:
                # Use first keyword as label (Windows file properties)
                cmd_args.append(f'-XMP-xmp:Label={keywords[0]}')
            
            # Execute the Windows-specific metadata write
            if cmd_args:
                cmd_args.extend(['-overwrite_original', file_path])
                debug("tags", f"Executing Windows Explorer metadata command: {' '.join(cmd_args)}")
                result = et.execute(*cmd_args)
                debug("tags", f"Windows Explorer metadata result: {result}")
            
            debug("tags", f"Successfully wrote Windows Explorer tags to {os.path.basename(file_path)}")
            return True, "Success"
                
        except Exception as e:
            debug_errors(f"Error writing Windows Explorer tags: {e}")
            return False, f"Error: {str(e)}"

    def write_macos_finder_tags(self, file_path, keywords):
        """Write macOS Finder tags using extended attributes and Spotlight metadata"""
        import subprocess
        import plistlib
        import os
        
        try:
            if not keywords or os.name != 'posix' or not hasattr(os, 'uname') or os.uname().sysname != 'Darwin':
                return True, "Not macOS or no keywords"
            
            debug("tags", f"Writing macOS Finder tags to {os.path.basename(file_path)}: {keywords}")
            
            # Method 1: Write Extended Attributes (for Finder display)
            # Use the EXACT format that macOS Finder uses: simple array of strings
            # Based on analysis of working macOS-tagged files
            tag_data = keywords  # Simple list of strings, no color info needed here
            
            # Convert to binary plist format (same as macOS native)
            debug("tags", f"Creating binary plist for {len(keywords)} keywords")
            plist_data = plistlib.dumps(tag_data, fmt=plistlib.FMT_BINARY)
            debug("tags", f"Binary plist created: {len(plist_data)} bytes")
            
            # Convert binary data to hex string
            hex_data = plist_data.hex()
            debug("tags", f"Hex data created: {len(hex_data)} characters")
            
            # Use xattr command with hex data
            xattr_cmd = [
                'xattr', '-w', '-x', 'com.apple.metadata:_kMDItemUserTags',
                hex_data, file_path
            ]
            debug("tags", f"Executing xattr command: {' '.join(xattr_cmd[:4])} [hex_data] {file_path}")
            
            result = subprocess.run(xattr_cmd, capture_output=True, text=True)
            
            debug("tags", f"xattr return code: {result.returncode}")
            if result.stdout:
                debug("tags", f"xattr stdout: {result.stdout}")
            if result.stderr:
                debug("tags", f"xattr stderr: {result.stderr}")
            
            if result.returncode != 0:
                debug_errors(f"Failed to write extended attributes: {result.stderr}")
                return False, f"xattr error: {result.stderr}"
            
            # Verify the write was successful
            try:
                verify_result = subprocess.run(['xattr', '-p', '-x', 'com.apple.metadata:_kMDItemUserTags', file_path], capture_output=True, text=True)
                if verify_result.returncode == 0:
                    debug("tags", f"✅ Verification: Extended attributes successfully written and readable")
                else:
                    debug("tags", f"⚠️ Verification failed: Cannot read back extended attributes")
            except Exception as verify_e:
                debug("tags", f"⚠️ Verification error: {verify_e}")
            
            debug("tags", f"Successfully wrote Finder extended attributes for {os.path.basename(file_path)}")
            
            # Method 2: Write Spotlight Metadata (for search and indexing)
            try:
                # Create metadata in format Spotlight understands
                spotlight_metadata = {
                    'kMDItemUserTags': keywords,
                    'kMDItemKeywords': keywords,
                    'kMDItemSubject': ', '.join(keywords)
                }
                
                # Write using xattr for Spotlight metadata as well
                for key, value in spotlight_metadata.items():
                    if isinstance(value, list):
                        # For arrays, write as plist
                        array_plist = plistlib.dumps(value, fmt=plistlib.FMT_BINARY)
                        array_hex = array_plist.hex()
                        subprocess.run([
                            'xattr', '-w', '-x', f'com.apple.metadata:{key}',
                            array_hex, file_path
                        ], capture_output=True)
                    else:
                        # For strings, write directly
                        subprocess.run([
                            'xattr', '-w', f'com.apple.metadata:{key}',
                            value, file_path
                        ], capture_output=True)
                
                debug("tags", "Successfully wrote Spotlight metadata")
                
            except Exception as spotlight_error:
                debug_errors(f"Spotlight metadata write failed: {spotlight_error}")
                # Continue anyway, extended attributes are still written
            
            debug("tags", f"Successfully wrote macOS Finder tags to {os.path.basename(file_path)}")
            
            # Force Spotlight reindex for immediate visibility
            try:
                subprocess.run(['mdimport', file_path], capture_output=True, timeout=5)
                debug("tags", f"Triggered Spotlight reindex for {os.path.basename(file_path)}")
            except:
                pass  # Non-critical if reindex fails
            
            return True, "Success"
                
        except Exception as e:
            debug_errors(f"Error writing macOS Finder tags: {e}")
            return False, f"Error: {str(e)}"

    def save_keywords_to_image(self, file_path, keywords_text):
        """Save keywords to image metadata using ExifTool (with fallback notification)"""
        # Check if keywords have actually changed
        if not self.has_keywords_changed(file_path, keywords_text):
            debug("tags", f"Skipping save for {os.path.basename(file_path)} - no changes")
            return True, ""
            
        if not keywords_text.strip():
            # If we're clearing keywords and original was empty, no change
            original_keywords = self.original_keywords.get(file_path, [])
            if not original_keywords:
                return True, ""
            # Otherwise, we're actually clearing keywords
        
        # Parse keywords from text (comma-separated)
        keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if self.exiftool_available and self.persistent_exiftool:
            try:
                debug("tags", f"Saving keywords with persistent ExifTool to {file_path}: {keywords}")
                
                # Use the persistent ExifTool instance (no context manager needed)
                et = self.persistent_exiftool
                
                # Check if format supports metadata writing based on ExifTool capabilities
                # Based on ExifTool -listwf output: GIF, PNG, JPEG, TIFF support writing
                # BMP and many other formats do NOT support metadata writing
                writable_formats = ['.jpg', '.jpeg', '.tiff', '.tif', '.png', '.gif', '.webp']

                if file_ext not in writable_formats:
                    # Format doesn't support metadata writing
                    format_msg = f"Format {file_ext.upper()} doesn't support metadata writing. Keywords preserved in application only."
                    debug("tags", format_msg)
                    return False, format_msg
                
                # OPTIMIZED CROSS-PLATFORM METADATA STRATEGY:
                # Write to core standard fields that work universally without causing duplicates
                # Each field serves a specific purpose and doesn't overlap
                
                try:
                    # IMPORTANT: Preserve Cloudinary public_id if it exists
                    # Check if there's a Cloudinary public_id in UserComment before writing
                    existing_public_id = None
                    try:
                        user_comment_result = et.execute('-UserComment', file_path)
                        if user_comment_result and not user_comment_result.startswith('Warning'):
                            for line in user_comment_result.strip().split('\n'):
                                if 'usercomment' in line.lower() and ':' in line:
                                    comment_value = line.split(':', 1)[1].strip()
                                    if comment_value.startswith('cloudinary_public_id:'):
                                        existing_public_id = comment_value
                                        debug("tags", f"Found existing Cloudinary public_id in UserComment: {existing_public_id}")
                                        break
                    except Exception as e:
                        debug("tags", f"Could not check existing UserComment: {e}")
                    
                    # Build optimized command arguments for universal compatibility
                    cmd_args = []
                    
                    # === CORE STANDARD FIELDS (No Platform Overlap) ===
                    
                    # 1. XMP-dc:Subject (Dublin Core standard - most universal, read by all platforms)
                    cmd_args.append('-XMP-dc:Subject=')  # Clear existing
                    if keywords:
                        for keyword in keywords:
                            cmd_args.append(f'-XMP-dc:Subject={keyword}')
                    
                    # 2. IPTC:Keywords (Legacy IPTC standard - widely supported)
                    cmd_args.append('-IPTC:Keywords=')  # Clear existing
                    if keywords:
                        for keyword in keywords:
                            cmd_args.append(f'-IPTC:Keywords={keyword}')
                    
                    # 3. XMP:Keywords (XMP Keywords field - different from XMP-dc:Subject)
                    cmd_args.append('-XMP:Keywords=')  # Clear existing
                    if keywords:
                        keywords_str = ';'.join(keywords)
                        cmd_args.append(f'-XMP:Keywords={keywords_str}')
                    
                    # 4. Format-specific optimization (PRESERVE UserComment for Cloudinary public_id)
                    if file_ext in ['.jpg', '.jpeg', '.tiff', '.tif']:
                        # For JPEG/TIFF: Use EXIF ImageDescription for tag description
                        if keywords:
                            description = f"Keywords: {', '.join(keywords)}"
                            cmd_args.append(f'-EXIF:ImageDescription={description}')
                        
                        # PRESERVE OR RESTORE Cloudinary public_id in UserComment
                        if existing_public_id:
                            # Restore the existing Cloudinary public_id
                            cmd_args.append(f'-UserComment={existing_public_id}')
                            debug("tags", f"Preserving Cloudinary public_id in UserComment")
                        # If no existing public_id, leave UserComment alone (don't overwrite)
                    
                    # Execute optimized operations in a SINGLE ExifTool call
                    if cmd_args:
                        cmd_args.extend(['-overwrite_original', file_path])
                        debug("tags", f"Executing streamlined ExifTool command with {len(cmd_args)-2} tag operations")
                        debug("tags", f"Full ExifTool command: {' '.join(cmd_args)}")
                        result = et.execute(*cmd_args)
                        debug("tags", f"ExifTool result: {result}")
                    
                    # Update original keywords after successful save (including year)
                    self.original_keywords[file_path] = keywords.copy()
                    
                    # PLATFORM-SPECIFIC TAGS: Write OS-specific tags for Finder/Explorer integration
                    # This is essential for macOS Finder and Windows Explorer to display tags
                    if keywords:  # Only write if there are keywords
                        platform_success, platform_msg = self.write_platform_specific_tags(file_path, keywords)
                        if platform_success:
                            debug("tags", f"Platform-specific tags written successfully: {platform_msg}")
                        else:
                            debug("tags", f"Platform-specific tags failed: {platform_msg}")
                    
                    # Remove from new files tracking after successful save
                    if hasattr(self, 'new_files_with_year') and file_path in self.new_files_with_year:
                        self.new_files_with_year.remove(file_path)
                    
                    debug("tags", f"Successfully saved keywords to {file_path}")
                    return True, ""
                except Exception as write_e:
                    error_msg = f"ExifTool write error: {str(write_e)[:200]}"
                    debug_errors(error_msg)
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"ExifTool write error: {str(e)[:200]}"
                debug_errors(error_msg)
                return False, error_msg
        
        else:
            # ExifTool not available - return informative message
            return False, "ExifTool not available for writing metadata. Keywords will be preserved in the application but not saved to file metadata."

    def save_all_keywords(self):
        """Save keywords from all image text fields to their respective files"""
        # Get current widgets from flow manager
        current_widgets = list(self.image_flow_manager.image_widgets.values()) if hasattr(self, 'image_flow_manager') else []
        
        if not current_widgets:
            QMessageBox.information(self, "Save Keywords", "No images loaded to save keywords to.")
            return

        success_count = 0
        skipped_count = 0
        error_files = []
        orphaned_cleanup_count = 0
        
        # Show progress bar with saving message
        saving_message = f"Saving tags..."
        self.show_progress(len(current_widgets), saving_message)
        
        for i, widget in enumerate(current_widgets):
            if hasattr(widget, 'file_path'):
                file_path = widget.file_path
                keywords_text = self.get_widget_text(widget)
                
                self.update_progress(i + 1)
                QApplication.processEvents()  # Keep UI responsive
                
                # Check if changes exist before attempting save
                if not self.has_keywords_changed(file_path, keywords_text):
                    skipped_count += 1
                    continue
                
                success, error_msg = self.save_keywords_to_image(file_path, keywords_text)
                
                if success:
                    success_count += 1
                    # Check for orphaned public_id cleanup after successful save
                    orphaned_cleanup_count += self._cleanup_orphaned_public_id(file_path)
                    # Clear the cloudinary imported flag after successful save
                    if hasattr(self, 'cloudinary_imported_files') and file_path in self.cloudinary_imported_files:
                        self.cloudinary_imported_files.remove(file_path)
                        debug_cloudinary(f"Cleared Cloudinary import flag for {os.path.basename(file_path)} after successful save")
                else:
                    error_files.append((os.path.basename(file_path), error_msg))
        
        self.hide_progress()
        
        # Show results to user
        total_processed = success_count + len(error_files)
        
        # Separate format limitation errors from actual write errors
        format_errors = []
        write_errors = []
        
        for filename, error in error_files:
            if "doesn't support metadata writing" in error:
                format_errors.append((filename, error))
            else:
                write_errors.append((filename, error))
        
        if error_files:
            error_message = f"Keywords saved to {success_count} of {total_processed} modified images"
            if skipped_count > 0:
                error_message += f" ({skipped_count} images skipped - no changes)"
            
            if format_errors:
                error_message += f"\n\n{len(format_errors)} files couldn't be saved due to format limitations:\n"
                for filename, error in format_errors:
                    file_ext = os.path.splitext(filename)[1].upper()
                    error_message += f"• {filename} ({file_ext} format doesn't support metadata)\n"
                error_message += "\nNote: Keywords are preserved in the application and will be available when you reopen these files."
            
            if write_errors:
                error_message += f"\n\n{len(write_errors)} files had actual write errors:\n"
                for filename, error in write_errors:
                    error_message += f"• {filename}: {error}\n"
            
            if format_errors and not write_errors:
                # Only format limitation errors - less alarming message
                QMessageBox.information(self, "Save Keywords - Format Limitations", error_message)
            else:
                # Actual write errors present - warning message
                QMessageBox.warning(self, "Save Keywords - Partial Success", error_message)
        else:
            if total_processed == 0 and skipped_count > 0:
                base_message = f"No images needed saving - all {skipped_count} images have unchanged keywords!"
                if orphaned_cleanup_count > 0:
                    base_message += f"\nCleaned up {orphaned_cleanup_count} orphaned Cloudinary references."
                QMessageBox.information(self, "Save Keywords", base_message)
            elif skipped_count > 0:
                base_message = (f"Successfully saved keywords to {success_count} modified images! "
                               f"({skipped_count} images skipped - no changes)")
                if orphaned_cleanup_count > 0:
                    base_message += f"\nCleaned up {orphaned_cleanup_count} orphaned Cloudinary references."
                QMessageBox.information(self, "Save Keywords", base_message)
            else:
                base_message = f"Successfully saved keywords to all {success_count} images!"
                if orphaned_cleanup_count > 0:
                    base_message += f"\nCleaned up {orphaned_cleanup_count} orphaned Cloudinary references."
                QMessageBox.information(self, "Save Keywords", base_message)

    def show_metadata_errors(self):
        """Show accumulated metadata errors to the user"""
        if not self.metadata_errors:
            return
        
        error_message = "Metadata reading errors encountered:\n\n"
        for file_path, errors in self.metadata_errors:
            filename = os.path.basename(file_path)
            error_message += f"• {filename}:\n"
            for error in errors:
                error_message += f"  - {error}\n"
            error_message += "\n"
        
        QMessageBox.warning(self, "Metadata Reading Errors", error_message)
        self.metadata_errors.clear()  # Clear after showing

    def show_unsupported_files(self):
        """Show list of unsupported files to the user"""
        if not self.unsupported_files:
            return
        
        error_message = "Some files could not be loaded due to unsupported formats:\n\n"
        for file_path, reason in self.unsupported_files:
            filename = os.path.basename(file_path)
            error_message += f"• {filename}: {reason}\n"
        
        error_message += "\nSupported formats: JPG, JPEG, PNG, TIFF, TIF, GIF, WEBP\n"
        error_message += "Unsupported formats: BMP, PSD (planned for future updates)"
        QMessageBox.information(self, "Unsupported Files", error_message)
        self.unsupported_files.clear()  # Clear after showing

    def create_progress_overlay(self):
        """Create a centered progress bar overlay"""
        # Create overlay widget
        self.progress_overlay = QWidget(self)
        self.progress_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.5);
            }
        """)
        
        # Create layout for overlay
        overlay_layout = QVBoxLayout(self.progress_overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        
        # Create progress bar container
        progress_container = QWidget()
        progress_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        # Create progress bar container with adaptive height
        progress_container = QWidget()
        progress_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        # Create progress bar layout with controlled spacing
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(15)
        progress_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add dynamic progress label with flexible height
        self.progress_label = QLabel("Loading images...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 12px; font-weight: bold; padding: 5px;")
        self.progress_label.setWordWrap(True)  # Enable word wrap for multi-line text
        self.progress_label.setMinimumHeight(20)  # Minimum height for single line
        self.progress_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        progress_layout.addWidget(self.progress_label)
        
        # Create progress bar with fixed height
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)  # Fixed height for progress bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                font-size: 10px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Set adaptive width and let height adjust based on content
        progress_container.setFixedWidth(320)  # Fixed width, adaptive height
        
        # Add container to overlay
        overlay_layout.addWidget(progress_container)
        
        # Position overlay to cover the entire window
        self.progress_overlay.resize(self.size())
        self.progress_overlay.hide()
    
    def show_progress(self, total_files, message=None):
        """Show progress bar with total file count and custom message"""
        if not self.progress_overlay:
            self.create_progress_overlay()
        
        # Set custom message or default based on context
        if message:
            self.progress_label.setText(message)
            # Count lines to adjust container height dynamically
            line_count = message.count('\n') + 1
            # Calculate adaptive height: base height + extra height per line
            base_height = 80  # Base height for single line + progress bar
            line_height = 20  # Additional height per extra line
            adaptive_height = base_height + (line_count - 1) * line_height
            
            # Get the progress container (first child of overlay layout)
            overlay_layout = self.progress_overlay.layout()
            if overlay_layout and overlay_layout.count() > 0:
                progress_container = overlay_layout.itemAt(0).widget()
                if progress_container:
                    progress_container.setFixedHeight(adaptive_height)
        else:
            # Default fallback
            self.progress_label.setText("Processing files...")
            # Reset to single line height
            overlay_layout = self.progress_overlay.layout()
            if overlay_layout and overlay_layout.count() > 0:
                progress_container = overlay_layout.itemAt(0).widget()
                if progress_container:
                    progress_container.setFixedHeight(80)
        
        self.progress_bar.setRange(0, total_files)
        self.progress_bar.setValue(0)
        self.progress_overlay.resize(self.size())
        self.progress_overlay.show()
        self.progress_overlay.raise_()
    
    def update_progress(self, current_file):
        """Update progress bar with file count"""
        if self.progress_bar:
            self.progress_bar.setValue(current_file)
            QApplication.processEvents()  # Force UI update
    
    def update_upload_progress(self, percentage):
        """Update progress bar with percentage (0-100) for uploads"""
        if self.progress_bar:
            # Convert percentage to file count based on total range
            total_files = self.progress_bar.maximum()
            current_value = int((percentage / 100.0) * total_files)
            self.progress_bar.setValue(current_value)
            QApplication.processEvents()  # Force UI update
    
    def hide_progress(self):
        """Hide progress bar"""
        if self.progress_overlay:
            self.progress_overlay.hide()
        # Update status bar and button states when loading is complete
        self.update_status_bar()
    
    def resizeEvent(self, event):
        """Handle window resize to reposition progress overlay and update layout"""
        super().resizeEvent(event)
        if self.progress_overlay:
            self.progress_overlay.resize(self.size())
            
        # Trigger layout update with a delay to handle window resizing
        if hasattr(self, 'resize_timer'):
            self.resize_timer.start()

    def update_status_bar(self):
        """Update the status bar with selection info or loaded images count"""
        if self.selected_images:
            self.statusBar().showMessage(f"Selected {len(self.selected_images)} images")
            # Enable clear tags button when images are selected
            self.clearTagsButton.setEnabled(True)
        else:
            # Show loaded images count in ready state
            loaded_count = len(self.image_flow_manager.image_widgets) if hasattr(self, 'image_flow_manager') and self.image_flow_manager else 0
            if loaded_count > 0:
                self.statusBar().showMessage(f"Ready - {loaded_count} images loaded")
            else:
                self.statusBar().showMessage("Ready")
            # Disable clear tags button when no images are selected
            self.clearTagsButton.setEnabled(False)

    def select_all_images(self):
        """Select all currently loaded images"""
        if not self.image_flow_manager.image_widgets:
            return
        
        debug_ui_events("Selecting all images using ImageFlowManager")
        
        # Use ImageFlowManager's select_all method
        self.image_flow_manager.select_all()
        
        debug_ui_events(f"Selected {len(self.image_flow_manager.selected_files)} images")

    def clear_selected_tags(self):
        """Clear all tags from selected images"""
        if not self.selected_images:
            return
        
        debug("ui_events", f"Clearing tags from {len(self.selected_images)} selected images")
        
        # Show confirmation dialog
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 
            'Clear Tags Confirmation',
            f'Are you sure you want to clear all tags from {len(self.selected_images)} selected images?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Clear tags from selected images
        cleared_count = 0
        current_widgets = list(self.image_flow_manager.image_widgets.values()) if hasattr(self, 'image_flow_manager') else []
        for widget in current_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                # Clear the text field using helper function
                self.set_widget_text(widget, "")
                cleared_count += 1
                
                # Update metadata to empty
                if widget.file_path in self.image_metadata:
                    self.image_metadata[widget.file_path]['keywords'] = ""
        
        debug("tags", f"Cleared tags from {cleared_count} images")
        
        # Show completion message
        QMessageBox.information(
            self,
            'Tags Cleared',
            f'Successfully cleared tags from {cleared_count} images.'
        )

    def create_preview(self, file_path):
        """Create and store a preview of the image with metadata reading for accurate progress"""
        try:
            print(f"Creating preview from file: {file_path}")
            
            # Check file extension first
            _, ext = os.path.splitext(file_path.lower())
            if ext == '.psd':
                print(f"Warning: PSD files are not currently supported for preview: {file_path}")
                self.unsupported_files.append((file_path, "PSD format not currently supported"))
                return None
            elif ext == '.bmp':
                print(f"Warning: BMP files are not currently supported for preview: {file_path}")
                self.unsupported_files.append((file_path, "BMP format not currently supported"))
                return None
            
            with Image.open(file_path) as img:
                orig_width, orig_height = img.size
                print(f"Original size: {orig_width}x{orig_height}")
                
                if orig_width > orig_height:
                    if orig_width > self.MAX_PREVIEW_SIZE:
                        width = self.MAX_PREVIEW_SIZE
                        height = int(orig_height * (self.MAX_PREVIEW_SIZE / orig_width))
                    else:
                        width = orig_width
                        height = orig_height
                else:
                    if orig_height > self.MAX_PREVIEW_SIZE:
                        height = self.MAX_PREVIEW_SIZE
                        width = int(orig_width * (self.MAX_PREVIEW_SIZE / orig_height))
                    else:
                        width = orig_width
                        height = orig_height
                
                # Optimize large image handling: resize with PIL first for better performance
                if orig_width > self.MAX_PREVIEW_SIZE or orig_height > self.MAX_PREVIEW_SIZE:
                    # For large images, resize with PIL first (much faster than QPixmap)
                    try:
                        # Use LANCZOS for better quality (fallback to older constant for older PIL versions)
                        resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'LANCZOS', 1))
                    except AttributeError:
                        resample_filter = 1  # LANCZOS constant value
                    
                    # Handle ICC color profiles that might cause Qt conversion issues
                    if 'icc_profile' in img.info:
                        print(f"Image has ICC profile ({len(img.info['icc_profile'])} bytes), removing for Qt compatibility...")
                        # Clear any cached preview for this image since we're fixing a color profile issue
                        if file_path in self.image_previews:
                            print(f"Clearing cached preview for {os.path.basename(file_path)} due to ICC profile fix")
                            del self.image_previews[file_path]
                        
                        img = img.copy()
                        del img.info['icc_profile']
                    
                    resized_img = img.resize((width, height), resample_filter)
                    
                    # Convert PIL image to QPixmap based on image mode
                    if resized_img.mode == 'RGBA':
                        qimage = QImage(resized_img.tobytes(), resized_img.width, resized_img.height, QImage.Format_RGBA8888)
                        pixmap = QPixmap.fromImage(qimage)
                    elif resized_img.mode == 'RGB':
                        # Ensure proper RGB byte order for Qt with ICC profile handling
                        rgb_data = resized_img.tobytes('raw', 'RGB')
                        qimage = QImage(rgb_data, resized_img.width, resized_img.height, QImage.Format_RGB888)
                        
                        # Verify QImage is not null and create QPixmap
                        if qimage.isNull():
                            print("ERROR: QImage is null, falling back to QPixmap")
                            pixmap = QPixmap(file_path)
                        else:
                            pixmap = QPixmap.fromImage(qimage)
                    else:
                        # Convert other modes to RGB first
                        resized_img = resized_img.convert('RGB')
                        rgb_data = resized_img.tobytes('raw', 'RGB')
                        qimage = QImage(rgb_data, resized_img.width, resized_img.height, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimage)
                    print(f"Used PIL optimization for large image: {orig_width}x{orig_height} -> {resized_img.width}x{resized_img.height}")
                else:
                    # For small images, use the original QPixmap method
                    pixmap = QPixmap(file_path)
                    print(f"Used QPixmap for small image: {orig_width}x{orig_height}")
                
                if not pixmap.isNull():
                    print(f"Preview size: {pixmap.width()}x{pixmap.height()}")
                    self.image_previews[file_path] = pixmap
                    
                    # Check if metadata already exists to avoid duplicate reading
                    if hasattr(self, 'image_metadata') and file_path in self.image_metadata:
                        year = self.image_metadata[file_path]['year']
                        keywords = self.image_metadata[file_path]['keywords']
                        debug_metadata(f"Using cached metadata for {os.path.basename(file_path)}")
                    else:
                        # Read metadata during preview creation for accurate progress tracking
                        year, keywords = self.get_image_metadata(file_path)
                        
                        # Store metadata with the preview for later use
                        if not hasattr(self, 'image_metadata'):
                            self.image_metadata = {}
                        self.image_metadata[file_path] = {
                            'year': year,
                            'keywords': keywords
                        }
                    
                    # Store original keywords for change tracking (should match what will be in UI)
                    if not hasattr(self, 'original_keywords'):
                        self.original_keywords = {}
                    
                    # Build the original keywords list to match what will appear in UI
                    ui_keywords = []
                    if year:
                        ui_keywords.append(str(year))
                    
                    # Add existing keywords (avoid duplicating year if it's already in keywords)
                    for keyword in keywords if keywords else []:
                        if keyword and keyword.strip() and keyword.strip() != str(year):
                            ui_keywords.append(keyword.strip())
                    
                    # Store the keywords that will actually appear in the UI
                    self.original_keywords[file_path] = ui_keywords.copy()
                    
                    # Year will be added to UI and saved as a keyword in metadata
                    
                    return pixmap
                else:
                    print(f"Error: Could not create preview for {file_path} - QPixmap returned null (unsupported format or corrupted file)")
                    return None
                    
        except Exception as e:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.psd', '.psb']:
                reason = "PSD/PSB format not supported"
                print(f"Error creating preview for {file_path}: {reason}")
                self.unsupported_files.append((file_path, reason))
            elif file_ext in ['.ai', '.eps']:
                reason = "Vector formats (AI/EPS) not supported"
                print(f"Error creating preview for {file_path}: {reason}")
                self.unsupported_files.append((file_path, reason))
            else:
                reason = f"File error: {str(e)}"
                print(f"Error creating preview for {file_path}: {e}")
                self.unsupported_files.append((file_path, reason))
            return None

    def update_layout(self, value=None):
        """Update the layout using the new ImageFlowManager"""
        print("\nStarting update_layout with ImageFlowManager...")
        
        # Calculate scaled size
        ratio = preview.width() / preview.height()
        scaled_width = min(max_width, preview.width())
        scaled_height = int(scaled_width / ratio)
        print(f"Scaled dimensions: {scaled_width}x{scaled_height}")
        
        # Create container widget with minimal margins
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(2)  # Reduced from 5 to 2
        layout.setContentsMargins(2, 2, 2, 2)  # Reduced from 5,5,5,5 to 2,2,2,2
        
        # Optional: Show widget boundaries for debugging (uncomment to visualize clickable areas)
        # container.setStyleSheet("QWidget { border: 1px solid red; background-color: rgba(255, 0, 0, 0.1); }")
        
        # Create image container with exact sizing
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
        
        # Initialize updating flag before setting up any event handlers
        input_field._updating = False
        
        # Function to update container height when input field height changes (defined early)
        def updateContainerHeight():
            """Update container height based on input field height"""
            current_input_height = input_field.height()
            container_height = scaled_height + current_input_height + 6  # image + input + spacing + margins
            container.setMinimumHeight(container_height)
            container.setMaximumHeight(container_height)
        
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
                
            debug("tags", f"sync_tags | last_word: '{last_word}' | source_field: {getattr(source_field, 'file_path', None)}")
            current_widgets = list(self.image_flow_manager.image_widgets.values()) if hasattr(self, 'image_flow_manager') else []
            for widget in current_widgets:
                if (hasattr(widget, 'file_path') and 
                    widget.file_path in self.selected_images and 
                    widget.input_field != source_field):
                    
                    target = widget.input_field
                    target._updating = True
                    existing = target.toPlainText().strip()
                    debug("tags", f"sync_tags | target file_path: {widget.file_path} | existing: '{existing}'")
                    if existing:
                        if not existing.endswith(','):
                            existing += ','
                        existing += ' '
                        target.setText(f"{existing}{last_word}")
                        debug("tags", f"sync_tags | setText: '{existing}{last_word}'")
                    else:
                        target.setText(last_word)
                        debug("tags", f"sync_tags | setText: '{last_word}'")
                    target._updating = False
        
        def updateHeight():
            """Calculate and set the proper height for the text field to show all content"""
            content = input_field.toPlainText()
            if not content:
                input_field.setFixedHeight(28)
                updateContainerHeight()  # Update container height after input field height change
                return
                
            # Ensure document width matches the current text field width
            current_width = input_field.width()
            available_width = current_width - 10  # Account for margins
            
            # Get the document and ensure it has the correct width for wrapping
            document = input_field.document()
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
                font_metrics = input_field.fontMetrics()
                line_height = font_metrics.height()
                estimated_lines = max(1, doc_height // line_height) if line_height > 0 else 1
                
                margins = input_field.contentsMargins()
                padding = 8
                new_height = doc_height + margins.top() + margins.bottom() + padding
                
                # Set minimum height but no maximum - always show all content
                final_height = max(28, new_height)
                input_field.setFixedHeight(final_height)
                updateContainerHeight()  # Update container height after input field height change
                
                debug_layout(f"updateHeight | width: {current_width} | available_width: {available_width}")
                debug_layout(f"  content_chars: {len(content)} | doc_height: {doc_height} | estimated_lines: {estimated_lines} | final_height: {final_height}")
                debug_layout(f"  block_count: {block_count} | line_height: {line_height}")
            else:
                # Fallback if document is not available
                input_field.setFixedHeight(28)
                updateContainerHeight()
        
        def updateHeightImmediate():
            """Immediate height update without timer delay"""
            content = input_field.toPlainText()
            if not content:
                input_field.setFixedHeight(28)
                updateContainerHeight()  # Update container height after input field height change
                return
                
            # Ensure document width matches the current text field width
            current_width = input_field.width()
            available_width = current_width - 10  # Account for margins
            
            # Get the document and ensure it has the correct width for wrapping
            document = input_field.document()
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
                font_metrics = input_field.fontMetrics()
                line_height = font_metrics.height()
                estimated_lines = max(1, doc_height // line_height) if line_height > 0 else 1
                
                margins = input_field.contentsMargins()
                padding = 8
                new_height = doc_height + margins.top() + margins.bottom() + padding
                
                # Set minimum height but no maximum - always show all content
                final_height = max(28, new_height)
                input_field.setFixedHeight(final_height)
                updateContainerHeight()  # Update container height after input field height change
                
                debug_layout(f"updateHeightImmediate | width: {current_width} | available_width: {available_width}")
                debug_layout(f"  content_chars: {len(content)} | doc_height: {doc_height} | estimated_lines: {estimated_lines} | final_height: {final_height}")
                debug_layout(f"  block_count: {block_count} | line_height: {line_height}")
            else:
                # Fallback if document is not available
                input_field.setFixedHeight(28)
                updateContainerHeight()
        
        resize_timer = QTimer(input_field)
        resize_timer.setSingleShot(True)
        resize_timer.setInterval(100)
        
        def focusInEvent(e):
            QTextEdit.focusInEvent(input_field, e)
            # Store both the current text and cursor position when focus starts
            current_text = input_field.toPlainText()
            input_field._focus_start_text = current_text
            input_field._last_synced_text = current_text
            # Find where the "pre-existing" content ends (before any actively typed content)
            input_field._pre_existing_boundary = len(current_text)
            
            debug("ui_events", f"focusInEvent | focus_start_text: '{current_text}' | boundary: {input_field._pre_existing_boundary}")
            
        def focusOutEvent(e):
            QTextEdit.focusOutEvent(input_field, e)
            # Clear tracking on focus loss
            input_field._focus_start_text = None
            input_field._last_synced_text = None
            input_field._pre_existing_boundary = None
            
            content = input_field.toPlainText()
            if content:
                viewport = input_field.viewport()
                if viewport:
                    doc_width = viewport.width()
                    text_width = input_field.fontMetrics().horizontalAdvance(content)
                    if text_width <= (doc_width - 10):
                        input_field.setFixedHeight(28)
        
        def onTextChanged():
            if input_field._updating:
                return
                
            # Always update height when text changes
            updateHeightImmediate()
            current_text = input_field.toPlainText()
            
            debug("ui_events", f"onTextChanged | current_text: '{current_text}' | selected: {input_field.property('selected')}")
            
            # Only sync if this field is selected, part of multi-selection, and we have focus tracking
            if (input_field.property("selected") and 
                len(self.selected_images) > 1 and 
                hasattr(input_field, '_focus_start_text') and 
                input_field._focus_start_text is not None and
                hasattr(input_field, '_last_synced_text') and
                input_field._last_synced_text is not None):
                
                last_synced = input_field._last_synced_text
                
                # Calculate the change from last synced state
                if current_text != last_synced:
                    debug("ui_events", f"onTextChanged | Text change detected - last_synced: '{last_synced}' -> current: '{current_text}'")
                    
                    # Synchronize the entire content to all other selected fields
                    for widget in self.image_widgets:
                        if (hasattr(widget, 'file_path') and 
                            widget.file_path in self.selected_images and 
                            widget.input_field != input_field):
                            
                            target = widget.input_field
                            target._updating = True
                            
                            # Get the target's current content and its pre-existing boundary
                            target_current = target.toPlainText()
                            target_boundary = getattr(target, '_pre_existing_boundary', None)
                            
                            # If target hasn't been focused yet, use its entire current content as pre-existing
                            if target_boundary is None:
                                target_boundary = len(target_current)
                                target._pre_existing_boundary = target_boundary
                                target._focus_start_text = target_current
                                target._last_synced_text = target_current
                            
                            # Keep the target's pre-existing content, replace the actively typed part
                            target_pre_existing = target_current[:target_boundary] if target_boundary <= len(target_current) else target_current
                            
                            # Get the source's actively typed content (everything from the boundary onwards)
                            source_boundary = getattr(input_field, '_pre_existing_boundary', 0)
                            if source_boundary is None:
                                source_boundary = 0
                            source_typed_content = current_text[source_boundary:] if source_boundary <= len(current_text) else ""
                            
                            # Combine target's pre-existing + source's actively typed content
                            new_content = target_pre_existing + source_typed_content
                            target.setText(new_content)
                            
                            debug("ui_events", f"onTextChanged | sync to: {widget.file_path}")
                            debug("ui_events", f"  target_pre_existing: '{target_pre_existing}' (boundary: {target_boundary})")
                            debug("ui_events", f"  source_typed: '{source_typed_content}' (from boundary: {source_boundary})")
                            debug("ui_events", f"  result: '{new_content}'")
                            
                            # Update height for this target field
                            current_width = target.width()
                            target.document().setTextWidth(current_width - 10)  # Account for margins
                            target.document().adjustSize()
                            doc_height = int(target.document().size().height())
                            margins = target.contentsMargins()
                            padding = 8
                            new_height = doc_height + margins.top() + margins.bottom() + padding
                            final_height = max(28, new_height)
                            target.setFixedHeight(final_height)
                            
                            # Update target's sync tracking
                            target._last_synced_text = new_content
                                
                            target._updating = False
                    
                    # Update source's sync tracking
                    input_field._last_synced_text = current_text
        
        resize_timer.timeout.connect(updateHeight)
        input_field.textChanged.connect(onTextChanged)
        input_field.focusInEvent = focusInEvent
        input_field.focusOutEvent = focusOutEvent
        
        # Get year and keywords from stored metadata (already read during preview creation)
        year = None
        existing_keywords = []
        if hasattr(self, 'image_metadata') and file_path in self.image_metadata:
            metadata = self.image_metadata[file_path]
            year = metadata.get('year')
            existing_keywords = metadata.get('keywords', [])
        else:
            # Fallback: read metadata if not available (shouldn't normally happen)
            year, existing_keywords = self.get_image_metadata(file_path)
        
        # Build initial text: year first, then existing keywords
        initial_text_parts = []
        if year:
            initial_text_parts.append(str(year))
        
        # Add existing keywords (avoid duplicating year if it's already in keywords)
        for keyword in existing_keywords:
            if keyword and keyword.strip() and keyword.strip() != str(year):
                initial_text_parts.append(keyword.strip())
        
        if initial_text_parts:
            input_field.setText(', '.join(initial_text_parts) + ', ')
            # Force height calculation after setting initial text
            updateHeightImmediate()
        else:
            input_field.setPlaceholderText("Enter tags...")
        
        # Add widgets to layout
        layout.addWidget(image_container)
        layout.addWidget(input_field)
        
        # Set container width to fit contents exactly, but allow height to be dynamic
        container.adjustSize()
        container_width = scaled_width + 4  # image width + minimal margins (2px each side)
        container.setFixedWidth(container_width)  # Only fix width, let height be dynamic
        
        # Set initial container height
        updateContainerHeight()
        
        # Track if container was clicked for background deselection
        layout.clicked = False
        container.mousePressEvent = lambda e: None  # Will be updated later
        
        # Store references
        container.file_path = file_path
        container.image_label = image_label
        container.image_container = image_container  # Add reference to image_container
        container.input_field = input_field
        container.updateContainerHeight = updateContainerHeight  # Store reference to height update function
        
        def update_selection_state(selected):
            debug("ui_events", f"update_selection_state | selected: {selected}")
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
            
        def containerClickEvent(event):
            if not layout.clicked:
                # Deselect all if click was on the background
                for widget in self.image_widgets:
                    if hasattr(widget, 'file_path'):
                        if hasattr(widget, 'image_label') and hasattr(widget, 'input_field'):
                            widget.image_label.setProperty("selected", False)
                            widget.input_field.setProperty("selected", False)
                            widget.image_label.style().polish(widget.image_label)
                            widget.input_field.style().polish(widget.input_field)
                self.selected_images.clear()
                self.update_status_bar()
            layout.clicked = False
        
        image_container.mousePressEvent = imageContainerMousePress
        input_field.mousePressEvent = inputFieldMousePress
        container.mousePressEvent = containerClickEvent
        
        return container

    def eventFilter(self, obj, event):
        """Handle rubber band selection for multi-select"""
        if obj == self.picturesContainer:
            if event.type() == 2:  # QEvent.MouseButtonPress
                if event.button() == 1:  # Qt.LeftButton
                    # Check if click is on empty area (not on any widget)
                    clicked_widget = self.picturesContainer.childAt(event.pos())
                    if clicked_widget is None or clicked_widget == self.picturesContainer:
                        # Start rubber band selection
                        self.selection_start = event.pos()
                        self.is_selecting = True
                        
                        # Create rubber band if it doesn't exist
                        if self.rubber_band is None:
                            self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.picturesContainer)
                        
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
                if event.button() == 1 and self.is_selecting:  # Qt.LeftButton
                    # End rubber band selection
                    self.is_selecting = False
                    
                    if self.rubber_band:
                        # Get final selection rectangle
                        selection_rect = self.rubber_band.geometry()
                        self.rubber_band.hide()
                        
                        # Find widgets within selection rectangle
                        self.select_widgets_in_rect(selection_rect)
    def update_layout(self, value=None):
        """Update the layout using the new ImageFlowManager"""
        print("\nStarting update_layout with ImageFlowManager...")
        
        # Prevent recursion during layout updates
        if getattr(self, '_updating_layout', False):
            debug_layout("Skipping update_layout - already in progress")
            return
        
        if not self.image_files:
            print("No image files to display")
            return
        
        # Set recursion guard
        self._updating_layout = True
        
        try:
            # Get widget width from discrete slider steps
            slider_step = self.horizontalSlider.value()
            widget_width = self.size_steps[slider_step]
            debug_layout(f"Slider step {slider_step} -> Setting widget width to {widget_width}px")
            
            # PRESERVE CURRENT TEXT CONTENT before any layout changes
            current_text_content = {}
            if hasattr(self, 'image_flow_manager') and self.image_flow_manager.image_widgets:
                debug("layout", "Preserving current text content before layout update...")
                for file_path, widget in self.image_flow_manager.image_widgets.items():
                    if hasattr(widget, 'get_tags'):
                        current_content = widget.get_tags()
                        current_text_content[file_path] = ', '.join(current_content) if isinstance(current_content, list) else str(current_content)
                        debug("layout", f"Preserved text for {os.path.basename(file_path)}: '{current_text_content[file_path]}'")
            
            # Check if this is just a resize (same images, different width) or new image set
            current_loaded_files = set(self.image_flow_manager.image_widgets.keys()) if hasattr(self, 'image_flow_manager') else set()
            new_image_files = set(self.image_files)
            is_resize = bool(current_text_content) and current_loaded_files == new_image_files
        
            if is_resize:
                debug("layout", "This is a resize - updating widget widths without recreating widgets")
                # Just update widget widths for existing widgets
                self.image_flow_manager.set_widget_width(widget_width)
                
                # Restore preserved text content and trigger height adjustment
                for file_path, preserved_text in current_text_content.items():
                    if file_path in self.image_flow_manager.image_widgets:
                        widget = self.image_flow_manager.image_widgets[file_path]
                        widget.set_tags(preserved_text)
                        debug_layout(f"Restored text for {os.path.basename(file_path)}: '{preserved_text}'")
                
                # Explicitly trigger height adjustment after all content is restored
                # Use a timer to ensure programmatic flags have cleared
                def trigger_height_adjustment():
                    debug_layout("Triggering height adjustment after text restoration...")
                    for widget in self.image_flow_manager.image_widgets.values():
                        if hasattr(widget, '_adjust_text_height'):
                            # Temporarily bypass suppression for this specific height adjustment
                            original_flag = getattr(widget, '_programmatic_update_in_progress', False)
                            widget._programmatic_update_in_progress = False
                            widget._adjust_text_height()
                            widget._programmatic_update_in_progress = original_flag
                
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(200, trigger_height_adjustment)  # Short delay, bypass suppression manually
                
                # Update the layout
                self.image_flow_manager.update_layout()
                
            else:
                debug_startup("This is initial load - creating widgets from metadata")
                # Update the flow manager's widget width
                self.image_flow_manager.set_widget_width(widget_width)
                
                # Prepare image data for the flow manager
                image_data = []
                for file_path in self.image_files:
                    if file_path in self.image_previews:
                        # Get existing metadata/tags if available
                        metadata = self.image_metadata.get(file_path, {})
                        
                        # Build tags from year and keywords
                        year = metadata.get('year', '')
                        keywords = metadata.get('keywords', [])
                        
                        # Combine year and keywords into a single tag string with duplicate checking
                        all_tags = []
                        seen = set()
                        
                        # Add year first if it exists and isn't already in keywords
                        if year:
                            year_str = str(year)
                            all_tags.append(year_str)
                            seen.add(year_str)
                        
                        # Add keywords, checking for duplicates
                        if keywords:
                            if isinstance(keywords, list):
                                for keyword in keywords:
                                    keyword_str = str(keyword).strip()
                                    if keyword_str and keyword_str not in seen:
                                        all_tags.append(keyword_str)
                                        seen.add(keyword_str)
                            else:
                                keyword_str = str(keywords).strip()
                                if keyword_str and keyword_str not in seen:
                                    all_tags.append(keyword_str)
                                    seen.add(keyword_str)
                        
                        existing_tags = ', '.join(all_tags) if all_tags else ''
                        debug_tags(f"Tags for {os.path.basename(file_path)}: year='{year}', keywords={keywords}, final_tags='{existing_tags}'")
                        
                        # Get public_id directly from ExifTool metadata (no cached_metadata needed!)
                        from utilities.cloudinary_upload_handler import get_cloudinary_public_id_from_metadata
                        public_id = get_cloudinary_public_id_from_metadata(file_path)
                        
                        # Set original_tags as the current existing_tags (these are from metadata)
                        original_tags_list = all_tags.copy()
                        
                        # Get cloudinary_tags if we have a public_id and Cloudinary connection
                        cloudinary_tags_list = []
                        if public_id and hasattr(self, 'cloudinary_files_cache') and self.cloudinary_files_cache:
                            debug_tags(f"Checking for Cloudinary tags for {os.path.basename(file_path)} with public_id: {public_id}")
                            for cf in self.cloudinary_files_cache:
                                if cf.get('public_id') == public_id:
                                    # Convert Cloudinary tags to list format
                                    cf_tags = cf.get('tags', [])
                                    if isinstance(cf_tags, list):
                                        cloudinary_tags_list = [str(tag).strip() for tag in cf_tags if str(tag).strip()]
                                    debug_tags(f"Found Cloudinary tags for {os.path.basename(file_path)}: {cloudinary_tags_list}")
                                    break
                            if not cloudinary_tags_list:
                                debug_tags(f"No Cloudinary tags found for {os.path.basename(file_path)} with public_id: {public_id}")
                        else:
                            debug_tags(f"Skipping Cloudinary tags lookup for {os.path.basename(file_path)} - public_id: {public_id}, has_cache: {hasattr(self, 'cloudinary_files_cache')}")
                        
                        image_data.append({
                            'file_path': file_path,
                            'preview': self.image_previews[file_path],
                            'metadata': metadata,
                            'tags': existing_tags,
                            # Enhanced metadata for upload optimization
                            'public_id': public_id,
                            'original_tags': original_tags_list,
                            'cloudinary_tags': cloudinary_tags_list
                        })
                    else:
                        print(f"Warning: No preview available for {file_path}, skipping...")
                
                # Load images into the flow manager - much simpler than grid!
                self.image_flow_manager.load_images(image_data)
            
            # Update backward compatibility references
            self.image_widgets = list(self.image_flow_manager.image_widgets.values())
            
            # NOTE: No need to call update_cloudinary_status_for_loaded_images() anymore
            # since widgets are now created with correct Cloudinary sync status from the start
            
            operation_type = "resized" if is_resize else "loaded"
            debug_layout(f"Layout update completed - {len(self.image_widgets)} images {operation_type} with {widget_width}px width")
            debug_memory(f"ImageFlowManager now manages {len(self.image_widgets)} widgets")
        
        finally:
            # Clear recursion guard
            self._updating_layout = False
    
    def setup_sort_menu(self):
        """Setup the sort menu for the UI file sort button"""
        from PyQt5.QtWidgets import QMenu
        
        # Create sort menu for the existing UI button
        sort_menu = QMenu(self)
        
        # Add Cloudinary sort options
        cloudinary_action = sort_menu.addAction("📦 Non-Cloudinary First")
        cloudinary_action.triggered.connect(lambda: self.sort_images_by_cloudinary(reverse=False))
        
        cloudinary_reverse_action = sort_menu.addAction("☁️ Cloudinary First") 
        cloudinary_reverse_action.triggered.connect(lambda: self.sort_images_by_cloudinary(reverse=True))
        
        sort_menu.addSeparator()
        
        # Add other sort options
        filename_action = sort_menu.addAction("🔤 Filename A-Z")
        filename_action.triggered.connect(lambda: self.sort_images_by_filename(reverse=False))
        
        filename_reverse_action = sort_menu.addAction("🔤 Filename Z-A")
        filename_reverse_action.triggered.connect(lambda: self.sort_images_by_filename(reverse=True))
        
        sort_menu.addSeparator()
        
        date_action = sort_menu.addAction("📅 Newest First")
        date_action.triggered.connect(lambda: self.sort_images_by_date(reverse=False))
        
        date_reverse_action = sort_menu.addAction("📅 Oldest First")
        date_reverse_action.triggered.connect(lambda: self.sort_images_by_date(reverse=True))
        
        sort_menu.addSeparator()
        
        size_action = sort_menu.addAction("📏 Largest First")
        size_action.triggered.connect(lambda: self.sort_images_by_size(reverse=False))
        
        size_reverse_action = sort_menu.addAction("📏 Smallest First")
        size_reverse_action.triggered.connect(lambda: self.sort_images_by_size(reverse=True))
        
        # Set the menu to the existing UI button
        self.sortButton.setMenu(sort_menu)
        
        debug_layout("Sort menu setup complete for UI file button")
    
    def sort_images_by_cloudinary(self, reverse=False):
        """Sort images by Cloudinary sync status"""
        if hasattr(self, 'image_flow_manager') and self.image_flow_manager:
            self.image_flow_manager.sort_by_cloudinary_status(reverse=reverse)
            sort_info = self.image_flow_manager.get_current_sort_info()
            status_msg = f"Sorted by {sort_info['criteria_display']}"
            if reverse:
                status_msg += " (Cloudinary first)"
            else:
                status_msg += " (Non-Cloudinary first)"
            self.update_progress_label(status_msg)
            debug_layout(f"Images sorted by Cloudinary status (reverse={reverse})")
    
    def sort_images_by_filename(self, reverse=False):
        """Sort images alphabetically by filename"""
        if hasattr(self, 'image_flow_manager') and self.image_flow_manager:
            self.image_flow_manager.sort_by_filename(reverse=reverse)
            direction = "Z-A" if reverse else "A-Z"
            self.update_progress_label(f"Sorted by filename ({direction})")
            debug_layout(f"Images sorted by filename (reverse={reverse})")
    
    def sort_images_by_date(self, reverse=False):
        """Sort images by modification date"""
        if hasattr(self, 'image_flow_manager') and self.image_flow_manager:
            self.image_flow_manager.sort_by_date_modified(reverse=reverse)
            direction = "oldest first" if reverse else "newest first"
            self.update_progress_label(f"Sorted by date ({direction})")
            debug_layout(f"Images sorted by date (reverse={reverse})")
    
    def sort_images_by_size(self, reverse=False):
        """Sort images by file size"""
        if hasattr(self, 'image_flow_manager') and self.image_flow_manager:
            self.image_flow_manager.sort_by_file_size(reverse=reverse)
            direction = "smallest first" if reverse else "largest first"
            self.update_progress_label(f"Sorted by size ({direction})")
            debug_layout(f"Images sorted by size (reverse={reverse})")
    
    def open_files(self):
        print("Opening file dialog...")
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.xpm *.jpg *.jpeg *.gif *.tiff *.tif *.webp)"
        )
        
        print(f"Selected files: {files}")
        
        if files:
            # Clear previous metadata errors and data
            self.metadata_errors.clear()
            self.unsupported_files.clear()
            
            # Initialize empty lists - we'll only add files that successfully create previews
            self.image_files = []
            self.image_previews.clear()
            self.image_metadata.clear()  # Clear metadata storage
            self.selected_images.clear()
            for widget in self.image_widgets:
                widget.setParent(None)
            self.image_widgets.clear()
            
            # Start complete integrated processing (new approach)
            # For files selection, non_image_files is 0 since user selected specific files
            self.start_integrated_processing(files, "files", 0)

    def open_folder(self):
        """Open a folder dialog and import all image files from the selected folder"""
        print("Opening folder dialog...")
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        print(f"Selected folder: {folder_path}")
        
        if folder_path:
            # Define supported image extensions (excluding XMP which are metadata sidecar files)
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.tiff', '.tif', '.webp'}
            # Define unsupported image formats that we recognize but can't process
            unsupported_image_extensions = {'.bmp', '.psd'}
            
            # Find all image files in the folder and count different file types
            image_files = []
            non_image_files = 0
            unsupported_image_files = []
            total_files = 0
            
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    total_files += 1
                    _, ext = os.path.splitext(filename.lower())
                    if ext in image_extensions:
                        image_files.append(file_path)
                    elif ext in unsupported_image_extensions:
                        unsupported_image_files.append(file_path)
                        # Add to unsupported list with appropriate message
                        format_name = "BMP" if ext == '.bmp' else "PSD"
                        self.unsupported_files.append((file_path, f"{format_name} format not currently supported"))
                    else:
                        non_image_files += 1
            
            print(f"Found {len(image_files)} image files in folder")
            if len(unsupported_image_files) > 0:
                print(f"Found {len(unsupported_image_files)} unsupported image files (BMP/PSD)")
            if non_image_files > 0:
                print(f"Skipping {non_image_files} non-image files")
            
            if image_files:
                # Clear previous metadata errors and data (but keep unsupported_files for reporting)
                self.metadata_errors.clear()
                # Don't clear self.unsupported_files here - we need it for messaging
                
                # Clear existing data - initialize empty lists
                self.image_files = []
                self.image_previews.clear()
                self.image_metadata.clear()  # Clear metadata storage
                self.selected_images.clear()
                for widget in self.image_widgets:
                    widget.setParent(None)
                self.image_widgets.clear()
                
                # Start complete integrated processing (new approach) with unsupported file info
                self.start_integrated_processing(image_files, "folder", non_image_files, len(unsupported_image_files))
            else:
                print("No image files found in the selected folder")

    def _convert_bmp_files_to_jpeg(self, image_files):
        """
        Convert BMP files to JPEG format and update file paths.
        Returns: (converted_files_list, conversion_count)
        """
        converted_files = []
        conversion_count = 0
        
        for file_path in image_files:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.bmp':
                try:
                    # Create new JPEG filename
                    jpeg_path = file_path.rsplit('.', 1)[0] + '.jpg'
                    
                    # Convert BMP to JPEG
                    with Image.open(file_path) as img:
                        # Convert to RGB if necessary (BMP might be in different modes)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Save as JPEG with high quality
                        img.save(jpeg_path, 'JPEG', quality=95, optimize=True)
                    
                    # Add converted file to list
                    converted_files.append(jpeg_path)
                    conversion_count += 1
                    
                    debug_startup(f"Converted BMP to JPEG: {os.path.basename(file_path)} -> {os.path.basename(jpeg_path)}")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to convert BMP file {file_path}: {e}")
                    # Keep original file if conversion fails
                    converted_files.append(file_path)
            else:
                # Non-BMP file, keep as is
                converted_files.append(file_path)
        
        if conversion_count > 0:
            debug_startup(f"BMP conversion complete: {conversion_count} files converted to JPEG")
        
        return converted_files, conversion_count

    def start_integrated_processing(self, image_files, source, non_image_files=0, unsupported_image_files=0):
        """Start integrated processing combining Cloudinary assessment with image loading"""
        debug_startup(f"Starting integrated processing for {len(image_files)} valid images (source: {source})")
        
        # Create detailed progress message
        progress_message = f"Processing {len(image_files)} images"
        if unsupported_image_files > 0:
            progress_message += f"\nSkipping {unsupported_image_files} unsupported image files (BMP/PSD)"
        if non_image_files > 0:
            progress_message += f"\nSkipping {non_image_files} non-image files"
        
        # Determine if Cloudinary processing should be enabled
        debug_cloudinary("Cloudinary connection check:")
        debug_cloudinary(f"  - self.cloudinary_connected: {getattr(self, 'cloudinary_connected', 'NOT SET')}")
        debug_cloudinary(f"  - has cloudinary_updater attr: {hasattr(self, 'cloudinary_updater')}")
        debug_cloudinary(f"  - cloudinary_updater value: {getattr(self, 'cloudinary_updater', 'NOT SET')}")
        
        cloudinary_enabled = self.cloudinary_connected and hasattr(self, 'cloudinary_updater') and self.cloudinary_updater
        
        if cloudinary_enabled:
            debug_cloudinary("✅ Cloudinary enabled - will process with cloud operations")
        else:
            debug_cloudinary("❌ Cloudinary disabled - processing locally only")
        
        # CRITICAL FIX: Reset assessment and upload handler lists to prevent accumulation across sessions
        if hasattr(self, 'image_assessment') and self.image_assessment:
            debug_startup("Resetting ImageAssessment lists for new processing session")
            self.image_assessment.reset_assessment_lists()
        
        if hasattr(self, 'upload_handler') and self.upload_handler:
            debug_startup("Resetting CloudinaryUploadHandler for new processing session")
            self.upload_handler.reset_upload_handler()
        
        # Show progress with detailed message
        self.show_progress(len(image_files), progress_message)
        
        # Process each image
        processed_data = []
        cloudinary_sync_status = {}  # Store sync status from assessment phase
        for i, file_path in enumerate(image_files):
            try:
                
                debug_file_ops(f"Loading image {i+1}/{len(image_files)}: {os.path.basename(file_path)}")
                
                # Update progress
                self.update_progress(i + 1)
                QApplication.processEvents()
                
                # Cloudinary assessment if enabled  
                if cloudinary_enabled and self.cloudinary_updater:
                    try:
                        debug_assessment(f"[LIGHTWEIGHT ASSESSMENT] Checking sync status for {os.path.basename(file_path)} - File {i+1}/{len(image_files)}")
                        
                        # Use lightweight assessment that only checks public_id without resizing
                        is_synced = self.image_assessment.check_cloudinary_sync_status_lightweight(file_path)
                        
                        if is_synced:
                            debug_cloudinary(f"[LIGHTWEIGHT ASSESSMENT] {os.path.basename(file_path)} - Already synced with Cloudinary (SKIPPED)")
                            debug_assessment(f"[LIGHTWEIGHT ASSESSMENT] {os.path.basename(file_path)} - Status: ALREADY_SYNCED")
                            cloudinary_sync_status[file_path] = True  # Store sync status
                        else:
                            debug_assessment(f"[LIGHTWEIGHT ASSESSMENT] {os.path.basename(file_path)} - Not synced, will be processed for upload later")
                            debug_assessment(f"[LIGHTWEIGHT ASSESSMENT] {os.path.basename(file_path)} - Status: NEEDS_PROCESSING")
                            cloudinary_sync_status[file_path] = False  # Store sync status
                            
                    except Exception as e:
                        debug_errors(f"[LIGHTWEIGHT ASSESSMENT] Cloudinary assessment failed for {os.path.basename(file_path)}: {e}")
                        cloudinary_sync_status[file_path] = False  # Default to not synced on exception
                else:
                    # Cloudinary not enabled - default to not synced
                    cloudinary_sync_status[file_path] = False
                
                # Create preview and extract metadata
                try:
                    preview = self.create_preview(file_path)
                    if preview:
                        year, local_keywords = self.get_image_metadata(file_path)
                        
                        # Store ACTUAL local keywords as original for proper change detection
                        self.original_keywords[file_path] = local_keywords.copy()
                        
                        # Start with local keywords
                        keywords = local_keywords.copy()
                        
                        # CLOUDINARY TAG IMPORT: Replace local tags with Cloudinary tags if public_id matches
                        if cloudinary_enabled and self.cloudinary_updater:
                            cloudinary_keywords = self._import_cloudinary_tags_for_file(file_path, local_keywords)
                            if cloudinary_keywords is not None:
                                keywords = cloudinary_keywords
                                debug_cloudinary(f"Replaced local tags with Cloudinary tags for {os.path.basename(file_path)}")
                                # Mark this file as having imported changes that need saving
                                if not hasattr(self, 'cloudinary_imported_files'):
                                    self.cloudinary_imported_files = set()
                                self.cloudinary_imported_files.add(file_path)
                                debug_cloudinary(f"Marked {os.path.basename(file_path)} as having imported Cloudinary changes")
                        
                        # Prepare image data
                        image_data = {
                            'file_path': file_path,
                            'preview': preview,
                            'year': year,
                            'keywords': keywords,
                            'cloudinary_synced': cloudinary_sync_status.get(file_path, False)  # Include sync status
                        }
                        processed_data.append(image_data)
                        
                        debug_file_ops(f"{os.path.basename(file_path)} - Complete processing finished")
                    
                except Exception as e:
                    print(f"[WARNING] Metadata extraction failed for {os.path.basename(file_path)}: {e}")
                    # Still add the image even if metadata fails
                    try:
                        preview = self.create_preview(file_path)
                        if preview:
                            image_data = {
                                'file_path': file_path,
                                'preview': preview,
                                'year': None,
                                'keywords': [],
                                'cloudinary_synced': cloudinary_sync_status.get(file_path, False)  # Include sync status
                            }
                            processed_data.append(image_data)
                    except Exception as preview_e:
                        print(f"[ERROR] Failed to process {os.path.basename(file_path)}: {preview_e}")
                        
            except Exception as e:
                print(f"[ERROR] Complete failure processing {os.path.basename(file_path)}: {e}")
        
        self.hide_progress()
        
        debug_startup(f"Integrated processing complete: {len(processed_data)}/{len(image_files)} images processed")
        
        # DEBUG: Show sync status summary
        if cloudinary_sync_status:
            synced_files = [f for f, status in cloudinary_sync_status.items() if status]
            unsynced_files = [f for f, status in cloudinary_sync_status.items() if not status]
            debug_cloudinary(f"SYNC STATUS SUMMARY: {len(synced_files)} synced, {len(unsynced_files)} not synced")
            
            if synced_files:
                debug_cloudinary("Files marked as SYNCED:")
                for file_path in synced_files:
                    debug_cloudinary(f"  ✅ {os.path.basename(file_path)}")
            
            if unsynced_files:
                debug_cloudinary("Files marked as NOT SYNCED:")
                for file_path in unsynced_files:
                    debug_cloudinary(f"  ❌ {os.path.basename(file_path)}")
        else:
            debug_cloudinary("No Cloudinary sync status data available")
        
        # LIGHTWEIGHT ASSESSMENT DEBUG: Show sync status summary if Cloudinary was enabled
        if cloudinary_enabled and self.cloudinary_updater:
            debug_assessment("=== LIGHTWEIGHT ASSESSMENT SUMMARY ===")
            debug_assessment(f"Total files processed: {len(image_files)}")
            
            if cloudinary_sync_status:
                synced_count = len([f for f, status in cloudinary_sync_status.items() if status])
                unsynced_count = len([f for f, status in cloudinary_sync_status.items() if not status])
                debug_assessment(f"Files already synced (skipped during upload): {synced_count}")
                debug_assessment(f"Files that will need upload processing: {unsynced_count}")
            else:
                debug_assessment("No sync status data available")
            
            debug_assessment("Note: Resizing and database operations deferred to upload phase for faster loading")
            debug_assessment("=== END LIGHTWEIGHT ASSESSMENT SUMMARY ===")
        else:
            debug_assessment("Cloudinary disabled - all files will be processed locally only")
        
        # Store processed images
        self.image_files = [data['file_path'] for data in processed_data]
        self.image_previews = {data['file_path']: data['preview'] for data in processed_data}
        self.image_metadata = {data['file_path']: {'year': data['year'], 'keywords': data['keywords'], 'cloudinary_synced': data.get('cloudinary_synced', False)} 
                             for data in processed_data}
        
        # Update layout with processed data
        if processed_data:
            self.update_layout()
            # NOTE: No need to call update_cloudinary_status_for_loaded_images() anymore
            # since widgets are now created with correct Cloudinary sync status from the start
            
            # Update status bar after a brief delay to ensure widgets are fully created
            QTimer.singleShot(100, self.update_status_bar)
            
            # Show unsupported files dialog if any were found
            if self.unsupported_files:
                QTimer.singleShot(500, self.show_unsupported_files)  # Small delay after UI updates
            
            # Auto-hide progress after 2 seconds
            QTimer.singleShot(2000, self.hide_progress)
        else:
            print("No images were successfully processed")
            self.statusBar().showMessage("No images loaded")

    def show_tag_manager(self):
        """Create and show the tag manager dialog"""
        if self.tag_manager is None:
            self.tag_manager = TagManager(self)
            # Connect the tag clicked signal to our handler
            self.tag_manager.tagClicked.connect(self.on_tag_clicked)
            # Connect the business clicked signal to our handler
            self.tag_manager.businessClicked.connect(self.on_business_clicked)
            # Connect the building and street clicked signals to our handlers
            self.tag_manager.buildingClicked.connect(self.on_building_clicked)
            self.tag_manager.streetClicked.connect(self.on_street_clicked)
        if self.tag_manager.isHidden():
            self.tag_manager.show()
            self.tag_manager.raise_()
    
    def initialize_cloudinary(self):
        """Initialize Cloudinary integration with proper error handling"""
        debug_startup("Initializing Cloudinary integration...")
        
        # Initialize as disconnected
        self.cloudinary_connected = False
        self.cloudinary_updater = None
        self.cloudinary_files_cache = []  # Global cache for Cloudinary files
        
        try:
            # Get Cloudinary settings from our unified settings system
            settings = SettingsDialog.get_saved_settings()
            cloudinary_settings = SettingsDialog.get_cloudinary_settings()
            
            debug_cloudinary(f"Retrieved settings: {cloudinary_settings}")
            
            # Check if Cloudinary is configured
            if not SettingsDialog.is_cloudinary_configured():
                debug_cloudinary("Cloudinary not configured - skipping CloudinaryUpdater setup")
                debug_cloudinary("Configure Cloudinary settings in File > Settings to enable cloud features")
                self._update_cloudinary_ui_status(False, "Not configured")
                return
            
            # Create CloudinaryUpdater instance
            self.cloudinary_updater = CloudinaryUpdater()
            debug_cloudinary("CloudinaryUpdater instance created successfully")
            
            debug_cloudinary("Cloudinary settings found - configuring CloudinaryUpdater...")
            
            # Prepare config in the format expected by CloudinaryUpdater
            cloudinary_config = [
                cloudinary_settings.get('log_folder', ''),
                cloudinary_settings.get('cloud_name', ''),
                cloudinary_settings.get('api_key', ''),
                cloudinary_settings.get('api_secret', ''),
                cloudinary_settings.get('max_size', '10')  # Default 10MB
            ]
            
            debug_cloudinary(f"Cloudinary config prepared: {[cloudinary_config[0], cloudinary_config[1], '*****', '*****', cloudinary_config[4]]}")
            
            # Configure the CloudinaryUpdater
            self.cloudinary_updater.setCloudinaryUpdaterConfig(cloudinary_config)
            debug_cloudinary("CloudinaryUpdater configured successfully")
            
            # Test initial connection and retrieve account info
            debug_cloudinary("Testing Cloudinary connection and retrieving account info...")
            try:
                # Connect signals to capture the response
                self.cloudinary_updater.beginning_signal.connect(self.on_cloudinary_status_received)
                self.cloudinary_updater.update_ui_signal.connect(self.on_cloudinary_ui_update)
                
                # Request account status
                self.cloudinary_updater.cloud_status()
                debug_cloudinary("Cloudinary status request sent")
                
                # For now, assume connection will succeed (will be updated by signal handlers)
                # The actual status will be set when we receive the response
                
            except Exception as e:
                debug_errors(f"Error testing Cloudinary connection: {str(e)}")
                self.cloudinary_connected = False
                self._update_cloudinary_ui_status(False, "Connection failed")
                
        except Exception as e:
            print(f"[ERROR] Failed to initialize Cloudinary: {str(e)}")
            import traceback
            traceback.print_exc()
            self.cloudinary_updater = None
            self.cloudinary_connected = False
            self._update_cloudinary_ui_status(False, "Initialization failed")
    
    def update_cloudinary_status_for_loaded_images(self):
        """Check and update Cloudinary sync status for all currently loaded images"""
        if not hasattr(self.image_flow_manager, 'image_widgets') or not self.image_flow_manager.image_widgets:
            debug_cloudinary(f"No images loaded - skipping Cloudinary status check")
            return
            
        debug_cloudinary(f"Updating Cloudinary sync status for {len(self.image_flow_manager.image_widgets)} loaded images using assessment results...")
        
        try:
            synced_count = 0
            for file_path, widget in self.image_flow_manager.image_widgets.items():
                try:
                    # Use the sync status from our assessment phase (stored in metadata)
                    is_synced = False
                    if hasattr(self, 'image_metadata') and file_path in self.image_metadata:
                        metadata = self.image_metadata[file_path]
                        is_synced = metadata.get('cloudinary_synced', False)
                        debug_cloudinary(f"File {os.path.basename(file_path)}: sync status from assessment = {is_synced}")
                    else:
                        debug_cloudinary(f"File {os.path.basename(file_path)}: no assessment data, defaulting to not synced")
                    
                    # Update widget Cloudinary status
                    if hasattr(widget, 'set_cloudinary_status'):
                        widget.set_cloudinary_status(is_synced)
                        debug_cloudinary(f"Set widget sync status for {os.path.basename(file_path)}: {is_synced}")
                    else:
                        debug_cloudinary(f"Widget for {os.path.basename(file_path)} has no set_cloudinary_status method")
                    
                    if is_synced:
                        synced_count += 1
                        
                except Exception as e:
                    debug_cloudinary(f"Error updating Cloudinary status for {os.path.basename(file_path)}: {e}")
                    # Set as not synced if there's an error
                    if hasattr(widget, 'set_cloudinary_status'):
                        widget.set_cloudinary_status(False)
            
            debug_cloudinary(f"Cloudinary status update complete: {synced_count}/{len(self.image_flow_manager.image_widgets)} images marked as synced")
            
            # Force immediate visual update of all widgets
            for widget in self.image_flow_manager.image_widgets.values():
                if hasattr(widget, 'update'):
                    widget.update()
            
            # Process any pending paint events to ensure immediate visual refresh
            QApplication.processEvents()
            
        except Exception as e:
            debug_cloudinary(f"Error updating Cloudinary status for loaded images: {e}")
    
    def setup_image_assessment_connections(self):
        """Setup connections for the image assessment system"""
        if self.image_assessment:
            # Connect signals for progress updates during assessment
            self.image_assessment.assessment_progress.connect(self.update_progress)
            self.image_assessment.assessment_status.connect(self.update_progress_label)
            # Note: Removed connections to unused methods (on_image_assessed, on_assessment_complete)
            debug_assessment(f"Image assessment system connected")
    
    def setup_upload_handler_connections(self):
        """Setup connections for the upload handler system"""
        if self.upload_handler:
            # Connect upload progress signals
            self.upload_handler.upload_progress_signal.connect(self.update_upload_progress)
            self.upload_handler.upload_status_signal.connect(self.update_progress_label)
            self.upload_handler.upload_complete_signal.connect(self.on_upload_complete)
            self.upload_handler.upload_preview_signal.connect(self.on_upload_preview)
            debug_upload("Upload handler system connected")
    
    def run_upload_assessment(self):
        """
        Run SIMPLIFIED widget-based assessment for upload phase.
        Uses widget methods to determine upload needs - NO ExifTool calls!
        """
        debug_upload("Running SIMPLIFIED widget-based assessment for upload phase...")
        
        if not hasattr(self, 'image_flow_manager') or not self.image_flow_manager.image_widgets:
            debug_upload("ERROR: No image widgets available for assessment")
            return False
        
        try:
            # Initialize assessment results using widget data
            files_for_tag_update_only = []
            files_not_on_cloudinary = []
            already_synced_count = 0
            
            debug_upload(f"Analyzing {len(self.image_flow_manager.image_widgets)} widgets for upload...")
            
            # Analyze each widget to determine upload needs
            for file_path, widget in self.image_flow_manager.image_widgets.items():
                # Get current UI tags
                ui_tags = widget.get_tags()
                ui_tags_list = [tag.strip() for tag in ui_tags] if isinstance(ui_tags, list) else [tag.strip() for tag in str(ui_tags).split(',') if tag.strip()]
                
                debug_upload(f"Widget analysis for {os.path.basename(file_path)}: UI tags = {ui_tags_list}")
                
                # Check if image has a public_id (is on Cloudinary)
                public_id = widget.get_cloudinary_public_id()
                
                if public_id:
                    # Image is on Cloudinary - check if tags need updating
                    debug_upload(f"  Has public_id: {public_id}")
                    
                    if widget.ui_tags_match_cloudinary():
                        # Tags match - no action needed
                        debug_upload(f"  Tags match Cloudinary - no action needed")
                        already_synced_count += 1
                    else:
                        # Tags don't match - needs tag update only
                        debug_upload(f"  Tags differ from Cloudinary - needs tag update")
                        debug_upload(f"    UI tags: {ui_tags_list}")
                        debug_upload(f"    Cloudinary tags: {widget.get_cloudinary_tags()}")
                        
                        files_for_tag_update_only.append({
                            'file_path': file_path,
                            'public_id': public_id,
                            'ui_tags': ui_tags_list,
                            'current_cloudinary_tags': widget.get_cloudinary_tags()
                        })
                else:
                    # Image is NOT on Cloudinary - needs full upload
                    debug_upload(f"  No public_id - needs full upload")
                    
                    files_not_on_cloudinary.append({
                        'file_path': file_path,
                        'ui_tags': ui_tags_list,
                        'original_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    })
            
            # Store results in image_assessment for compatibility with upload handler
            self.image_assessment.files_for_tag_update_only = files_for_tag_update_only
            self.image_assessment.files_not_on_cloudinary = files_not_on_cloudinary
            self.image_assessment.already_synced_count = already_synced_count
            
            # Log summary
            debug_upload(f"SIMPLIFIED widget-based assessment complete:")
            debug_upload(f"  Files needing tag updates only: {len(files_for_tag_update_only)}")
            debug_upload(f"  Files not on Cloudinary (full upload): {len(files_not_on_cloudinary)}")
            debug_upload(f"  Files already synced (no action): {already_synced_count}")
            
            return True
                
        except Exception as e:
            debug_upload(f"ERROR: Exception during SIMPLIFIED widget-based assessment: {e}")
            return False
    
    def start_cloudinary_upload(self):
        """Start the Cloudinary upload phase using the upload handler"""
        debug_upload("Starting Cloudinary upload phase from UI action")
        
        if not self.upload_handler:
            debug_upload("ERROR: Upload handler not initialized")
            return
        
        # Run on-demand assessment for upload phase
        debug_upload("Running on-demand assessment for upload...")
        if not self.run_upload_assessment():
            debug_upload("ERROR: Upload assessment failed")
            QMessageBox.warning(self, "Upload Error", 
                              "Assessment failed. Please check that images are loaded and Cloudinary is configured.")
            return
        
        # Verify NEW assessment results are now available
        if not hasattr(self.image_assessment, 'files_for_tag_update_only'):
            debug_upload("ERROR: NEW assessment structure not available")
            QMessageBox.warning(self, "Upload Error", 
                              "Assessment failed. Please check that images are loaded and Cloudinary is configured.")
            return
            
        # Get the latest assessment results
        files_for_tag_update = getattr(self.image_assessment, 'files_for_tag_update_only', [])
        files_not_on_cloudinary = getattr(self.image_assessment, 'files_not_on_cloudinary', [])
        already_synced_count = getattr(self.image_assessment, 'already_synced_count', 0)
        
        # Check if there's anything to do
        total_work = len(files_for_tag_update) + len(files_not_on_cloudinary)
        if total_work == 0:
            debug_upload("No files need uploading or updating after NEW assessment")
            message = f"All {already_synced_count} images are already perfectly synced with Cloudinary. No upload needed."
            QMessageBox.information(self, "Upload Info", message)
            return
        
        # Show progress bar for upload phase
        upload_message = f"Uploading to Cloudinary...\n{total_work} files to process"
        self.show_progress(total_work, upload_message)
        
        # ENHANCED DEBUG: Show NEW assessment data
        debug_upload(f"NEW assessment data for upload handler:")
        debug_upload(f"  - Files for tag update only: {len(files_for_tag_update)} files")
        debug_upload(f"  - Files not on Cloudinary (resize+upload): {len(files_not_on_cloudinary)} files")
        debug_upload(f"  - Files already synced (no action): {already_synced_count} files")
        
        if files_for_tag_update:
            debug_upload("Files needing tag updates only:")
            for i, file_data in enumerate(files_for_tag_update, 1):
                file_path = file_data.get('file_path', 'Unknown')
                ui_tags = file_data.get('ui_tags', [])
                public_id = file_data.get('public_id', 'Unknown')
                debug_upload(f"  {i}. {os.path.basename(file_path)} - Tags: {ui_tags} - ID: {public_id}")
                
        if files_not_on_cloudinary:
            debug_upload("Files not on Cloudinary needing full upload:")
            for i, file_data in enumerate(files_not_on_cloudinary, 1):
                file_path = file_data.get('file_path', 'Unknown')
                ui_tags = file_data.get('ui_tags', [])
                debug_upload(f"  {i}. {os.path.basename(file_path)} - Tags: {ui_tags}")
        
        # Extract source folder name from original image files
        source_folder_name = self._extract_original_folder_name()
        
        # Prepare NEW assessment data in the format expected by upload handler
        new_assessment_data = {
            'files_for_tag_update_only': files_for_tag_update,
            'files_not_on_cloudinary': files_not_on_cloudinary,
            'already_synced_count': already_synced_count
        }
        
        # Set NEW assessment data and source folder name 
        self.upload_handler.set_assessment_data(new_assessment_data)
        self.upload_handler.set_source_folder_name(source_folder_name)
        
        # Start the upload process
        self.upload_handler.start_upload_phase()
    
    def get_tag_widgets_for_upload(self):
        """Collect tag input widgets from the UI for metadata extraction"""
        tag_widgets = []
        
        # Get widgets from the image flow manager
        if hasattr(self, 'image_flow_manager') and self.image_flow_manager.image_widgets:
            for widget in self.image_flow_manager.image_widgets.values():
                # Get text input field from each image widget
                text_field = self.get_widget_text_field(widget)
                if text_field:
                    tag_widgets.append(text_field)
        
        debug_upload(f"Collected {len(tag_widgets)} tag widgets for upload")
        return tag_widgets
    
    def _extract_original_folder_name(self):
        """Extract folder name from original image file paths (not temp paths)"""
        if not hasattr(self, 'image_files') or not self.image_files:
            debug_upload("No original image files available to extract folder name")
            return None
            
        try:
            # Get first original file path
            first_original_file = self.image_files[0]
            from pathlib import Path
            file_path_obj = Path(first_original_file)
            folder_name = file_path_obj.parent.name
            
            debug_upload(f"Extracted original folder name: '{folder_name}' from {first_original_file}")
            return folder_name
            
        except Exception as e:
            debug_upload(f"Error extracting original folder name: {e}")
            return None
    
    def on_upload_complete(self, upload_data):
        """Handle upload completion with enhanced metadata failure reporting"""
        # Hide the progress bar first
        self.hide_progress()
        
        # Handle both old format (2 values) and new format (3 values)
        if len(upload_data) == 2:
            uploaded_count, error_count = upload_data
            metadata_failures = 0
        else:
            uploaded_count, error_count, metadata_failures = upload_data
        
        debug_upload(f"Upload complete: {uploaded_count} uploaded, {error_count} errors, {metadata_failures} metadata failures")
        
        # Refresh Cloudinary status to update the asset count in the credits bar
        if uploaded_count > 0 and hasattr(self, 'cloudinary_updater') and self.cloudinary_updater:
            print(f"[UPLOAD REFRESH] Refreshing Cloudinary status after {uploaded_count} successful uploads...")
            try:
                self.cloudinary_updater.cloud_status()
                print(f"[UPLOAD REFRESH] Cloudinary status refresh triggered successfully")
            except Exception as e:
                print(f"[UPLOAD REFRESH] Warning: Failed to refresh Cloudinary status after upload: {e}")
        else:
            print(f"[UPLOAD REFRESH] Skipping refresh - uploaded_count: {uploaded_count}, has_cloudinary_updater: {hasattr(self, 'cloudinary_updater')}")
        
        # Check for metadata write failures and show detailed warning if needed
        metadata_failure_summary = None
        if hasattr(self, 'upload_handler') and self.upload_handler:
            metadata_failure_summary = self.upload_handler.get_metadata_failure_summary()
        
        # Show completion message with metadata warnings if applicable
        if error_count == 0 and metadata_failures == 0:
            QMessageBox.information(self, "Upload Complete", 
                                  f"Successfully uploaded {uploaded_count} files to Cloudinary!\n"
                                  f"All metadata (tags and public IDs) saved successfully.")
        elif error_count == 0 and metadata_failures > 0:
            # Successful upload but metadata issues
            message = f"Successfully uploaded {uploaded_count} files to Cloudinary!\n\n"
            message += f"⚠️ Warning: {metadata_failures} files had metadata writing issues.\n"
            message += "Files are uploaded but may not have persistent metadata.\n\n"
            
            if metadata_failure_summary:
                message += f"Reason: {metadata_failure_summary['reasons'][0] if metadata_failure_summary['reasons'] else 'Unknown'}\n\n"
                message += metadata_failure_summary['recommendation']
            
            QMessageBox.warning(self, "Upload Complete with Metadata Warnings", message)
        else:
            # Upload errors (possibly with metadata issues too)
            message = f"Uploaded {uploaded_count} files with {error_count} upload errors."
            if metadata_failures > 0:
                message += f"\nAdditionally, {metadata_failures} files had metadata writing issues."
            message += "\nCheck logs for details."
            
            QMessageBox.warning(self, "Upload Complete with Errors", message)
    
    def on_upload_preview(self, file_path):
        """Handle upload preview updates"""
        debug_upload(f"Currently uploading: {file_path}")
        # Update UI to show which file is currently being uploaded
        # This could update a preview widget or status bar
    
    def update_progress_label(self, message):
        """Update the progress label with a custom message"""
        if hasattr(self, 'progress_label') and self.progress_label:
            self.progress_label.setText(message)
    
    def on_cloudinary_status_received(self, data):
        """Handle Cloudinary status data received from cloud_status"""
        print(f"[UPLOAD REFRESH] on_cloudinary_status_received called with data length: {len(data) if data else 0}")
        debug_cloudinary(f" Cloudinary status received: {data}")
        if data and len(data) > 0:
            if data[0] == True:  # Status retrieval successful
                debug_cloudinary(f"✅ Cloudinary connection successful!")
                debug_startup("Showing Cloudinary UI after successful connection")
                
                # IMPORTANT: Set the connection flag to True
                self.cloudinary_connected = True
                self._update_cloudinary_ui_status(True, "Connected")
                
                # Retrieve Cloudinary files list once at initialization
                self._retrieve_cloudinary_files_cache()
                
                if len(data) > 10:
                    storage_credits = data[8] if len(data) > 8 else "Unknown"
                    transformations = data[9] if len(data) > 9 else "Unknown"
                    bandwidth = data[10] if len(data) > 10 else "Unknown"
                    debug_cloudinary(f"📊 Account Usage - Storage: {storage_credits}, Transformations: {transformations}, Bandwidth: {bandwidth}")
                    
                    # Use the correct percentage values from the data - FIXED: Correct mapping
                    storage_percent = data[6] if len(data) > 6 else 0          # Storage % is at index 6
                    transformations_percent = data[5] if len(data) > 5 else 0  # Transformations % is at index 5
                    bandwidth_percent = data[7] if len(data) > 7 else 0        # Bandwidth % is at index 7
                    
                    # Update the CloudinaryCreditsBar if it exists
                    resources_count = data[4] if len(data) > 4 else 0  # Get number of files from index 4
                    print(f"[UPLOAD REFRESH] Calling update_credits_bar with resources_count: {resources_count}")
                    self.update_credits_bar(storage_percent, transformations_percent, bandwidth_percent, resources_count)
            else:
                debug_cloudinary(f"❌ Cloudinary connection failed: {data}")
                self.cloudinary_connected = False
                self._update_cloudinary_ui_status(False, "Connection failed")
        else:
            debug_cloudinary(f"❌ No data received from Cloudinary")
            self.cloudinary_connected = False
            self._update_cloudinary_ui_status(False, "No response")
    
    def _retrieve_cloudinary_files_cache(self):
        """Retrieve and cache Cloudinary files list once during initialization"""
        debug_cloudinary(f"Retrieving Cloudinary files list for global cache...")
        try:
            import cloudinary.api
            
            # Use the same logic as the original list_all_files function
            all_files = []
            next_cursor = None
            
            while True:
                resources = cloudinary.api.resources(
                    type="upload", max_results=100, next_cursor=next_cursor, tags=True
                )
                all_files.extend(resources['resources'])
                next_cursor = resources.get('next_cursor')
                if not next_cursor:
                    break
            
            self.cloudinary_files_cache = all_files
            self.cloudinary_cache_populated = True  # Mark that we've attempted to populate the cache
            debug_cloudinary(f"✅ Cached {len(self.cloudinary_files_cache)} files from Cloudinary for global use")
            
            # Update widget cloudinary_tags now that cache is loaded
            self._populate_widget_cloudinary_tags()
            
        except Exception as e:
            print(f"[WARNING] Could not retrieve Cloudinary files for cache: {e}")
            self.cloudinary_files_cache = []
            self.cloudinary_cache_populated = True  # Mark that we attempted even if it failed
    
    def create_colored_label_text(self, color, label_text, percentage):
        """Create HTML text with a colored square and percentage for credit labels"""
        return f'<span style="background-color: {color}; color: {color}; border: 1px solid #ccc;">██</span> {label_text} {percentage:.1f}%'

    def _populate_widget_cloudinary_tags(self):
        """Populate cloudinary_tags in widgets after Cloudinary cache is loaded"""
        if not hasattr(self, 'image_flow_manager') or not self.image_flow_manager:
            debug_cloudinary("No image_flow_manager available to populate cloudinary_tags")
            return
            
        if not hasattr(self, 'cloudinary_files_cache') or not self.cloudinary_files_cache:
            debug_cloudinary("No cloudinary_files_cache available to populate cloudinary_tags")
            return
            
        debug_cloudinary(f"Populating cloudinary_tags in {len(self.image_flow_manager.image_widgets)} widgets from {len(self.cloudinary_files_cache)} cached files")
        
        for file_path, widget in self.image_flow_manager.image_widgets.items():
            public_id = widget.get_cloudinary_public_id()
            if not public_id:
                continue
                
            # Find matching Cloudinary file
            for cf in self.cloudinary_files_cache:
                if cf.get('public_id') == public_id:
                    cf_tags = cf.get('tags', [])
                    if isinstance(cf_tags, list):
                        cloudinary_tags_list = [str(tag).strip() for tag in cf_tags if str(tag).strip()]
                        widget.set_cloudinary_tags(cloudinary_tags_list)
                        debug_cloudinary(f"✅ Populated cloudinary_tags for {os.path.basename(widget.file_path)}: {cloudinary_tags_list}")
                    break
            else:
                debug_cloudinary(f"⚠️ No Cloudinary file found for {os.path.basename(widget.file_path)} with public_id: {public_id}")
        
        debug_cloudinary("Finished populating cloudinary_tags in widgets")
    
    def update_credits_bar(self, storage_percent, transformations_percent, bandwidth_percent, resources_count=0):
        """Update the CloudinaryCreditsBar with usage data and resources count"""
        print(f"[UPLOAD REFRESH] update_credits_bar called with resources_count: {resources_count}")
        debug_cloudinary(f"main.py update_credits_bar() called with:")
        print(f"  Storage: {storage_percent} (type: {type(storage_percent)})")
        print(f"  Transformations: {transformations_percent} (type: {type(transformations_percent)})")
        print(f"  Bandwidth: {bandwidth_percent} (type: {type(bandwidth_percent)})")
        print(f"  Resources: {resources_count} (type: {type(resources_count)})")
        
        # Only update if Cloudinary is connected
        if not self.cloudinary_connected:
            debug_cloudinary(f" Cloudinary not connected - skipping credits bar update")
            return
            
        # Check if this is a duplicate update (same values as last time)
        # Include resources_count in the comparison to ensure overlay text updates
        current_values = (storage_percent, transformations_percent, bandwidth_percent, resources_count)
        if hasattr(self, '_last_credits_values') and self._last_credits_values == current_values:
            debug_cloudinary("Credits bar values unchanged - skipping unnecessary update")
            return
        
        try:
            # Check if the credits bar widget exists (whatever name it has in the UI)
            credits_bar = None
            
            # Try common names for the credits bar widget
            for attr_name in ['cloudinaryCreditsBar', 'creditsBar', 'credits_bar']:
                if hasattr(self, attr_name):
                    credits_bar = getattr(self, attr_name)
                    debug_cloudinary(f"Found credits bar widget: {attr_name}")
                    break
            
            if credits_bar is not None:
                print(f"[UPLOAD REFRESH] Credits bar found, updating...")
                # Define colors matching the original Cloudinary app
                STORAGE_COLOUR = "#b83232"      # Red
                TRANSFORMATIONS_COLOUR = "#32a4ba"  # Blue  
                BANDWIDTH_COLOUR = "#dbde3e"    # Yellow
                
                # Only set colors if this is the first time or they're not set
                if not self.credits_bar_initialized:
                    debug_cloudinary(f"First-time credits bar initialization")
                    credits_bar.setColors(STORAGE_COLOUR, TRANSFORMATIONS_COLOUR, BANDWIDTH_COLOUR)
                    self.credits_bar_initialized = True
                
                # Use the percentages directly (they're already calculated correctly in the Cloudinary data)
                storage_perc = float(storage_percent) if isinstance(storage_percent, (int, float)) else 0
                transformations_perc = float(transformations_percent) if isinstance(transformations_percent, (int, float)) else 0
                bandwidth_perc = float(bandwidth_percent) if isinstance(bandwidth_percent, (int, float)) else 0
                
                debug_tags(f"Converted percentages - Storage: {storage_perc}, Transformations: {transformations_perc}, Bandwidth: {bandwidth_perc}")
                
                # Set the percentages (this will handle caching internally)
                debug_tags(f"Calling setPercentages on credits bar")
                credits_bar.setPercentages(storage_perc, transformations_perc, bandwidth_perc)
                
                # Set the overlay text with resources count
                if resources_count > 0:
                    overlay_text = f"{resources_count} online images"
                    print(f"[UPLOAD REFRESH] Setting overlay text to: '{overlay_text}'")
                    debug_cloudinary(f"Setting overlay text: '{overlay_text}'")
                    credits_bar.setOverlayText(overlay_text)
                else:
                    print(f"[UPLOAD REFRESH] No overlay text set (resources_count: {resources_count})")
                    credits_bar.setOverlayText("")  # Clear overlay if no resources
                
                # Update the colored legend labels
                try:
                    # First, ensure the labels are visible (they might be hidden from startup)
                    cloudinary_widgets = [
                        ('storageLabel', getattr(self, 'storageLabel', None)),
                        ('transformationsLabel', getattr(self, 'transformationsLabel', None)), 
                        ('bandwidthLabel', getattr(self, 'bandwidthLabel', None)),
                        ('label', getattr(self, 'label', None))  # "Current Credits Usage" label
                    ]
                    
                    # Make widgets visible and update their text
                    for widget_name, widget in cloudinary_widgets:
                        if widget:
                            if not widget.isVisible():
                                widget.setVisible(True)
                                print(f"[LAYOUT FIX] Made {widget_name} visible")
                            else:
                                print(f"[LAYOUT FIX] {widget_name} was already visible")
                        else:
                            print(f"[LAYOUT FIX] Widget {widget_name} not found")
                    
                    if hasattr(self, 'storageLabel'):
                        storage_text = self.create_colored_label_text(STORAGE_COLOUR, "Storage", storage_perc)
                        self.storageLabel.setText(storage_text)
                        print(f"[LAYOUT FIX] Updated storageLabel: {storage_text}")
                    
                    if hasattr(self, 'transformationsLabel'):
                        transformations_text = self.create_colored_label_text(TRANSFORMATIONS_COLOUR, "Transformations", transformations_perc)
                        self.transformationsLabel.setText(transformations_text)
                        print(f"[LAYOUT FIX] Updated transformationsLabel: {transformations_text}")
                    
                    if hasattr(self, 'bandwidthLabel'):
                        bandwidth_text = self.create_colored_label_text(BANDWIDTH_COLOUR, "Bandwidth", bandwidth_perc)
                        self.bandwidthLabel.setText(bandwidth_text)
                        print(f"[LAYOUT FIX] Updated bandwidthLabel: {bandwidth_text}")
                        
                    # Force layout refresh after making widgets visible and updating text
                    print("[LAYOUT FIX] Calling layout refresh...")
                    self._force_layout_refresh_after_visibility_change()
                        
                except Exception as label_error:
                    print(f"[LAYOUT FIX] Error updating legend labels: {label_error}")
                    debug_cloudinary(f"Error updating legend labels: {label_error}")
                
                # Store values to prevent duplicate updates
                self._last_credits_values = current_values
                
                debug_cloudinary(f"📊 Credits bar updated - Storage: {storage_perc:.2f}%, Transformations: {transformations_perc:.2f}%, Bandwidth: {bandwidth_perc:.2f}%")
                
            else:
                print(f"[UPLOAD REFRESH] Credits bar widget not found!")
                debug_cloudinary(f"⚠️ Credits bar widget not found in main window")
                # List all widget attributes for debugging
                widget_attrs = [attr for attr in dir(self) if not attr.startswith('_') and hasattr(getattr(self, attr, None), 'setVisible')]
                debug_cloudinary(f"Available widget attributes: {widget_attrs[:10]}...")  # Show first 10
                
        except Exception as e:
            debug_cloudinary(f"❌ Error updating credits bar: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_cloudinary_ui_update(self, message):
        """Handle UI update messages from Cloudinary"""
        debug_cloudinary(f" Cloudinary UI update: {message}")
            
    def show_settings(self):
        """Create and show the settings dialog"""
        settings_dialog = SettingsDialog(self)
        result = settings_dialog.exec_()
        
        # If user clicked OK and settings were saved, re-initialize Cloudinary
        if result == QDialog.Accepted:
            debug_cloudinary(f"Settings saved, re-initializing Cloudinary...")
            # Reset credits bar flag to allow new data to be shown
            self.credits_bar_initialized = False
            if hasattr(self, '_last_credits_values'):
                delattr(self, '_last_credits_values')
            self.initialize_cloudinary()
            
    def on_tag_clicked(self, tag_text):
        debug_tags(f"Tag clicked: '{tag_text}' | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's input field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                current_text = self.get_widget_text(widget)
                debug_tags(f"Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
                # Split tags, strip whitespace, and ensure uniqueness
                tags = [t.strip() for t in current_text.split(',') if t.strip()]
                if tag_text in tags:
                    continue  # Skip if already present
                tags.append(tag_text)
                unique_tags = []
                seen = set()
                for t in tags:
                    if t not in seen:
                        unique_tags.append(t)
                        seen.add(t)
                new_text = ', '.join(unique_tags)
                
                # Use helper function to set the text (handles both ImageCardWidget and legacy widgets)
                self.set_widget_text(widget, new_text)
                debug_tags(f"After append | file_path: {widget.file_path} | new_text: '{new_text}'")
    
    def on_business_clicked(self, business_button):
        """Handle business button clicks and add business description to selected images with field-level duplicate checking"""
        business_text = business_button.get_full_description()
        business_fields = business_button.get_individual_fields()
        debug_tags(f"Business clicked: '{business_text}' | Fields: {business_fields} | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's text field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                current_text = self.get_widget_text(widget)
                debug_tags(f"Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
                
                # Advanced duplicate checking: check each field individually
                duplicate_fields = []
                missing_fields = []
                
                for field in business_fields:
                    if field.strip() and field.strip() in current_text:
                        duplicate_fields.append(field.strip())
                    else:
                        missing_fields.append(field.strip())
                
                # If all fields are already present, skip entirely
                if len(duplicate_fields) == len([f for f in business_fields if f.strip()]):
                    debug_tags(f"All business fields already present, skipping. Duplicates: {duplicate_fields}")
                    continue
                
                # If some fields are missing, add only the missing ones
                if missing_fields:
                    if duplicate_fields:
                        debug_tags(f"Partial duplicates found: {duplicate_fields}. Adding missing fields: {missing_fields}")
                        new_business_text = ", ".join(missing_fields)  # Add commas between fields
                    else:
                        debug_tags(f"No duplicates found. Adding all fields: {missing_fields}")
                        new_business_text = ", ".join(business_fields)  # Add commas between all fields
                else:
                    debug_tags(f"All fields already present, skipping")
                    continue
                
                # Add the new business text (handle comma duplication)
                if current_text:
                    # Check if current text already ends with comma or space
                    if current_text.rstrip().endswith(','):
                        new_text = f"{current_text} {new_business_text}"
                    else:
                        new_text = f"{current_text}, {new_business_text}"
                else:
                    new_text = new_business_text
                
                # Use helper function to set the text (handles both ImageCardWidget and legacy widgets)
                self.set_widget_text(widget, new_text)
                debug_tags(f"After append | file_path: {widget.file_path} | new_text: '{new_text}'")

    def on_building_clicked(self, building_button):
        """Handle building button clicks and add building description to selected images"""
        building_text = f"{building_button.building_name}, {building_button.street_address}"
        debug_tags(f"Building clicked: '{building_text}' | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's input field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                current_text = self.get_widget_text(widget)
                debug_tags(f"Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
                
                # Check for duplicates
                if building_text in current_text:
                    debug_tags(f" Building already present, skipping")
                    continue
                
                # Add the building text
                if current_text:
                    if current_text.rstrip().endswith(','):
                        new_text = f"{current_text} {building_text}"
                    else:
                        new_text = f"{current_text}, {building_text}"
                else:
                    new_text = building_text
                
                # Use helper function to set the text (handles both ImageCardWidget and legacy widgets)
                self.set_widget_text(widget, new_text)
                debug_tags(f"After append | file_path: {widget.file_path} | new_text: '{new_text}'")

    def on_street_clicked(self, street_button):
        """Handle street button clicks and add street name to selected images"""
        street_text = street_button.street_name
        debug_tags(f"Street clicked: '{street_text}' | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's text field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                # For ImageCardWidget, use text_edit instead of input_field
                if hasattr(widget, 'text_edit'):
                    text_field = widget.text_edit
                    current_text = text_field.toPlainText().strip()
                    debug_tags(f"Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
                    
                    # Check for duplicates
                    if street_text in current_text:
                        debug_tags(f" Street already present, skipping")
                        continue
                    
                    # Add the street text
                    if current_text:
                        if current_text.rstrip().endswith(','):
                            new_text = f"{current_text} {street_text}"
                        else:
                            new_text = f"{current_text}, {street_text}"
                    else:
                        new_text = street_text
                    
                    # For ImageCardWidget, use set_tags method which handles text properly
                    # Convert current text to list, add street, and set back
                    current_tags = [tag.strip() for tag in current_text.split(',') if tag.strip()] if current_text else []
                    if street_text not in current_tags:
                        current_tags.append(street_text)
                        widget.set_tags(', '.join(current_tags))
                        debug_tags(f"After append | file_path: {widget.file_path} | new_tags: '{', '.join(current_tags)}'")
                
                # Handle legacy widget types (if any still exist)
                elif hasattr(widget, 'input_field'):
                    input_field = widget.input_field
                    current_text = input_field.toPlainText().strip()
                    
                    # Check for duplicates
                    if street_text in current_text:
                        continue
                    
                    # Add the street text
                    if current_text:
                        if current_text.rstrip().endswith(','):
                            new_text = f"{current_text} {street_text}"
                        else:
                            new_text = f"{current_text}, {street_text}"
                    else:
                        new_text = street_text
                    
                    # Prevent real-time sync during programmatic text setting
                    input_field._updating = True
                    input_field.setText(new_text)
                    input_field._updating = False
                    debug_tags(f"After append | file_path: {widget.file_path} | new_text: '{new_text}'")
                    
                    # Apply proper height calculation
                    input_field.document().adjustSize()
                    doc_height = int(input_field.document().size().height())
                    margins = input_field.contentsMargins()
                    padding = 8
                    new_height = doc_height + margins.top() + margins.bottom() + padding
                    final_height = max(28, new_height)
                    input_field.setFixedHeight(final_height)
                    
                    # Update container height if function is available
                    if hasattr(widget, 'updateContainerHeight'):
                        widget.updateContainerHeight()

if __name__ == '__main__':
    try:
        debug_tags(f"Starting HappyTag application...")
        app = QApplication(sys.argv)
        debug_startup("QApplication created successfully")
        
        window = MainWindow()
        debug_startup("MainWindow created successfully")
        
        window.show()
        debug_startup("Window shown, starting event loop...")
        
        result = app.exec_()
        debug_startup(f"Application exited with code: {result}")
        sys.exit(result)
        
    except Exception as e:
        print(f"\n=== CRITICAL ERROR ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("======================")
        
        # If running as PyInstaller executable, pause before exit
        if getattr(sys, 'frozen', False):
            print("\nRunning as executable. Press Enter to close...")
            try:
                input()
            except:
                import time
                time.sleep(5)
        sys.exit(1)
