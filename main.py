import sys
import os
import re
import gc
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from PyQt5.QtWidgets import (QMainWindow, QApplication, QFileDialog, 
                           QWidget, QLabel, QTextEdit, QMessageBox,
                           QVBoxLayout, QGridLayout, QSizePolicy, QProgressBar, QRubberBand)
from PyQt5.QtCore import Qt, QTimer, QSize, QRect, QPoint, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from tag_manager import TagManager
from settings_dialog import SettingsDialog

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
            print(f"[DEBUG] Cleaning up any stale ExifTool processes...")
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
            print(f"[DEBUG] Stale process cleanup completed")
        except Exception as e:
            print(f"[DEBUG] Process cleanup warning (non-critical): {e}")
    
    # Clean up any stale processes first
    cleanup_stale_exiftool_processes()
    
    def detect_exiftool_path():
        """Detect the appropriate ExifTool executable based on the current system"""
        base_path = resource_path('packages')
        
        system = platform.system().lower()
        architecture = platform.machine().lower()
        is_64bit = struct.calcsize("P") * 8 == 64
        
        if system == 'windows':
            # Windows: choose between 32-bit and 64-bit versions
            if is_64bit:
                exiftool_path = os.path.join(base_path, 'exiftool_win64', 'exiftool-13.34_64', 'exiftool(-k).exe')
                print(f"Detected 64-bit Windows, looking for: {exiftool_path}")
            else:
                exiftool_path = os.path.join(base_path, 'exiftool_win32', 'exiftool-13.34_32', 'exiftool(-k).exe')
                print(f"Detected 32-bit Windows, looking for: {exiftool_path}")
        
        elif system == 'darwin':  # macOS
            # For Mac, we'll use the .pkg content when available
            exiftool_path = os.path.join(base_path, 'exiftool_mac', 'exiftool')
            print(f"Detected macOS, looking for: {exiftool_path}")
        
        elif system == 'linux':
            # For Linux, try the Perl version or system installation
            exiftool_path = os.path.join(base_path, 'Image-ExifTool-13.34', 'exiftool')
            print(f"Detected Linux, looking for: {exiftool_path}")
        
        else:
            print(f"Unsupported system: {system}")
            return None
        
        if os.path.exists(exiftool_path):
            return exiftool_path
        else:
            print(f"ExifTool executable not found at: {exiftool_path}")
            return None
    
    # Try to find local ExifTool installation
    local_exiftool_path = detect_exiftool_path()
    
    print(f"[DEBUG] Local ExifTool path detected: {local_exiftool_path}")
    
    if local_exiftool_path:
        # Test if local ExifTool works
        try:
            print(f"[DEBUG] Testing local ExifTool at: {local_exiftool_path}")
            with exiftool.ExifTool(executable=local_exiftool_path) as et:
                # Simple test - try to get version
                test_result = et.execute("-ver")
                print(f"[DEBUG] ExifTool version test result: {test_result}")
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = local_exiftool_path
            print(f"Successfully using local ExifTool from: {local_exiftool_path}")
        except Exception as e:
            print(f"Local ExifTool test failed: {e}")
            EXIFTOOL_AVAILABLE = False
            EXIFTOOL_PATH = None
    else:
        print(f"[DEBUG] No local ExifTool path found")
        EXIFTOOL_AVAILABLE = False
        EXIFTOOL_PATH = None
    
    # Fallback to system ExifTool if local one doesn't work
    if not EXIFTOOL_AVAILABLE:
        print(f"[DEBUG] Trying system ExifTool as fallback")
        try:
            with exiftool.ExifTool() as et:
                test_result = et.execute("-ver")
                print(f"[DEBUG] System ExifTool version test result: {test_result}")
            EXIFTOOL_AVAILABLE = True
            EXIFTOOL_PATH = None
            print("Using system ExifTool")
        except Exception:
            EXIFTOOL_AVAILABLE = False
            EXIFTOOL_PATH = None
            print("Warning: ExifTool executable not found - using fallback metadata reading")

    print(f"[DEBUG] Final ExifTool status: EXIFTOOL_AVAILABLE={EXIFTOOL_AVAILABLE}, EXIFTOOL_PATH={EXIFTOOL_PATH}")

