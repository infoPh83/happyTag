# utilities/image_assessment.py
"""
Image Assessment System for HappyTag
Integrates the assessment phase functionality from the Cloudinary app
Performs image processing, resizing, validation, and Cloudinary sync checking during loading
"""

import os
import sys
import time
import tempfile
import csv
from pathlib import Path
from datetime import datetime
from PIL import Image
from io import BytesIO
import logging
from PyQt5.QtCore import QObject, pyqtSignal

# Constants from Cloudinary system
MAX_DIMENSION = 4000  # Maximum dimension on the longest side
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
SUPPORTED_FORMATS = {'JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'WEBP'}
RESIZING_TIME_LIMIT = 20  # Set time limit in seconds
DEFAULT_MAX_FILE_SIZE = 3.2 * 1024 * 1024  # 3.2MB in bytes
DATABASE_FILE_NAME = "cloudinary_database.csv"
LOG_NAME_PREFIX = "happytag_assessment_"

class ImageAssessment(QObject):
    """
    Image Assessment System for HappyTag
    Performs comprehensive image analysis, resizing, and Cloudinary sync checking
    Based on the original Cloudinary assessment_phase logic
    """
    
    # Signals for progress updates
    assessment_progress = pyqtSignal(int)  # Progress percentage (0-100)
    assessment_status = pyqtSignal(str)    # Status message
    image_processed = pyqtSignal(str, dict)  # file_path, assessment_result
    assessment_complete = pyqtSignal(dict)   # Final assessment summary
    
    def __init__(self, max_file_size=None, cloudinary_updater=None, main_app=None):
        super().__init__()
        self.max_file_size = max_file_size or DEFAULT_MAX_FILE_SIZE
        self.cloudinary_updater = cloudinary_updater
        self.main_app = main_app  # Reference to main app for accessing cached data
        self.assessment_data = {}
        self.temp_dir = None
        self.processed_count = 0
        self.total_count = 0
        
        # Logging setup
        self.log_file_handle = None
        self.log_folder = None
        
        # Database and Cloudinary data
        self.database = {}
        self.cloudinary_files = []
        
        # Assessment results (matching original Cloudinary logic)
        self.files_to_upload = []      # Files ready to upload (already resized)
        self.files_to_resize = []      # Files that need resizing before upload
        self.already_synced_count = 0  # Files already on Cloudinary
        self.total_original_size = 0   # Total size of original files
        self.total_upload_size = 0     # Total size of files to upload
        
    def setup_logging(self, log_folder):
        """Setup logging for assessment phase"""
        try:
            self.log_folder = log_folder
            if not log_folder:
                print("[WARNING] No log folder specified - assessment logging disabled")
                return
            
            # Create log folder if it doesn't exist
            log_path = Path(log_folder)
            log_path.mkdir(parents=True, exist_ok=True)
            
            # Create log filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = f"{LOG_NAME_PREFIX}{timestamp}.txt"
            log_file_path = log_path / log_filename
            
            # Open log file for writing
            self.log_file_handle = log_file_path.open("w", encoding="utf-8")
            
            # Write header
            session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_file_handle.write(f"=== HappyTag Assessment Session ===\n")
            self.log_file_handle.write(f"Session started: {session_start}\n")
            self.log_file_handle.write(f"Log file: {log_file_path}\n")
            self.log_file_handle.write("=" * 50 + "\n\n")
            self.log_file_handle.flush()
            
            print(f"[DEBUG] Assessment logging enabled: {log_file_path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to setup assessment logging: {e}")
            self.log_file_handle = None
    
    def log_message(self, message, level="INFO"):
        """Log message to both console and log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        # Log to console
        print(f"[ASSESSMENT {level}] {message}")
        
        # Log to file if handle exists
        if self.log_file_handle:
            try:
                self.log_file_handle.write(f"{formatted_message}\n")
                self.log_file_handle.flush()
            except Exception as e:
                print(f"[ERROR] Failed to write to log file: {e}")
    
    def close_logging(self):
        """Close log file handle"""
        if self.log_file_handle:
            try:
                session_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_file_handle.write(f"\n\nSession ended: {session_end}\n")
                self.log_file_handle.write("=" * 50 + "\n")
                self.log_file_handle.close()
                print("[DEBUG] Assessment logging closed")
            except Exception as e:
                print(f"[ERROR] Failed to close log file: {e}")
            finally:
                self.log_file_handle = None
        
    def process_single_image_with_cloudinary_logic(self, file_path, settings_dialog=None):
        """
        Process a single image with full ImageAssessment Cloudinary logic
        Returns: (success: bool, result_data: dict, optimized_file: str or None)
        
        This method applies all the sophisticated Cloudinary sync verification,
        database checking, and resizing logic from assess_images to a single file
        """
        try:
            file_path_obj = Path(file_path)
            
            # Validate the file
            if not self._is_valid_image_file(file_path):
                return False, {'error': 'Invalid image file'}, None
            
            # Initialize if needed
            cloudinary_available = self._initialize_cloudinary_data(settings_dialog)
            if not cloudinary_available:
                # Fallback to basic processing without Cloudinary
                return self._process_single_image_basic(file_path_obj)
            
            # Get file details
            original_size = file_path_obj.stat().st_size
            filetype = file_path_obj.suffix.lower()
            db_key = (original_size, filetype)
            
            result_data = {
                'original_file': str(file_path),
                'original_size': original_size,
                'filetype': filetype,
                'processed': False,
                'uploaded': False,
                'already_synced': False,
                'resized_size': None,
                'cloudinary_url': None,
                'error': None
            }
            
            print(f"[DEBUG] Processing {file_path_obj.name}: {original_size} bytes, {filetype}")
            
            # CORE CLOUDINARY LOGIC: Check if file is in database
            if self._is_file_in_database(original_size, filetype):
                print(f"[DEBUG] File found in database: {file_path_obj.name}")
                
                # Get resized size from database
                resized_size = self.database[db_key]['resized_size']
                result_data['resized_size'] = resized_size
                
                # CRITICAL: Check if file is synced with Cloudinary
                if self._is_file_synced(file_path_obj, resized_size):
                    print(f"[DEBUG] File SYNCED with Cloudinary: {file_path_obj.name}")
                    result_data['already_synced'] = True
                    result_data['cloudinary_url'] = self.database[db_key].get('url', '')
                    return True, result_data, None
                else:
                    print(f"[DEBUG] File in database but NOT synced with Cloudinary: {file_path_obj.name}")
                    # Will need to be re-uploaded (resized file should exist)
                    result_data['uploaded'] = True  # Placeholder for now
                    result_data['cloudinary_url'] = f"https://res.cloudinary.com/example/{file_path_obj.name}"
                    return True, result_data, None
            else:
                print(f"[DEBUG] File NOT in database, needs processing: {file_path_obj.name}")
                
                # Create temp directory if needed
                if not self.temp_dir:
                    import tempfile
                    self.temp_dir = Path(tempfile.mkdtemp(prefix="happytag_single_"))
                
                # SOPHISTICATED RESIZING: Use the ImageAssessment resize logic
                resized_buffer = self._resize_image_to_fit(file_path_obj)
                if resized_buffer is None:
                    return False, {'error': 'Failed to resize image'}, None
                
                # Save resized file to temp directory
                resized_file_path = self.temp_dir / file_path_obj.name
                with open(resized_file_path, 'wb') as f:
                    f.write(resized_buffer.getvalue())
                
                # Update database with resized size
                resized_size = resized_file_path.stat().st_size
                result_data['resized_size'] = resized_size
                result_data['processed'] = True
                
                # Add to database
                self.database[db_key] = {
                    'file_name': file_path_obj.name,
                    'original_size': original_size,
                    'resized_size': resized_size,
                    'filetype': filetype,
                    'url': f"https://res.cloudinary.com/example/{file_path_obj.name}"  # Placeholder
                }
                
                # CRITICAL: Check if resized file is already synced with Cloudinary
                if self._is_file_synced(file_path_obj, resized_size):
                    print(f"[DEBUG] New file already SYNCED with Cloudinary: {file_path_obj.name}")
                    result_data['already_synced'] = True
                    result_data['cloudinary_url'] = self.database[db_key]['url']
                else:
                    print(f"[DEBUG] New file NOT synced, needs upload: {file_path_obj.name}")
                    result_data['uploaded'] = True  # Placeholder for actual upload
                    result_data['cloudinary_url'] = self.database[db_key]['url']
                
                # Save database
                self._save_database()
                
                return True, result_data, str(resized_file_path)
                
        except Exception as e:
            print(f"[ERROR] Single image processing failed for {file_path}: {e}")
            return False, {'error': f'Processing failed: {str(e)}'}, None
    
    def _process_single_image_basic(self, file_path_obj):
        """Fallback processing when Cloudinary is not available"""
        try:
            original_size = file_path_obj.stat().st_size
            result_data = {
                'original_file': str(file_path_obj),
                'original_size': original_size,
                'filetype': file_path_obj.suffix.lower(),
                'processed': False,
                'uploaded': False,
                'already_synced': False,
                'resized_size': None,
                'cloudinary_url': None,
                'error': None
            }
            
            # Simple processing without Cloudinary
            if original_size > self.max_file_size:
                # Create temp directory if needed
                if not self.temp_dir:
                    import tempfile
                    self.temp_dir = Path(tempfile.mkdtemp(prefix="happytag_basic_"))
                
                # Resize image
                resized_buffer = self._resize_image_to_fit(file_path_obj)
                if resized_buffer:
                    resized_file_path = self.temp_dir / file_path_obj.name
                    with open(resized_file_path, 'wb') as f:
                        f.write(resized_buffer.getvalue())
                    
                    result_data['resized_size'] = resized_file_path.stat().st_size
                    result_data['processed'] = True
                    return True, result_data, str(resized_file_path)
                else:
                    return False, {'error': 'Failed to resize image'}, None
            else:
                # No resizing needed
                return True, result_data, None
                
        except Exception as e:
            return False, {'error': f'Basic processing failed: {str(e)}'}, None

    def assess_images(self, image_files, settings_dialog=None):
        """
        Main assessment function that processes a list of image files
        Performs the equivalent of Cloudinary's assessment_phase with full logic
        """
        self.total_count = len(image_files)
        self.processed_count = 0
        self.assessment_data = {}
        
        # Reset counters
        self.files_to_upload = []
        self.files_to_resize = []
        self.already_synced_count = 0
        self.total_original_size = 0
        self.total_upload_size = 0
        
        # Setup logging if settings available
        if settings_dialog:
            try:
                cloudinary_settings = settings_dialog.get_cloudinary_settings()
                if cloudinary_settings and cloudinary_settings.get('log_folder'):
                    self.setup_logging(cloudinary_settings['log_folder'])
                    self.log_message(f"Starting assessment of {len(image_files)} images")
                else:
                    print("[WARNING] No log folder configured - assessment logging disabled")
            except Exception as e:
                print(f"[WARNING] Failed to setup assessment logging: {e}")
        
        # Create temporary directory for processed images
        self.temp_dir = Path(tempfile.mkdtemp(prefix="happytag_assessment_"))
        self.log_message(f"Created temporary directory: {self.temp_dir}")
        
        self.assessment_status.emit(f"Starting assessment of {self.total_count} images...")
        
        # Initialize database and Cloudinary data (returns True/False)
        cloudinary_available = self._initialize_cloudinary_data(settings_dialog)
        if not cloudinary_available:
            # If Cloudinary is not configured, just do basic image processing
            self.log_message("Cloudinary not available - falling back to basic assessment")
            return self._basic_image_assessment(image_files)
        
        # Phase 1: Initial assessment - categorize images (original logic)
        files_to_be_resized_in_assessment = []
        valid_files = []
        
        self.assessment_status.emit(f"Checking {len(image_files)} images against database and Cloudinary...")
        
        for i, file_path in enumerate(image_files):
            try:
                if not self._is_valid_image_file(file_path):
                    continue
                    
                valid_files.append(file_path)
                file_path_obj = Path(file_path)
                
                # Get file details
                original_size = file_path_obj.stat().st_size
                filetype = file_path_obj.suffix.lower()
                
                print(f"[DEBUG] Assessing {file_path_obj.name}: {original_size} bytes, {filetype}")
                self.log_message(f"Assessing {file_path_obj.name}: {original_size} bytes, {filetype}")
                
                # Check if file is in database (CORE CLOUDINARY LOGIC)
                if self._is_file_in_database(original_size, filetype):
                    print(f"[DEBUG] File found in database: {file_path_obj.name}")
                    self.log_message(f"File found in database: {file_path_obj.name}")
                    
                    # FILE IS IN DATABASE - get resized size and check Cloudinary sync
                    db_key = (original_size, filetype)
                    resized_size = self.database[db_key]['resized_size']
                    
                    if not self._is_file_synced(file_path_obj, resized_size):
                        print(f"[DEBUG] File in database but NOT synced with Cloudinary: {file_path_obj.name}")
                        self.log_message(f"File in database but NOT synced with Cloudinary: {file_path_obj.name}")
                        # FILE IS NOT SYNCED WITH CLOUDINARY - will be resized and uploaded later
                        self.files_to_resize.append(file_path)
                        self.total_upload_size += resized_size
                        self.total_original_size += original_size
                    else:
                        print(f"[DEBUG] File in database and SYNCED with Cloudinary: {file_path_obj.name}")
                        self.log_message(f"File in database and SYNCED with Cloudinary: {file_path_obj.name}")
                        # FILE IS SYNCED WITH CLOUDINARY - skip
                        self.already_synced_count += 1
                else:
                    print(f"[DEBUG] File NOT in database, needs processing: {file_path_obj.name}")
                    self.log_message(f"File NOT in database, needs processing: {file_path_obj.name}")
                    # FILE NOT IN DATABASE - resize now to get size for Cloudinary comparison
                    files_to_be_resized_in_assessment.append(file_path)
                
                # Update progress
                progress = int((i + 1) / len(image_files) * 50)  # First phase is 50% of progress
                self.assessment_progress.emit(progress)
                
            except Exception as e:
                print(f"[ERROR] Failed to assess {file_path}: {e}")
                self.log_message(f"Failed to assess {file_path}: {e}", "ERROR")
                continue
        
        # Phase 2: Process files that need resizing now (original logic)
        if files_to_be_resized_in_assessment:
            self.assessment_status.emit(f"Processing {len(files_to_be_resized_in_assessment)} new images...")
            self.log_message(f"Processing {len(files_to_be_resized_in_assessment)} new images that need resizing")
            
            for i, file_path in enumerate(files_to_be_resized_in_assessment):
                try:
                    file_path_obj = Path(file_path)
                    self.assessment_status.emit(f"Processing {file_path_obj.name} ({i+1}/{len(files_to_be_resized_in_assessment)})")
                    
                    # Resize the image (CORE CLOUDINARY LOGIC)
                    resized_buffer = self._resize_image_to_fit(file_path_obj)
                    if resized_buffer is None:
                        print(f"[WARNING] Failed to resize {file_path_obj.name}")
                        continue
                    
                    # Save resized file to temp directory
                    resized_file_path = self.temp_dir / file_path_obj.name
                    with open(resized_file_path, 'wb') as f:
                        f.write(resized_buffer.getvalue())
                    
                    # Update database with resized size (CORE CLOUDINARY LOGIC)
                    original_size = file_path_obj.stat().st_size
                    resized_size = resized_file_path.stat().st_size
                    filetype = file_path_obj.suffix.lower()
                    
                    db_key = (original_size, filetype)
                    self.database[db_key] = {
                        'file_name': file_path_obj.name,
                        'original_size': original_size,
                        'resized_size': resized_size,
                        'filetype': filetype
                    }
                    
                    print(f"[DEBUG] Added to database: {file_path_obj.name}, original: {original_size}, resized: {resized_size}")
                    
                    # Check if resized file is already synced with Cloudinary (CORE CLOUDINARY LOGIC)
                    if not self._is_file_synced(file_path_obj, resized_size):
                        print(f"[DEBUG] New file NOT synced with Cloudinary: {file_path_obj.name}")
                        # FILE NOT SYNCED - add to upload queue
                        self.files_to_upload.append(str(resized_file_path))
                        self.total_upload_size += resized_size
                        self.total_original_size += original_size
                    else:
                        print(f"[DEBUG] New file already SYNCED with Cloudinary: {file_path_obj.name}")
                        # FILE ALREADY SYNCED - skip
                        self.already_synced_count += 1
                    
                    # Update progress
                    progress = 50 + int((i + 1) / len(files_to_be_resized_in_assessment) * 50)
                    self.assessment_progress.emit(progress)
                    
                except Exception as e:
                    print(f"[ERROR] Failed to process {file_path}: {e}")
                    continue
        
        # Save updated database
        self._save_database()
        self.log_message("Assessment database saved")
        
        # Compile final assessment results
        assessment_summary = {
            'total_files': len(valid_files),
            'files_to_upload': len(self.files_to_upload),
            'files_to_resize': len(self.files_to_resize),
            'already_synced': self.already_synced_count,
            'total_original_size': self.total_original_size,
            'total_upload_size': self.total_upload_size,
            'valid_files': valid_files,
            'temp_directory': str(self.temp_dir),
            'cloudinary_enabled': True
        }
        
        self.assessment_status.emit("Assessment complete")
        self.assessment_progress.emit(100)
        self.assessment_complete.emit(assessment_summary)
        
        print(f"[DEBUG] Assessment complete:")
        print(f"  Total files: {len(valid_files)}")
        print(f"  Already synced: {self.already_synced_count}")
        print(f"  Need upload: {len(self.files_to_upload)}")
        print(f"  Need resize: {len(self.files_to_resize)}")
        
        # Log final summary
        self.log_message("=== ASSESSMENT SUMMARY ===")
        self.log_message(f"Total files processed: {len(valid_files)}")
        self.log_message(f"Files already synced: {self.already_synced_count}")
        self.log_message(f"Files to upload: {len(self.files_to_upload)}")
        self.log_message(f"Files to resize: {len(self.files_to_resize)}")
        self.log_message(f"Total original size: {self.total_original_size:,} bytes")
        self.log_message(f"Total upload size: {self.total_upload_size:,} bytes")
        
        # Close logging
        self.close_logging()
        
        return assessment_summary
    
    def _initialize_cloudinary_data(self, settings_dialog=None):
        """Initialize database and Cloudinary files data"""
        try:
            # Load database
            if settings_dialog:
                cloudinary_settings = settings_dialog.get_cloudinary_settings()
                if cloudinary_settings and cloudinary_settings.get('log_folder'):
                    log_folder = cloudinary_settings['log_folder']
                    database_path = Path(log_folder) / DATABASE_FILE_NAME
                else:
                    database_path = Path("logs") / DATABASE_FILE_NAME
            else:
                database_path = Path("logs") / DATABASE_FILE_NAME
            
            self.database = self._load_csv_database(database_path)
            print(f"[DEBUG] Loaded database with {len(self.database)} entries from {database_path}")
            self.log_message(f"Loaded database with {len(self.database)} entries from {database_path}")
            
            # Get Cloudinary files list from cache instead of making API calls
            if self.cloudinary_updater and self.main_app and hasattr(self.main_app, 'cloudinary_files_cache'):
                # Use cached data from main app (retrieved once at startup)
                self.cloudinary_files = self.main_app.cloudinary_files_cache
                print(f"[DEBUG] Using cached Cloudinary files list: {len(self.cloudinary_files)} files")
                self.log_message(f"Using cached Cloudinary files list: {len(self.cloudinary_files)} files")
            elif self.cloudinary_updater:
                print("[DEBUG] No cached Cloudinary files available, falling back to API call")
                try:
                    # Fallback to API call if cache not available (should rarely happen)
                    import cloudinary.api
                    
                    # Use the same logic as the original list_all_files function
                    all_files = []
                    next_cursor = None
                    
                    while True:
                        resources = cloudinary.api.resources(
                            type="upload", max_results=100, next_cursor=next_cursor
                        )
                        all_files.extend(resources['resources'])
                        next_cursor = resources.get('next_cursor')
                        if not next_cursor:
                            break
                    
                    self.cloudinary_files = all_files
                    print(f"[DEBUG] Retrieved {len(self.cloudinary_files)} files from Cloudinary API (fallback)")
                    self.log_message(f"Retrieved {len(self.cloudinary_files)} files from Cloudinary API (fallback)")
                except Exception as e:
                    print(f"[WARNING] Could not retrieve Cloudinary files: {e}")
                    self.log_message(f"Could not retrieve Cloudinary files: {e}", "WARNING")
                    self.cloudinary_files = []
            else:
                print("[DEBUG] No CloudinaryUpdater available, skipping Cloudinary sync check")
                self.log_message("No CloudinaryUpdater available, skipping Cloudinary sync check", "WARNING")
                self.cloudinary_files = []
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize Cloudinary data: {e}")
            self.log_message(f"Failed to initialize Cloudinary data: {e}", "ERROR")
            return False
    
    def _basic_image_assessment(self, image_files):
        """Fallback to basic image assessment without Cloudinary integration"""
        print("[DEBUG] Performing basic image assessment (no Cloudinary)")
        self.log_message("Performing basic image assessment (no Cloudinary)", "WARNING")
        
        valid_files = []
        for file_path in image_files:
            if self._is_valid_image_file(file_path):
                valid_files.append(file_path)
        
        self.log_message(f"Basic assessment complete: {len(valid_files)} valid files found")
        
        assessment_summary = {
            'total_files': len(valid_files),
            'valid_files': valid_files,
            'cloudinary_enabled': False,
            'temp_directory': str(self.temp_dir) if self.temp_dir else None
        }
        
        # Close logging
        self.close_logging()
        
        self.assessment_complete.emit(assessment_summary)
        return assessment_summary
    
    def _is_file_in_database(self, original_size, filetype):
        """Check if file exists in database (from original Cloudinary logic)"""
        db_key = (original_size, filetype)
        return db_key in self.database
    
    def _is_file_synced(self, file_path, resized_size):
        """Check if file is already synced with Cloudinary (from original Cloudinary logic)"""
        if not self.cloudinary_files:
            return False
            
        filetype = file_path.suffix.lower().lstrip('.')  # Remove leading dot
        
        for cloudinary_file in self.cloudinary_files:
            cloudinary_size = int(cloudinary_file.get('bytes', 0))
            cloudinary_format = cloudinary_file.get('format', '').lower()
            
            if cloudinary_size == resized_size and cloudinary_format == filetype:
                return True
        
        return False
    
    def _is_valid_image_file(self, file_path):
        """Check if file is a valid image file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                return False
            
            extension = file_path.suffix.lower()
            return extension in VALID_EXTENSIONS
        except Exception:
            return False
    
    def _resize_image_to_fit(self, file_path):
        """
        Resize an image to fit within specified dimensions and file size
        Based on the original Cloudinary resize_image_to_fit function
        """
        try:
            with Image.open(file_path) as img:
                start_time = time.time()
                iterations = 0
                
                original_format = img.format
                
                if original_format not in SUPPORTED_FORMATS:
                    print(f"[WARNING] Unsupported format: {file_path.name} ({original_format})")
                    return None
                
                # Convert palette mode GIFs to RGB
                if original_format == 'GIF' and img.mode == 'P':
                    img = img.convert('RGB')
                
                original_width, original_height = img.size
                
                # Resize if dimensions are too large
                if max(original_width, original_height) > MAX_DIMENSION:
                    if original_width > original_height:
                        new_width = MAX_DIMENSION
                        new_height = int((MAX_DIMENSION / original_width) * original_height)
                    else:
                        new_height = MAX_DIMENSION
                        new_width = int((MAX_DIMENSION / original_height) * original_width)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                quality = 95
                
                while True:
                    buffer = BytesIO()
                    image_format = original_format.upper() if original_format else 'JPEG'
                    
                    # Save with appropriate format
                    if image_format in ['JPG', 'JPEG']:
                        image_format = 'JPEG'
                        img.save(buffer, format=image_format, quality=quality)
                    elif image_format == 'PNG':
                        img.save(buffer, format=image_format, optimize=True)
                    elif image_format == 'TIFF':
                        img.save(buffer, format=image_format, compression="tiff_deflate")
                    elif image_format == 'GIF':
                        image_format = 'JPEG'
                        img.save(buffer, format=image_format, quality=quality)
                    else:
                        image_format = 'JPEG'
                        img.save(buffer, format=image_format, quality=quality)
                    
                    # Check if optimization is complete
                    buffer_size = buffer.tell()
                    original_size = file_path.stat().st_size
                    
                    if buffer_size <= self.max_file_size and buffer_size <= original_size:
                        buffer.seek(0)
                        return buffer
                    
                    # Check time limit
                    elapsed_time = time.time() - start_time
                    if elapsed_time > RESIZING_TIME_LIMIT:
                        print(f"[WARNING] Time limit exceeded for {file_path.name}: {elapsed_time:.2f} seconds")
                        break
                    
                    iterations += 1
                    
                    # Adjust optimization parameters (from original logic)
                    size_ratio = buffer_size / self.max_file_size
                    if size_ratio > 2:
                        resize_factor = 0.5
                    elif size_ratio > 1.5:
                        resize_factor = 0.7
                    else:
                        resize_factor = 0.9
                    
                    # Apply optimization
                    if image_format == 'PNG':
                        new_width = int(img.width * resize_factor)
                        new_height = int(img.height * resize_factor)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    else:
                        if quality > 60:
                            quality -= 5
                        else:
                            new_width = int(img.width * resize_factor)
                            new_height = int(img.height * resize_factor)
                            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
        except Exception as e:
            print(f"[ERROR] Failed to resize {file_path}: {e}")
            return None
    
    def _load_csv_database(self, csv_path):
        """Load the CSV database (from original Cloudinary logic)"""
        database = {}
        if csv_path.exists():
            try:
                with open(csv_path, mode='r', newline='') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        try:
                            key = (int(row['original_size']), row['filetype'])
                            database[key] = {
                                'file_name': row['file_name'],
                                'original_size': int(row['original_size']),
                                'resized_size': int(row['resized_size']) if row['resized_size'] else None,
                                'filetype': row['filetype']
                            }
                        except (KeyError, ValueError) as e:
                            print(f"[WARNING] Invalid database row: {e}")
            except Exception as e:
                print(f"[ERROR] Failed to load database: {e}")
        return database
    
    def _save_database(self):
        """Save the updated database (from original Cloudinary logic)"""
        try:
            # Determine database path
            database_path = Path("logs") / DATABASE_FILE_NAME
            database_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(database_path, mode='w', newline='') as file:
                fieldnames = ['file_name', 'original_size', 'resized_size', 'filetype']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for data in self.database.values():
                    writer.writerow(data)
            
            print(f"[DEBUG] Saved database with {len(self.database)} entries to {database_path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to save database: {e}")
    
    def get_assessment_data(self, file_path=None):
        """Get assessment data for a specific file or all files"""
        if file_path:
            return self.assessment_data.get(str(file_path))
        return self.assessment_data
    
    def cleanup(self):
        """Clean up temporary files and directories"""
        if self.temp_dir and self.temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                print(f"[DEBUG] Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"[WARNING] Failed to clean up temporary directory: {e}")
    
    def convert_bytes(self, size):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
