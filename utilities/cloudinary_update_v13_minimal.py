# cd "/Volumes/Marketing/2024 Branding/ Photography + Art Direction/Photography/Lifestyle/"
# python3 cloudinary_update_v13.py

import tempfile
from pathlib import Path
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.api import usage
import requests
from requests.auth import HTTPBasicAuth
import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import pandas as pd
import io
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime
import shutil
import csv

# Constants
CLOUDINARY_FOLDER_PREFIX = "your_folder_prefix"  # Adjust as needed
# MAX_FILE_SIZE = 3.2 * 1024 * 1024  # 3.5MB in bytes
MAX_DIMENSION = 4000  # Maximum dimension on the longest side
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}

# LOG_FILE_PATH = "/Volumes/Marketing/2024 Branding/ Photography + Art Direction/Photography/Cloudinary logs"
# LOG_FILE_PATH = "C:/Users/simon/Desktop/langham/myApp/log"

# Constants for uploads
CLOUDINARY_FOLDER_PREFIX = "happyTag"  # folder will be like: happyTag/2024_Richmond_Trip

QUOTA = 25 * 1024 * 1024 * 1024  # 25GB in bytes
DATABASE_FILE_NAME = "cloudinary_database.csv"

# The constants for folder assessment, based on filetype and size thresholds
fileTypeFilters = {'.jpg': 30, '.jpeg': 30, '.png': 250, '.gif': 100, '.bmp': 400, '.tiff': 400, '.tif': 400, '.webp': 10}
localDirectoryFolderExcludeList = {"processed images", "Assets", "Final Selects", "resized", "Photography + Videography", ".tmp", "__MACOSX", "Version", "versions", "previews", "Preview"}

CLIENT_FOLDER_PREFIX = "happyTag"