except ImportError:
    EXIFTOOL_AVAILABLE = False
    EXIFTOOL_PATH = None
    print("Warning: PyExifTool not available - using fallback metadata reading")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Check if UI file exists before loading
        ui_path = resource_path('ui/mainWindow.ui')
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")
            
        # Load the UI
        uic.loadUi(ui_path, self)
        
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
        
        # Setup grid layout with minimal spacing
        self.grid_layout = QGridLayout(self.picturesContainer)
        self.grid_layout.setSpacing(5)  # Reduced from 10 to 5
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        
        # Rubber band selection variables
        self.selection_start = None
        self.selection_rect = None
        self.rubber_band = None
        self.is_selecting = False
        
        # Install event filter for rubber band selection
        self.picturesContainer.installEventFilter(self)
        self.picturesContainer.setMouseTracking(True)
        
        # Add mouse press handler to pictures container for deselecting on empty area clicks
        def picturesContainerMousePress(event):
            # Check if click is on empty area (not on any widget)
            clicked_widget = self.picturesContainer.childAt(event.pos())
            
            # More precise empty area detection
            is_empty_area = True
            if clicked_widget is not None:
                # Check if the clicked widget is actually one of our image containers
                for widget in self.image_widgets:
                    if hasattr(widget, 'file_path'):
                        # Check if click is within the actual widget bounds (not extended layout area)
                        widget_rect = widget.geometry()
                        if widget_rect.contains(event.pos()):
                            is_empty_area = False
                            break
                        
                        # Also check if clicked on the image_container or input_field specifically
                        if (hasattr(widget, 'image_container') and widget.image_container == clicked_widget) or \
                           (hasattr(widget, 'input_field') and widget.input_field == clicked_widget):
                            is_empty_area = False
                            break
            
            if is_empty_area:
                print("[DEBUG] Clicked on empty area - deselecting all")
                # Deselect all images
                for widget in self.image_widgets:
                    if hasattr(widget, 'file_path'):
                        if hasattr(widget, 'image_label') and hasattr(widget, 'input_field'):
                            widget.image_label.setProperty("selected", False)
                            widget.input_field.setProperty("selected", False)
                            widget.image_label.style().polish(widget.image_label)
                            widget.input_field.style().polish(widget.input_field)
                self.selected_images.clear()
                self.update_status_bar()
        
        self.picturesContainer.mousePressEvent = picturesContainerMousePress
        
        # Connect signals
        self.actionOpenFiles.triggered.connect(self.open_files)
        self.actionOpen_Folder.triggered.connect(self.open_folder)
        self.horizontalSlider.valueChanged.connect(self.update_layout)
        
        # Connect Save action for metadata
        if hasattr(self, 'actionSave'):
            self.actionSave.triggered.connect(self.save_all_keywords)
        
        # Connect Settings action
        if hasattr(self, 'actionSettings'):
            self.actionSettings.triggered.connect(self.show_settings)
        
        # Create the Tags Window action if it doesn't exist
        if not hasattr(self, 'actionTags_Window'):
            from PyQt5.QtWidgets import QAction
            self.actionTags_Window = QAction("Show Tags Window", self)
            self.menuWindow.addAction(self.actionTags_Window)
        
        # Initialize tag manager as None
        self.tag_manager = None
        
        # Connect Tags Window action
        self.actionTags_Window.triggered.connect(self.show_tag_manager)
        
        # Connect the Tags Window menu action
        if hasattr(self, 'menuTags_Window'):
            self.menuTags_Window.triggered.connect(self.show_tag_manager)
        
        # Store loaded images
        self.image_files = []
        self.image_previews = {}
        self.image_metadata = {}  # Store metadata (year, keywords) for each image
        self.original_keywords = {}  # Track original keywords for change detection
        self.image_widgets = []
        
        # Initialize column slider (1-7 columns, default to 6)
        self.horizontalSlider.setMinimum(1)
        self.horizontalSlider.setMaximum(7)
        self.horizontalSlider.setValue(6)
        
        self.MAX_PREVIEW_SIZE = 800
        self.selected_images = set()
        
        # Create progress bar overlay (initially hidden)
        self.progress_overlay = None
        self.progress_bar = None
        
        # Track metadata errors for reporting
        self.metadata_errors = []
        
        # Flag to enable/disable metadata reading (can be toggled if causing issues)
        self.enable_metadata_reading = True
        
        # Track files that caused metadata reading issues
        self.problematic_files = set()
        
        # Initialize persistent ExifTool instance for better performance
        self.persistent_exiftool = None
        self.exiftool_available = False
        self.init_persistent_exiftool()

    def init_persistent_exiftool(self):
        """Initialize a persistent ExifTool instance for better performance"""
        global EXIFTOOL_AVAILABLE, EXIFTOOL_PATH
        
        # First, ensure any existing instance is cleaned up
        self.cleanup_persistent_exiftool()
        
        try:
            # Check if exiftool module is available
            import exiftool as et_module
            
            if EXIFTOOL_AVAILABLE:
                print(f"[DEBUG] Initializing persistent ExifTool...")
                
                try:
                    if EXIFTOOL_PATH:
                        print(f"[DEBUG] Using local ExifTool: {EXIFTOOL_PATH}")
                        self.persistent_exiftool = et_module.ExifTool(executable=EXIFTOOL_PATH)
                    else:
                        print(f"[DEBUG] Using system ExifTool")
                        self.persistent_exiftool = et_module.ExifTool()
                    
                    # Start the persistent process using __enter__
                    print(f"[DEBUG] Starting ExifTool process...")
                    self.persistent_exiftool.__enter__()
                    
                    # Test the connection with a simple command
                    test_result = self.persistent_exiftool.execute("-ver")
                    print(f"[DEBUG] ExifTool connection test: {test_result.strip()}")
                    
                    self.exiftool_available = True
                    print(f"[DEBUG] Persistent ExifTool started successfully")
                    
                except Exception as start_error:
                    print(f"[DEBUG] Failed to start ExifTool process: {start_error}")
                    self.exiftool_available = False
                    self.persistent_exiftool = None
                    
            else:
                print(f"[DEBUG] ExifTool not available globally, skipping persistent instance")
                self.exiftool_available = False
                
        except ImportError:
            print(f"[DEBUG] ExifTool module not available for persistent instance")
            self.exiftool_available = False
        except Exception as e:
            print(f"[DEBUG] Failed to initialize persistent ExifTool: {e}")
            self.exiftool_available = False
            self.persistent_exiftool = None

    def cleanup_persistent_exiftool(self):
        """Clean up the persistent ExifTool instance"""
        if hasattr(self, 'persistent_exiftool') and self.persistent_exiftool:
            try:
                print(f"[DEBUG] Terminating persistent ExifTool...")
                self.persistent_exiftool.__exit__(None, None, None)
                print(f"[DEBUG] Persistent ExifTool terminated successfully")
            except Exception as e:
                print(f"[DEBUG] Error terminating persistent ExifTool: {e}")
            finally:
                self.persistent_exiftool = None
                self.exiftool_available = False

    def closeEvent(self, event):
        """Handle application close event to clean up resources"""
        self.cleanup_persistent_exiftool()
        super().closeEvent(event)

    def get_image_metadata(self, file_path):
        """Extract year and keywords from image metadata using persistent ExifTool (unified approach)"""
        year = None
        keywords = []
        filename = os.path.basename(file_path)
        
        # Skip files that previously caused issues
        if file_path in self.problematic_files:
            print(f"[DEBUG] Skipping problematic file: {filename}")
            return year, keywords
        
        try:
            if self.exiftool_available and self.persistent_exiftool:
                print(f"[DEBUG] Reading metadata with persistent ExifTool from: {filename}")
                
                # Use the persistent ExifTool instance (no context manager needed)
                et = self.persistent_exiftool
                
                # Read date/time fields for year extraction
                try:
                    # Try DateTimeOriginal first (when photo was taken)
                    date_original = et.execute('-DateTimeOriginal', file_path)
                    if date_original and not date_original.startswith('Warning') and date_original.strip():
                        for line in date_original.strip().split('\n'):
                            if 'original' in line.lower() and ':' in line:
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
                                        print(f"[DEBUG] Found DateTimeOriginal year: {year}")
                                        break
                                    except ValueError:
                                        continue
                    
                    # Fallback to CreateDate if DateTimeOriginal not found
                    if not year:
                        create_date = et.execute('-CreateDate', file_path)
                        if create_date and not create_date.startswith('Warning') and create_date.strip():
                            for line in create_date.strip().split('\n'):
                                if 'create' in line.lower() and ':' in line:
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
                                            print(f"[DEBUG] Found CreateDate year: {year}")
                                            break
                                        except ValueError:
                                            continue
                                        
                except Exception as e:
                    print(f"[DEBUG] Date extraction failed: {e}")
                
                # Read keywords (existing logic)
                if self.enable_metadata_reading:
                    try:
                        # Try to get IPTC Keywords
                        iptc_keywords = et.execute('-IPTC:Keywords', file_path)
                        if iptc_keywords and not iptc_keywords.startswith('Warning') and iptc_keywords.strip():
                            for line in iptc_keywords.strip().split('\n'):
                                if 'keywords' in line.lower() and ':' in line:
                                    keyword_values = line.split(':', 1)[1].strip()
                                    
                                    # Try semicolon separator first, then comma separator
                                    if ';' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(';') if k.strip()]
                                        keywords.extend(split_keywords)
                                    elif ',' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(',') if k.strip()]
                                        keywords.extend(split_keywords)
                                    else:
                                        keywords.append(keyword_values.strip())
                    except Exception as e:
                        print(f"[DEBUG] IPTC Keywords read failed: {e}")
                    
                    try:
                        # Try to get XMP Keywords  
                        xmp_keywords = et.execute('-XMP:Keywords', file_path)
                        if xmp_keywords and not xmp_keywords.startswith('Warning') and xmp_keywords.strip():
                            for line in xmp_keywords.strip().split('\n'):
                                if 'keywords' in line.lower() and ':' in line:
                                    keyword_values = line.split(':', 1)[1].strip()
                                    
                                    # Try semicolon separator first, then comma separator
                                    if ';' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(';') if k.strip()]
                                        keywords.extend(split_keywords)
                                    elif ',' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(',') if k.strip()]
                                        keywords.extend(split_keywords)
                                    else:
                                        keywords.append(keyword_values.strip())
                    except Exception as e:
                        print(f"[DEBUG] XMP Keywords read failed: {e}")
                    
                    try:
                        # Try to get XMP Subject (Dublin Core - for Windows/cross-platform compatibility)
                        xmp_subject = et.execute('-XMP:Subject', file_path)
                        if xmp_subject and not xmp_subject.startswith('Warning') and xmp_subject.strip():
                            for line in xmp_subject.strip().split('\n'):
                                if 'subject' in line.lower() and ':' in line:
                                    keyword_values = line.split(':', 1)[1].strip()
                                    
                                    # Try semicolon separator first, then comma separator
                                    if ';' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(';') if k.strip()]
                                        keywords.extend(split_keywords)
                                    elif ',' in keyword_values:
                                        split_keywords = [k.strip() for k in keyword_values.split(',') if k.strip()]
                                        keywords.extend(split_keywords)
                                    else:
                                        keywords.append(keyword_values.strip())
                    except Exception as e:
                        print(f"[DEBUG] XMP Subject read failed: {e}")
                
            # Fallback to PIL for date if ExifTool not available
            elif not year:
                print(f"[DEBUG] Using PIL fallback for date extraction: {filename}")
                try:
                    with Image.open(file_path) as img:
                        # Try to get EXIF data for JPEG files
                        try:
                            exif = img._getexif()
                            if exif:
                                for tag_id in exif:
                                    tag = TAGS.get(tag_id, tag_id)
                                    if tag == 'DateTimeOriginal':
                                        date_str = exif[tag_id]
                                        year = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').year
                                        break
                        except (AttributeError, TypeError):
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
                print(f"[DEBUG] Using file creation year: {year}")
            
            # Remove duplicate keywords while preserving order
            unique_keywords = []
            seen = set()
            for keyword in keywords:
                if keyword and keyword not in seen:
                    unique_keywords.append(keyword)
                    seen.add(keyword)
            
            if year:
                print(f"[DEBUG] Found year for {filename}: {year}")
            if unique_keywords:
                print(f"[DEBUG] Found keywords for {filename}: {unique_keywords}")
                
            return year, unique_keywords
                
        except Exception as e:
            error_msg = str(e)[:200]
            print(f"[DEBUG] Metadata read failed for {filename}: {error_msg}")
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

    def has_keywords_changed(self, file_path, current_keywords_text):
        """Check if keywords have changed compared to original"""
        # Parse current keywords from text field
        current_keywords = [k.strip() for k in current_keywords_text.split(',') if k.strip()]
        
        # Get original keywords (including year)
        original_keywords = self.original_keywords.get(file_path, [])
        
        # Check if this is a new file that had the year automatically added
        is_new_file_with_year = hasattr(self, 'new_files_with_year') and file_path in self.new_files_with_year
        
        # Compare sets (order doesn't matter for keywords)
        current_set = set(current_keywords)
        original_set = set(original_keywords)
        
        changed = current_set != original_set
        if changed:
            print(f"[DEBUG] Keywords changed for {os.path.basename(file_path)}")
            print(f"[DEBUG]   Original: {sorted(original_set)}")
            print(f"[DEBUG]   Current:  {sorted(current_set)}")
        else:
            print(f"[DEBUG] Keywords unchanged for {os.path.basename(file_path)}")
        
        return changed

    def save_keywords_to_image(self, file_path, keywords_text):
        """Save keywords to image metadata using ExifTool (with fallback notification)"""
        # Check if keywords have actually changed
        if not self.has_keywords_changed(file_path, keywords_text):
            print(f"[DEBUG] Skipping save for {os.path.basename(file_path)} - no changes")
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
                print(f"[DEBUG] Saving keywords with persistent ExifTool to {file_path}: {keywords}")
                
                # Use the persistent ExifTool instance (no context manager needed)
                et = self.persistent_exiftool
                
                # Check if format supports metadata writing based on ExifTool capabilities
                # Based on ExifTool -listwf output: GIF, PNG, JPEG, TIFF support writing
                # BMP and many other formats do NOT support metadata writing
                writable_formats = ['.jpg', '.jpeg', '.tiff', '.tif', '.png', '.gif', '.webp']

                if file_ext not in writable_formats:
                    # Format doesn't support metadata writing
                    format_msg = f"Format {file_ext.upper()} doesn't support metadata writing. Keywords preserved in application only."
                    print(f"[DEBUG] {format_msg}")
                    return False, format_msg
                
                # Write only to keyword fields (not subject fields)
                try:
                    # For JPEG/TIFF: Write to IPTC and XMP Keywords + XMP Subject for cross-platform compatibility
                    if file_ext in ['.jpg', '.jpeg', '.tiff', '.tif']:
                        # Write IPTC Keywords (semicolon-separated for legacy compatibility)
                        keywords_str = ';'.join(keywords) if keywords else ''
                        et.execute(f'-IPTC:Keywords={keywords_str}', '-overwrite_original', file_path)
                        
                        # Write XMP Keywords (semicolon-separated for macOS compatibility)
                        et.execute(f'-XMP:Keywords={keywords_str}', '-overwrite_original', file_path)
                        
                        # Write XMP Subject as individual array elements (for Windows Explorer)
                        if keywords:
                            # Clear existing subject first
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                            # Add each keyword as separate array element
                            for keyword in keywords:
                                et.execute(f'-XMP:Subject+={keyword}', '-overwrite_original', file_path)
                        else:
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                    
                    # For PNG: Use XMP Keywords + XMP Subject for cross-platform compatibility
                    elif file_ext == '.png':
                        # Write XMP Keywords (semicolon-separated for macOS compatibility)
                        keywords_str = ';'.join(keywords) if keywords else ''
                        et.execute(f'-XMP:Keywords={keywords_str}', '-overwrite_original', file_path)
                        
                        # Write XMP Subject as individual array elements (for Windows Explorer)
                        if keywords:
                            # Clear existing subject first
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                            # Add each keyword as separate array element
                            for keyword in keywords:
                                et.execute(f'-XMP:Subject+={keyword}', '-overwrite_original', file_path)
                        else:
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                    
                    # For GIF: Use XMP Keywords + XMP Subject for cross-platform compatibility
                    elif file_ext == '.gif':
                        # Write XMP Keywords (semicolon-separated for macOS compatibility)
                        keywords_str = ';'.join(keywords) if keywords else ''
                        et.execute(f'-XMP:Keywords={keywords_str}', '-overwrite_original', file_path)
                        
                        # Write XMP Subject as individual array elements (for Windows Explorer)
                        if keywords:
                            # Clear existing subject first
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                            # Add each keyword as separate array element
                            for keyword in keywords:
                                et.execute(f'-XMP:Subject+={keyword}', '-overwrite_original', file_path)
                        else:
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                    
                    # For WebP: Use XMP Keywords + XMP Subject for cross-platform compatibility
                    elif file_ext == '.webp':
                        # Write XMP Keywords (semicolon-separated for macOS compatibility)
                        keywords_str = ';'.join(keywords) if keywords else ''
                        et.execute(f'-XMP:Keywords={keywords_str}', '-overwrite_original', file_path)
                        
                        # Write XMP Subject as individual array elements (for Windows Explorer)
                        if keywords:
                            # Clear existing subject first
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                            # Add each keyword as separate array element
                            for keyword in keywords:
                                et.execute(f'-XMP:Subject+={keyword}', '-overwrite_original', file_path)
                        else:
                            et.execute('-XMP:Subject=', '-overwrite_original', file_path)
                    
                    # Update original keywords after successful save (including year)
                    self.original_keywords[file_path] = keywords.copy()
                    
                    # Remove from new files tracking after successful save
                    if hasattr(self, 'new_files_with_year') and file_path in self.new_files_with_year:
                        self.new_files_with_year.remove(file_path)
                    
                    print(f"[DEBUG] Successfully saved keywords to {file_path}")
                    return True, ""
                except Exception as write_e:
                    error_msg = f"ExifTool write error: {str(write_e)[:200]}"
                    print(f"[DEBUG] {error_msg}")
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"ExifTool write error: {str(e)[:200]}"
                print(f"[DEBUG] {error_msg}")
                return False, error_msg
        
        else:
            # ExifTool not available - return informative message
            return False, "ExifTool not available for writing metadata. Keywords will be preserved in the application but not saved to file metadata."

    def save_all_keywords(self):
        """Save keywords from all image text fields to their respective files"""
        if not self.image_widgets:
            QMessageBox.information(self, "Save Keywords", "No images loaded to save keywords to.")
            return
        
        success_count = 0
        skipped_count = 0
        error_files = []
        
        # Show progress bar
        self.show_progress(len(self.image_widgets))
        
        for i, widget in enumerate(self.image_widgets):
            if hasattr(widget, 'file_path') and hasattr(widget, 'input_field'):
                file_path = widget.file_path
                keywords_text = widget.input_field.toPlainText().strip()
                
                self.update_progress(i + 1)
                QApplication.processEvents()  # Keep UI responsive
                
                # Check if changes exist before attempting save
                if not self.has_keywords_changed(file_path, keywords_text):
                    skipped_count += 1
                    continue
                
                success, error_msg = self.save_keywords_to_image(file_path, keywords_text)
                
                if success:
                    success_count += 1
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
                QMessageBox.information(self, "Save Keywords", 
                                      f"No images needed saving - all {skipped_count} images have unchanged keywords!")
            elif skipped_count > 0:
                QMessageBox.information(self, "Save Keywords", 
                                      f"Successfully saved keywords to {success_count} modified images! "
                                      f"({skipped_count} images skipped - no changes)")
            else:
                QMessageBox.information(self, "Save Keywords", 
                                      f"Successfully saved keywords to all {success_count} images!")

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
        progress_container.setFixedSize(300, 80)
        
        # Create progress bar layout
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(10)
        
        # Add loading label
        loading_label = QLabel("Loading images...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        progress_layout.addWidget(loading_label)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Add container to overlay
        overlay_layout.addWidget(progress_container)
        
        # Position overlay to cover the entire window
        self.progress_overlay.resize(self.size())
        self.progress_overlay.hide()
    
    def show_progress(self, total_files):
        """Show progress bar with total file count"""
        if not self.progress_overlay:
            self.create_progress_overlay()
        
        self.progress_bar.setRange(0, total_files)
        self.progress_bar.setValue(0)
        self.progress_overlay.resize(self.size())
        self.progress_overlay.show()
        self.progress_overlay.raise_()
    
    def update_progress(self, current_file):
        """Update progress bar"""
        if self.progress_bar:
            self.progress_bar.setValue(current_file)
            QApplication.processEvents()  # Force UI update
    
    def hide_progress(self):
        """Hide progress bar"""
        if self.progress_overlay:
            self.progress_overlay.hide()
    
    def resizeEvent(self, event):
        """Handle window resize to reposition progress overlay"""
        super().resizeEvent(event)
        if self.progress_overlay:
            self.progress_overlay.resize(self.size())

    def update_status_bar(self):
        """Update the status bar with selection info"""
        if self.selected_images:
            self.statusBar().showMessage(f"Selected {len(self.selected_images)} images")
        else:
            self.statusBar().showMessage("Ready")

    def create_preview(self, file_path):
        """Create and store a preview of the image with metadata reading for accurate progress"""
        try:
            print(f"Creating preview from file: {file_path}")
            
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
                
                pixmap = QPixmap(file_path).scaled(
                    width, height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                if not pixmap.isNull():
                    print(f"Preview size: {pixmap.width()}x{pixmap.height()}")
                    self.image_previews[file_path] = pixmap
                    
                    # Read metadata during preview creation for accurate progress tracking
                    year, keywords = self.get_image_metadata(file_path)
                    
                    # Store metadata with the preview for later use
                    if not hasattr(self, 'image_metadata'):
                        self.image_metadata = {}
                    self.image_metadata[file_path] = {
                        'year': year,
                        'keywords': keywords
                    }
                    
                    # Store original keywords for change tracking (including year for new files)
                    if not hasattr(self, 'original_keywords'):
                        self.original_keywords = {}
                    # Track if this is a new file that will need the year added
                    if not hasattr(self, 'new_files_with_year'):
                        self.new_files_with_year = set()
                    # If the file has no existing keywords but will get a year, mark it as needing save
                    if not keywords and year:
                        self.new_files_with_year.add(file_path)
                        # Store empty original keywords for new files
                        self.original_keywords[file_path] = []
                    else:
                        # Store all existing keywords including year if present
                        self.original_keywords[file_path] = keywords.copy() if keywords else []
                    
                    # Year will be added to UI and saved as a keyword in metadata
                    
                    return pixmap
                else:
                    print(f"Error: Could not create preview for {file_path}")
                    return None
                    
        except Exception as e:
            print(f"Error creating preview for {file_path}: {e}")
            return None

    def create_image_widget(self, preview, max_width, file_path):
        """Create a widget containing an image and its input field"""
        print(f"Creating image widget with max_width: {max_width}")
        
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
                
            print(f"[DEBUG] sync_tags | last_word: '{last_word}' | source_field: {getattr(source_field, 'file_path', None)}")
            for widget in self.image_widgets:
                if (hasattr(widget, 'file_path') and 
                    widget.file_path in self.selected_images and 
                    widget.input_field != source_field):
                    
                    target = widget.input_field
                    target._updating = True
                    existing = target.toPlainText().strip()
                    print(f"[DEBUG] sync_tags | target file_path: {widget.file_path} | existing: '{existing}'")
                    if existing:
                        if not existing.endswith(','):
                            existing += ','
                        existing += ' '
                        target.setText(f"{existing}{last_word}")
                        print(f"[DEBUG] sync_tags | setText: '{existing}{last_word}'")
                    else:
                        target.setText(last_word)
                        print(f"[DEBUG] sync_tags | setText: '{last_word}'")
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
            input_field.document().setTextWidth(current_width - 10)  # Account for margins
            
            # Calculate required height based on document content
            input_field.document().adjustSize()
            doc_height = int(input_field.document().size().height())
            margins = input_field.contentsMargins()
            padding = 8
            new_height = doc_height + margins.top() + margins.bottom() + padding
            
            # Set minimum height but no maximum - always show all content
            final_height = max(28, new_height)
            input_field.setFixedHeight(final_height)
            updateContainerHeight()  # Update container height after input field height change
            print(f"[DEBUG] updateHeight | file_path: {file_path} | width: {current_width} | content_lines: {content.count(chr(10))+1} | new_height: {final_height}")
        
        def updateHeightImmediate():
            """Immediate height update without timer delay"""
            content = input_field.toPlainText()
            if not content:
                input_field.setFixedHeight(28)
                updateContainerHeight()  # Update container height after input field height change
                return
                
            # Ensure document width matches the current text field width
            current_width = input_field.width()
            input_field.document().setTextWidth(current_width - 10)  # Account for margins
            
            # Force document to recalculate size with proper width
            input_field.document().adjustSize()
            
            # Calculate required height based on document content  
            doc_height = int(input_field.document().size().height())
            margins = input_field.contentsMargins()
            padding = 8
            new_height = doc_height + margins.top() + margins.bottom() + padding
            
            # Set minimum height but no maximum - always show all content
            final_height = max(28, new_height)
            input_field.setFixedHeight(final_height)
            updateContainerHeight()  # Update container height after input field height change
        
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
            
            print(f"[DEBUG] focusInEvent | file_path: {file_path} | focus_start_text: '{current_text}' | boundary: {input_field._pre_existing_boundary}")
            
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
            
            print(f"[DEBUG] onTextChanged | file_path: {file_path} | current_text: '{current_text}' | selected: {input_field.property('selected')}")
            
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
                    print(f"[DEBUG] onTextChanged | Text change detected - last_synced: '{last_synced}' -> current: '{current_text}'")
                    
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
                            
                            print(f"[DEBUG] onTextChanged | sync to: {widget.file_path}")
                            print(f"[DEBUG]   target_pre_existing: '{target_pre_existing}' (boundary: {target_boundary})")
                            print(f"[DEBUG]   source_typed: '{source_typed_content}' (from boundary: {source_boundary})")
                            print(f"[DEBUG]   result: '{new_content}'")
                            
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
            print(f"[DEBUG] update_selection_state | file_path: {file_path} | selected: {selected}")
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
                    
                    return True
        
        return super().eventFilter(obj, event)

    def select_widgets_in_rect(self, rect):
        """Select all image widgets that intersect with the selection rectangle"""
        # Clear current selection if not holding Ctrl
        modifiers = QApplication.keyboardModifiers()
        if not (modifiers & 0x04000000):  # Qt.ControlModifier
            self.clear_selection()
        
        # Find widgets that intersect with selection rect
        newly_selected = []
        for widget in self.image_widgets:
            if hasattr(widget, 'geometry'):
                widget_rect = widget.geometry()
                if rect.intersects(widget_rect):
                    file_path = getattr(widget, 'file_path', None)
                    if file_path:
                        if modifiers & 0x04000000:  # Qt.ControlModifier
                            # Toggle selection with Ctrl
                            if file_path in self.selected_images:
                                self.selected_images.remove(file_path)
                                self.update_selection_state(file_path, False)
                            else:
                                self.selected_images.add(file_path)
                                self.update_selection_state(file_path, True)
                                newly_selected.append(file_path)
                        else:
                            # Add to selection
                            self.selected_images.add(file_path)
                            self.update_selection_state(file_path, True)
                            newly_selected.append(file_path)
        
        # Update status bar
        if hasattr(self, 'statusBar') and self.statusBar():
            if self.selected_images:
                self.statusBar().showMessage(f"Selected {len(self.selected_images)} images")
            else:
                self.statusBar().showMessage("Ready")
        
        print(f"[DEBUG] Rubber band selection: {len(newly_selected)} images selected")

    def clear_selection(self):
        """Clear all selected images"""
        for file_path in list(self.selected_images):
            self.update_selection_state(file_path, False)
        self.selected_images.clear()

    def update_selection_state(self, file_path, selected):
        """Update the visual selection state of an image widget"""
        # Find the widget for this file path
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path == file_path:
                if hasattr(widget, 'image_label'):
                    widget.image_label.setProperty("selected", selected)
                    widget.image_label.style().polish(widget.image_label)
                if hasattr(widget, 'input_field'):
                    widget.input_field.setProperty("selected", selected)
                    widget.input_field.style().polish(widget.input_field)
                break

    def update_layout(self, value=None):
        print("\nStarting update_layout...")
        if not self.image_files:
            print("No image files to display")
            return
        
        # PRESERVE EXISTING TEXT CONTENT before clearing widgets
        preserved_text = {}
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and hasattr(widget, 'input_field'):
                preserved_text[widget.file_path] = widget.input_field.toPlainText()
                print(f"[DEBUG] Preserving text for {widget.file_path}: '{preserved_text[widget.file_path]}'")
            
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        self.image_widgets.clear()
        
        scroll_bar_width = 30
        safety_margin = 10
        
        container_margin = self.grid_layout.contentsMargins()
        total_margins = (container_margin.left() + container_margin.right() + 
                        self.scrollArea.verticalScrollBar().width())
        
        grid_spacing = self.grid_layout.spacing()
        scroll_area_margins = self.scrollArea.widget().layout().contentsMargins()
        total_margins += (scroll_area_margins.left() + scroll_area_margins.right())
        
        viewport_width = self.scrollArea.viewport().width()
        available_width = viewport_width - scroll_bar_width - total_margins - safety_margin
        
        num_columns = self.horizontalSlider.value()
        spacing_width = (num_columns - 1) * grid_spacing
        
        if available_width - spacing_width <= 0:
            available_width = viewport_width - total_margins - safety_margin
            spacing_width = 0
            num_columns = 1
            self.horizontalSlider.setValue(1)
            
        item_width = (available_width - spacing_width) // num_columns
        item_width = max(100, min(item_width, 800))
        
        print(f"Viewport width: {viewport_width}px")
        print(f"Available width: {available_width}px")
        print(f"Grid layout: {num_columns} columns, item width: {item_width}px")
        
        for i, file_path in enumerate(self.image_files):
            preview = self.image_previews[file_path]
            print(f"\nProcessing image {i+1}/{len(self.image_files)}")
            widget = self.create_image_widget(preview, item_width, file_path)
            
            # RESTORE PRESERVED TEXT CONTENT AND PROPER HEIGHT
            if file_path in preserved_text and hasattr(widget, 'input_field'):
                restored_text = preserved_text[file_path]
                
                # Ensure the text field width matches the new item width
                widget.input_field.setFixedWidth(item_width)
                
                # Set the text
                widget.input_field.setText(restored_text)
                print(f"[DEBUG] Restored text for {file_path}: '{restored_text}' | New width: {item_width}")
                
                # Apply proper height calculation for restored text
                if restored_text:
                    # Force document to recalculate size with the restored text and new width
                    widget.input_field.document().adjustSize()
                    
                    # Give the document a moment to recalculate with the new width
                    widget.input_field.document().setTextWidth(item_width - 10)  # Account for margins
                    widget.input_field.document().adjustSize()
                    
                    doc_height = int(widget.input_field.document().size().height())
                    margins = widget.input_field.contentsMargins()
                    padding = 8
                    new_height = doc_height + margins.top() + margins.bottom() + padding
                    final_height = max(28, new_height)
                    widget.input_field.setFixedHeight(final_height)
                    print(f"[DEBUG] Applied width {item_width} and height {final_height} for restored text")
            
            row = i // num_columns
            col = i % num_columns
            print(f"Placing at position: row={row}, col={col}")
            self.grid_layout.addWidget(widget, row, col)
            self.image_widgets.append(widget)
            
        print("Layout update completed")

    def open_files(self):
        print("Opening file dialog...")
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.xpm *.jpg *.bmp *.gif, *.tiff *.tif, *.webp)"
        )
        
        print(f"Selected files: {files}")
        
        if files:
            # Clear previous metadata errors and data
            self.metadata_errors.clear()
            
            self.image_files = files
            self.image_previews.clear()
            self.image_metadata.clear()  # Clear metadata storage
            self.selected_images.clear()
            for widget in self.image_widgets:
                widget.setParent(None)
            self.image_widgets.clear()
            
            # Show progress bar
            self.show_progress(len(files))
            
            batch_size = 10
            self.image_files = files
            processed_count = 0
            
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                for file_path in batch:
                    print(f"Creating preview for: {file_path} ({processed_count+1}/{len(files)})")
                    preview = self.create_preview(file_path)
                    if preview is None:
                        print(f"Warning: Could not create preview for {file_path}")
                    
                    processed_count += 1
                    self.update_progress(processed_count)
                
                if i + batch_size >= len(files):
                    print("Processing final batch, updating layout...")
                    self.update_layout()
                    self.hide_progress()  # Hide progress bar when done
                    # Show any metadata errors encountered
                    if self.metadata_errors:
                        QTimer.singleShot(500, self.show_metadata_errors)  # Delay to let UI settle
                else:
                    import gc
                    gc.collect()

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
            # Define supported image extensions
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.xpm', '.tiff', '.tif', '.webp'}
            
            # Find all image files in the folder
            image_files = []
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(filename.lower())
                    if ext in image_extensions:
                        image_files.append(file_path)
            
            print(f"Found {len(image_files)} image files in folder")
            
            if image_files:
                # Clear previous metadata errors and data
                self.metadata_errors.clear()
                
                # Clear existing data
                self.image_files = image_files
                self.image_previews.clear()
                self.image_metadata.clear()  # Clear metadata storage
                self.selected_images.clear()
                for widget in self.image_widgets:
                    widget.setParent(None)
                self.image_widgets.clear()
                
                # Show progress bar
                self.show_progress(len(image_files))
                
                # Process images in batches (same as open_files)
                batch_size = 10
                self.image_files = image_files
                processed_count = 0
                
                for i in range(0, len(image_files), batch_size):
                    batch = image_files[i:i + batch_size]
                    for file_path in batch:
                        print(f"Creating preview for: {file_path} ({processed_count+1}/{len(image_files)})")
                        preview = self.create_preview(file_path)
                        if preview is None:
                            print(f"Warning: Could not create preview for {file_path}")
                        
                        processed_count += 1
                        self.update_progress(processed_count)
                    
                    if i + batch_size >= len(image_files):
                        print("Processing final batch, updating layout...")
                        self.update_layout()
                        self.hide_progress()  # Hide progress bar when done
                        # Show any metadata errors encountered
                        if self.metadata_errors:
                            QTimer.singleShot(500, self.show_metadata_errors)  # Delay to let UI settle
                    else:
                        import gc
                        gc.collect()
            else:
                print("No image files found in the selected folder")

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
            
    def show_settings(self):
        """Create and show the settings dialog"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()
            
    def on_tag_clicked(self, tag_text):
        print(f"[DEBUG] Tag clicked: '{tag_text}' | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's input field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                input_field = widget.input_field
                current_text = input_field.toPlainText().strip()
                print(f"[DEBUG] Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
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
                
                # Prevent real-time sync during programmatic text setting
                input_field._updating = True
                input_field.setText(new_text)
                input_field._updating = False
                print(f"[DEBUG] After append | file_path: {widget.file_path} | new_text: '{new_text}'")
                
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
    
    def on_business_clicked(self, business_button):
        """Handle business button clicks and add business description to selected images with field-level duplicate checking"""
        business_text = business_button.get_full_description()
        business_fields = business_button.get_individual_fields()
        print(f"[DEBUG] Business clicked: '{business_text}' | Fields: {business_fields} | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's input field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                input_field = widget.input_field
                current_text = input_field.toPlainText().strip()
                print(f"[DEBUG] Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
                
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
                    print(f"[DEBUG] All business fields already present, skipping. Duplicates: {duplicate_fields}")
                    continue
                
                # If some fields are missing, add only the missing ones
                if missing_fields:
                    if duplicate_fields:
                        print(f"[DEBUG] Partial duplicates found: {duplicate_fields}. Adding missing fields: {missing_fields}")
                        new_business_text = ", ".join(missing_fields)  # Add commas between fields
                    else:
                        print(f"[DEBUG] No duplicates found. Adding all fields: {missing_fields}")
                        new_business_text = ", ".join(business_fields)  # Add commas between all fields
                else:
                    print(f"[DEBUG] All fields already present, skipping")
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
                
                # Prevent real-time sync during programmatic text setting
                input_field._updating = True
                input_field.setText(new_text)
                input_field._updating = False
                print(f"[DEBUG] After append | file_path: {widget.file_path} | new_text: '{new_text}'")
                
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

    def on_building_clicked(self, building_button):
        """Handle building button clicks and add building description to selected images"""
        building_text = f"{building_button.building_name}, {building_button.street_address}"
        print(f"[DEBUG] Building clicked: '{building_text}' | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's input field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                input_field = widget.input_field
                current_text = input_field.toPlainText().strip()
                print(f"[DEBUG] Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
                
                # Check for duplicates
                if building_text in current_text:
                    print(f"[DEBUG] Building already present, skipping")
                    continue
                
                # Add the building text
                if current_text:
                    if current_text.rstrip().endswith(','):
                        new_text = f"{current_text} {building_text}"
                    else:
                        new_text = f"{current_text}, {building_text}"
                else:
                    new_text = building_text
                
                # Prevent real-time sync during programmatic text setting
                input_field._updating = True
                input_field.setText(new_text)
                input_field._updating = False
                print(f"[DEBUG] After append | file_path: {widget.file_path} | new_text: '{new_text}'")
                
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

    def on_street_clicked(self, street_button):
        """Handle street button clicks and add street name to selected images"""
        street_text = street_button.street_name
        print(f"[DEBUG] Street clicked: '{street_text}' | Selected images: {self.selected_images}")
        if not self.selected_images:
            return

        # Update each selected image's input field
        for widget in self.image_widgets:
            if hasattr(widget, 'file_path') and widget.file_path in self.selected_images:
                input_field = widget.input_field
                current_text = input_field.toPlainText().strip()
                print(f"[DEBUG] Before append | file_path: {widget.file_path} | current_text: '{current_text}'")
                
                # Check for duplicates
                if street_text in current_text:
                    print(f"[DEBUG] Street already present, skipping")
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
                print(f"[DEBUG] After append | file_path: {widget.file_path} | new_text: '{new_text}'")
                
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
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