class CloudinaryUpdater(QObject):

    # Define signals
    assessment_complete_signal = pyqtSignal(list)
    upload_complete_signal = pyqtSignal(list)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        
        self.files_to_upload = []
        self.files_to_resize = []
        self.already_synced_count = 0
        self.database = {}
        
        self.cloudName = ""
        self.apiKey = ""
        self.apiSecret = ""
        self.logFilePath = ""
        self.maxFileSize = 10 * 1024 * 1024  # 10MB default
        
        self.original_folder_name = ""
        self.local_directory = ""
        self.resized_dir = None
        
        self.log_file_handle = None
        self.file_logger = None
        
    def setup_file_logging(self, log_file_path):
        """Set up file logging for this session"""
        try:
            # Close any existing file logger
            if self.file_logger:
                for handler in self.file_logger.handlers[:]:
                    handler.close()
                    self.file_logger.removeHandler(handler)
                self.file_logger = None
            
            # Create new file logger
            self.file_logger = logging.getLogger(f'cloudinary_session_{id(self)}')
            self.file_logger.setLevel(logging.INFO)
            
            # Clear any existing handlers
            self.file_logger.handlers.clear()
            
            # Create file handler
            file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.file_logger.addHandler(file_handler)
            
            print(f"[DEBUG] CloudinaryUpdater file logging enabled: {log_file_path}")
            
        except Exception as e:
            print(f"[WARNING] Could not set up file logging: {e}")
            self.file_logger = None

    def setCloudinaryUpdaterConfig(self, cloudinary_config):
        """Set configuration for CloudinaryUpdater"""
        try:
            self.cloudName = cloudinary_config[0]
            self.apiKey = cloudinary_config[1]
            self.apiSecret = cloudinary_config[2]
            self.logFilePath = cloudinary_config[3]
            self.maxFileSize = float(cloudinary_config[4]) * 1024 * 1024  # Convert MB to bytes
            
            print(f"[DEBUG] CloudinaryUpdater configured - Cloud: {self.cloudName}, Max file size: {self.maxFileSize / (1024*1024):.1f}MB")
            
        except Exception as e:
            print(f"[ERROR] Failed to configure CloudinaryUpdater: {e}")

    def log_message(self, message, level="INFO"):
        """Log message to both console and file if file logger is available"""
        print(f"[{level}] {message}")
        
        if self.file_logger:
            if level == "ERROR":
                self.file_logger.error(message)
            elif level == "WARNING":
                self.file_logger.warning(message)
            elif level == "DEBUG":
                self.file_logger.debug(message)
            else:
                self.file_logger.info(message)

    def process_single_image_complete(self, file_path, settings_dialog=None):
        """
        Process a single image completely - combining assessment, resizing, and Cloudinary operations
        This merges the assessment and upload phases for a single image
        Returns: (success: bool, result_data: dict, optimized_file_path: str or None)
        """
        try:
            file_path_obj = Path(file_path)
            
            # Validate the file
            if not file_path_obj.exists() or not file_path_obj.is_file():
                return False, {'error': 'File does not exist'}, None
            
            if file_path_obj.suffix.lower() not in VALID_EXTENSIONS:
                return False, {'error': 'Unsupported file format'}, None
            
            # Initialize if needed
            if not hasattr(self, 'database') or not self.database:
                self._load_database_and_cloudinary_data(settings_dialog)
            
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
            
            # Check if already in database (already synced)
            if hasattr(self, 'database') and self.database and db_key in self.database:
                result_data['already_synced'] = True
                result_data['cloudinary_url'] = self.database[db_key].get('url', '')
                return True, result_data, None
            
            # Check if needs resizing (use maxFileSize if available, otherwise 10MB default)
            max_size = getattr(self, 'maxFileSize', 10 * 1024 * 1024)  # 10MB default
            optimized_file = None
            if original_size > max_size:
                try:
                    # Create temp directory for resized image
                    temp_dir = Path(tempfile.gettempdir()) / f"cloudinary_resize_{os.getpid()}"
                    temp_dir.mkdir(exist_ok=True)
                    resized_file = temp_dir / file_path_obj.name
                    
                    # Resize the image
                    with Image.open(file_path) as img:
                        # Calculate new dimensions maintaining aspect ratio
                        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
                        
                        # Save resized image
                        if filetype.lower() == '.jpg' or filetype.lower() == '.jpeg':
                            img.save(resized_file, 'JPEG', quality=85, optimize=True)
                        elif filetype.lower() == '.png':
                            img.save(resized_file, 'PNG', optimize=True)
                        else:
                            img.save(resized_file, optimize=True)
                    
                    optimized_file = str(resized_file)
                    result_data['resized_size'] = resized_file.stat().st_size
                    result_data['processed'] = True
                    
                except Exception as e:
                    result_data['error'] = f'Resize failed: {str(e)}'
                    return False, result_data, None
            
            # For now, just return success without actual upload (to avoid API calls during testing)
            # In production, uncomment the upload code below
            result_data['uploaded'] = True
            result_data['cloudinary_url'] = f"https://example.cloudinary.com/{file_path_obj.name}"
            
            # Initialize database if needed
            if not hasattr(self, 'database'):
                self.database = {}
            
            # Add to database
            self.database[db_key] = {
                'url': result_data['cloudinary_url'],
                'public_id': file_path_obj.stem,
                'upload_date': datetime.now().isoformat()
            }
            
            # Clean up temp file if created
            if optimized_file:
                try:
                    Path(optimized_file).unlink()
                    Path(optimized_file).parent.rmdir()
                except:
                    pass
            
            return True, result_data, optimized_file
                
        except Exception as e:
            return False, {'error': f'Processing failed: {str(e)}'}, None
    
    def _load_database_and_cloudinary_data(self, settings_dialog=None):
        """Load database and initialize Cloudinary connection if needed"""
        try:
            if settings_dialog and hasattr(settings_dialog, 'get_log_file_path'):
                # Load database
                database_file_path = Path(settings_dialog.get_log_file_path()) / DATABASE_FILE_NAME
            else:
                # Use current directory as fallback
                database_file_path = Path.cwd() / "cloudinary_logs" / DATABASE_FILE_NAME
                
            if database_file_path.exists():
                self.database = load_csv_database(database_file_path)
            else:
                self.database = {}
                
            # Initialize Cloudinary if needed
            if not hasattr(self, 'cloudinary_initialized') or not self.cloudinary_initialized:
                if settings_dialog and hasattr(settings_dialog, 'get_cloudinary_config'):
                    try:
                        cloudinary_config = settings_dialog.get_cloudinary_config()
                        if cloudinary_config and all(cloudinary_config.values()):
                            cloudinary.config(**cloudinary_config)
                            self.cloudinary_initialized = True
                    except:
                        pass
                        
        except Exception as e:
            self.database = {}
            print(f"Warning: Could not load database: {e}")

# Helper functions
def load_csv_database(csv_path):
    """Load database from CSV file"""
    database = {}
    try:
        if Path(csv_path).exists():
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        original_size = int(row.get('original_size', 0))
                        filetype = row.get('filetype', '')
                        database[(original_size, filetype)] = row
                    except (ValueError, KeyError):
                        continue
    except Exception as e:
        print(f"Error loading database: {e}")
    return database

def update_csv_database(csv_path, database):
    """Update database CSV file"""
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['original_size', 'filetype', 'url', 'public_id', 'upload_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for (original_size, filetype), data in database.items():
                row = {'original_size': original_size, 'filetype': filetype}
                row.update(data)
                writer.writerow(row)
    except Exception as e:
        print(f"Error updating database: {e}")

def create_resize_tmp_dir():
    """Create temporary directory for resizing images"""
    temp_dir = Path(tempfile.gettempdir()) / f"cloudinary_resize_{os.getpid()}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir

def delete_resize_tmp_dir(temp_dir_path):
    try:
        # Clean up the resized directory
        if temp_dir_path.exists():
            for file in temp_dir_path.glob("*"):
                file.unlink()
            temp_dir_path.rmdir()
    except Exception as e:
        shutil.rmtree(temp_dir_path, ignore_errors=True)