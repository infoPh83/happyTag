# cd "/Volumes/Marketing/2024 Branding/ Photography + Art Direction/Photography/Lifestyle/"
# python3 cloudinary_update_v13.py

import tempfile
from pathlib import Path
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.api import usage
import requests
from .debug_utils import debug_cloudinary, debug_business, debug_errors
from requests.auth import HTTPBasicAuth
import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from io import BytesIO
import re
import csv
from datetime import datetime
import logging
import shutil
import time



# Constants
# MAX_FILE_SIZE = 3.2 * 1024 * 1024  # 3.5MB in bytes
MAX_DIMENSION = 4000  # Maximum dimension on the longest side
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.webp'}
SUPPORTED_FORMATS = {'JPEG', 'PNG', 'GIF', 'TIFF', 'WEBP'}
UNSUPPORTED_EXTENSIONS = {'.bmp', '.psd'}  # Known image formats not currently supported
# LOG_FILE_PATH = "/Volumes/Marketing/2024 Branding/ Photography + Art Direction/Photography/Cloudinary logs"
# LOG_FILE_PATH = "C:/Users/simon/Desktop/langham/myApp/log"
CLOUDINARY_FOLDER_PREFIX = "Uploaded"
FOLDER_MODE = 1 # sync_files MODE(s)
FILES_MODE  = 2 # sync_files MODE(s)
SINGLE_FOLDER_MODE = 3 # sync_files MODE(s) - non-recursive folder scan
LOG_NAME = "CloudinaryLog "
QUOTA = 25 * 1024 * 1024 * 1024  # 25GB in bytes
BATCH_SIZE = 10  # Number of files to upload before deleting temporary files
DATABASE_FILE_NAME = "cloudinary_database.csv"
resized_count = 0
CREDITS_MAX = 25  # 1 Cloudinary credit equals 1k Transformations, 1Gb Storage, 1 Gb Bandwidth
# adding time management
RESIZING_TIME_LIMIT = 20  # Set time limit in seconds

# Debug mode
DEBUG = False  # Set to False to disable detailed debugging logs

# Global Variables
total_original_size = 0









# utilities/cloudinary_update_v13.py
from PyQt5.QtCore import QObject, pyqtSignal
from utilities.session_logger import get_session_logger, log_session_message

class CloudinaryUpdater(QObject):
    # Define signals to update the UI
    update_ui_signal = pyqtSignal(str)  # Emits a string (e.g., status message)
    beginning_signal = pyqtSignal(list)  # Emits a list containing multiple variables
    setPreviewImages_signal = pyqtSignal(list)  # Emits a list containing multiple variables
    assessment_complete_signal = pyqtSignal(list)  # Signal to indicate assessment phase is complete
    update_assessment_bar_signal = pyqtSignal(int)  # Signal to update the progress bar
    update_assessment_file_count = pyqtSignal(int)  # Signal to update assessment file count
    # upload phase signals
    updatePreviewImage_signal = pyqtSignal(str)
    updateResizeInUploadProgressBar_signal = pyqtSignal(int)
    updateProgressBar_signal = pyqtSignal(int)
    updateUiUploadStatus_signal = pyqtSignal(str)
    setUploadPreviewImage_signal = pyqtSignal(str)
    uploadStarting_signal = pyqtSignal(bool)
    upload_complete_signal = pyqtSignal(list)  # Signal to indicate upload is complete

    currentTransformations = 0
    currentBandwidth = 0
    currentStorageCredits = 0

    # upload phase
    update_uploadResizeCount_signal = pyqtSignal(str)
    # update_uploadResizeProgressBar_signal = pyqtSignal(int)  # Signal to update the progress bar

    def __init__(self):
        super().__init__()
        self.files_to_upload = []
        self.files_to_resize = []
        self.total_upload_size = 0
        self.already_synced_count = 0
        self.local_directory = ""
        self.database = {}
        self.cloudinary_files = []
        self.resized_dir = Path()
        self.mode = 0
        self.original_folder_name = ""  # Store the original folder name for SINGLE_FOLDER_MODE
        self.log_file_handle = None  # Store log file handle for consistent logging
        self.file_logger = None  # Store dedicated file logger
        
        self.logFilePath = ""
        self.maxFileSize = 0
        self.cloudName = ""
        self.apiKey = ""
        self.apiSecret = ""
    
    def setup_file_logging(self, log_file_path):
        """Setup file logging for CloudinaryUpdater"""
        try:
            # Create a dedicated logger for this session
            logger_name = f"cloudinary_upload_{id(self)}"
            self.file_logger = logging.getLogger(logger_name)
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
            
            # Prevent propagation to root logger to avoid console duplication
            self.file_logger.propagate = False
            
            debug_cloudinary(f"CloudinaryUpdater file logging enabled: {log_file_path}")
            
        except Exception as e:
            debug_errors(f"Failed to setup CloudinaryUpdater file logging: {e}")
            self.file_logger = None

    def setCloudinaryUpdaterConfig(self, cloudinary_config):
        debug_cloudinary(f"CloudinaryUpdater initialization with config: {cloudinary_config}")
        self.logFilePath = cloudinary_config[0]
        self.cloudName = cloudinary_config[1]
        self.apiKey = cloudinary_config[2]
        self.apiSecret = cloudinary_config[3]
        self.maxFileSize = float(cloudinary_config[4]) * 1024 * 1024  # Convert MB to bytes

        # Dynamically set the Cloudinary configuration
        cloudinary.config(
            cloud_name=self.cloudName,
            api_key=self.apiKey,
            api_secret=self.apiSecret
        )

        debug_cloudinary(f"CloudinaryUpdater variables: {self.logFilePath}, {self.cloudName}, {self.apiKey}, *****, {self.maxFileSize}")

    def log_message(self, message, level="INFO"):
        """Log message to both console and log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        # Log to console using standard logging
        if level == "ERROR":
            logging.error(message)
        elif level == "WARNING":
            logging.warning(message)
        else:
            logging.info(message)
        
        # Log to session logger (preferred method)
        log_session_message(message, "UPLOAD")
        
        # Log to dedicated file logger if available (fallback)
        if self.file_logger:
            if level == "ERROR":
                self.file_logger.error(message)
            elif level == "WARNING":
                self.file_logger.warning(message)
            else:
                self.file_logger.info(message)
        
        # Legacy: Log to file handle if it exists (for backward compatibility)
        if self.log_file_handle:
            try:
                self.log_file_handle.write(f"\n{formatted_message}")
                self.log_file_handle.flush()
            except Exception as e:
                debug_errors(f"Failed to write to legacy log file: {e}")
            self.log_file_handle.flush()  # Ensure immediate write

    def sync_files_signal(self, folder, mode):
        """
        Simulate a long-running task and emit updates to the UI.
        """
        self.mode = mode
        self.local_directory = folder
        self.sync_files(folder, mode)

    def cloud_status(self):
        """Get Cloudinary status and emit the details to the UI."""
        
        data = get_cloudinary_status(self)
        
        # data contains error message if status retrieval failed
        self.beginning_signal.emit(data)
        

        if data[0] == True:  # Check if the status retrieval was successful
            self.update_ui_signal.emit("Cloudinary account connected")  # Emit the update_ui_signal

            self.log_message(f"SETTING TRANSFORMATION CREDITS: {data[9]}")
            self.currentStorageCredits = data[8]  # Update the current storage value
            self.currentTransformations = data[9]  # Update the current transformations value
            self.currentBandwidth = data[10]  # Update the current bandwidth value
    


    def updateStatusLabel(self, message):
        self.update_ui_signal.emit(message)

    def sync_files(self, local_directory, sync_files_mode):
        self.log_message(f"SYNC_FILES")
        self.log_message(f"--- Cloudinary upload v13 --- CloudinaryUpdater with {sync_files_mode}")
        self.log_message(f"Uploading all images  : {local_directory}")
        
        # Ensure session logging is available and get log folder for database
        session_logger = get_session_logger()
        current_log_file = session_logger.get_or_create_session()
        
        if current_log_file:
            # Set the log file path for this updater to match session logger folder
            self.logFilePath = str(current_log_file.parent)
        else:
            # Fallback to default if session logger not available
            from utilities.settings_dialog import SettingsDialog
            settings = SettingsDialog.get_saved_settings()
            if settings.get('cloudinary_log_folder'):
                self.logFilePath = settings['cloudinary_log_folder']
            else:
                # Ultimate fallback to logs subdirectory
                self.logFilePath = str(Path.cwd() / "logs")
                Path(self.logFilePath).mkdir(parents=True, exist_ok=True)

        database_file_path = Path(self.logFilePath) / DATABASE_FILE_NAME
        self.database = load_csv_database(database_file_path)

        self.mode = sync_files_mode

        # Define the persistent directory for resized files
        self.resized_dir = get_local_temp_dir()

        # Ensure the resized directory is empty at the start of the script
        if self.resized_dir.exists():
            try:
                shutil.rmtree(self.resized_dir, ignore_errors=True)
            except PermissionError as e:
                debug_errors(f"Error in deleting tmp folder: {e}")
        self.resized_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.log_message("Starting assessment phase")
            
            # Log mode and directory/files info in a cleaner way
            if sync_files_mode == FILES_MODE:
                # For files mode, just show count and first file's directory
                if isinstance(local_directory, list) and len(local_directory) > 0:
                    first_file_dir = os.path.dirname(local_directory[0])
                    self.log_message(f"Mode: {sync_files_mode} (Files) | Selected {len(local_directory)} files from: {first_file_dir}")
                else:
                    self.log_message(f"Mode: {sync_files_mode} (Files) | No files selected")
            else:
                # For folder modes, show the directory path as before
                self.log_message(f"Mode: {sync_files_mode} | Directory: {local_directory}")

            debug_cloudinary("")
            self.log_message("Checking the folder...")

            # List all files from Cloudinary
            self.cloudinary_files = list_all_files()

            # Assessment phase
            self.files_to_upload, self.files_to_resize, self.total_upload_size, self.already_synced_count = assessment_phase(self, 
                local_directory, self.database, self.cloudinary_files, self.resized_dir, self.mode)

            # Save the updated database to the CSV file
            update_csv_database(database_file_path, self.database)

            # Display Cloudinary usage and storage details
            cloudinaryAvailableStorage = get_cloudinary_credits(self)
            
            # Store values for final report
            self.total_original_size = total_original_size
            self.cloudinary_available_storage = cloudinaryAvailableStorage
            numberOfTotalFilesToUpload = len(self.files_to_upload) + len(self.files_to_resize)

            # Check if all files are already synced
            if numberOfTotalFilesToUpload == 0:
                self.log_message("="*80)
                self.log_message("ASSESSMENT")
                self.log_message("="*80)
                
                # Log mode and directory/files info in a cleaner way
                if self.mode == FILES_MODE:
                    if isinstance(self.local_directory, list) and len(self.local_directory) > 0:
                        first_file_dir = os.path.dirname(self.local_directory[0])
                        self.log_message(f"Mode: {self.mode} (Files) | Selected {len(self.local_directory)} files from: {first_file_dir}")
                    else:
                        self.log_message(f"Mode: {self.mode} (Files) | No files selected")
                else:
                    self.log_message(f"Mode: {self.mode} | Directory: {self.local_directory}")
                    
                self.log_message(f"Files already synced: {self.already_synced_count}")
                self.log_message(f"Files to upload: {numberOfTotalFilesToUpload}")
                self.log_message(f"Total size to upload: {convert_bytes(self.total_upload_size)} (original size: {convert_bytes(self.total_original_size)})")
                self.log_message(f"Available storage on Cloudinary: {convert_bytes(cloudinaryAvailableStorage)}")
                self.log_message("All files already on Cloudinary. No upload needed.")
                self.log_message("="*80)
                
                # Close log file
                if self.log_file_handle:
                    self.log_file_handle.close()
                    self.log_file_handle = None
                
                # Show message to user and reinitialize
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Upload Status")
                msg.setText("All files already on Cloudinary. No upload needed.")
                msg.exec_()
                
                # Emit signal to reinitialize the UI
                self.upload_complete_signal.emit([0, 0])  # 0 uploaded, 0 errors
                return

            self.log_message(f"--- Upload Summary ---")

            self.log_message(f"Transformation credits retrieved: {self.currentTransformations}")

            self.log_message(f"Number of files already synced: {self.already_synced_count}")
            self.log_message(f"Number of files to upload: {numberOfTotalFilesToUpload}")
            self.log_message(f"Total size to upload: {convert_bytes(self.total_upload_size)} (original size: {convert_bytes(total_original_size)})")
            self.log_message(f"Available storage on Cloudinary: {convert_bytes(cloudinaryAvailableStorage)}")
            afterUploadStorage = cloudinaryAvailableStorage - self.total_upload_size - (numberOfTotalFilesToUpload * 1024 * 1024)
            self.log_message(f"Estimated storage transformation consumed: {convert_bytes(numberOfTotalFilesToUpload * 1024 * 1024)}")
            self.log_message(f"Estimated storage on Cloudinary after upload: {convert_bytes(afterUploadStorage)}")

            # Check if the total upload size exceeds the quota
            if self.total_upload_size > cloudinaryAvailableStorage:
                error_msg = f"Total upload size ({convert_bytes(self.total_upload_size)}) exceeds the {convert_bytes(cloudinaryAvailableStorage)} available space."
                self.log_message(error_msg, "ERROR")
                return

            # Emit signal to indicate assessment phase is complete
            dataList = []
            dataList.append(self.already_synced_count)                                  # 0
            dataList.append(numberOfTotalFilesToUpload)                                 # 1
            dataList.append(convert_bytes(self.total_upload_size))                      # 2 string
            dataList.append(convert_bytes(total_original_size))                         # 3 string
            dataList.append(convert_bytes(numberOfTotalFilesToUpload * 1024 * 1024))    # 4 string transformation consumed
            dataList.append(convert_bytes(afterUploadStorage))                          # 5 string

            storageCredits = self.currentStorageCredits + (self.total_upload_size / (1024 * 1024 * 1024))
            transformationCreditsAfterUpload = self.currentTransformations + (numberOfTotalFilesToUpload / 1000) 

            storageCreditsPerc = round((storageCredits / CREDITS_MAX) * 100 , 2)  # Convert to percentage
            transformationsCreditsPerc = (transformationCreditsAfterUpload / CREDITS_MAX) * 100
            bandwidthCreditsPerc = (self.currentBandwidth / CREDITS_MAX) * 100          # Bandwidth doesn't change with upload

            self.log_message(f"Storage Credits Percentage: {storageCreditsPerc}%, transformation Credits Percentage: {transformationsCreditsPerc}%, Bandwidth Credits Percentage: {bandwidthCreditsPerc}%")


            # credits breakdown for bar
            dataList.append(storageCreditsPerc)                 # (6) bar
            dataList.append(transformationsCreditsPerc)         # (7) bar
            dataList.append(bandwidthCreditsPerc)               # (8) bar

            self.assessment_complete_signal.emit(dataList)

        except Exception as e:
            exceptionMessage = f"Failed to sync files: {e}"
            self.log_message(exceptionMessage, "ERROR")
        
        # Note: Don't close log file here as it will be used in upload phase

    def upload_files(self, upload_mode):
        """Upload files after user confirmation."""
        # Initialize counters for detailed reporting
        resize_error_count = 0
        upload_error_count = 0
        total_processed = len(self.files_to_upload) + len(self.files_to_resize)
        
        uploaded_count, error_files, resize_errors = upload_phase(
            self, self.files_to_upload, self.files_to_resize, self.resized_dir, self.local_directory, self.database)

        # Save the updated database
        # database_file_path = Path(LOG_FILE_PATH) / DATABASE_FILE_NAME
        database_file_path = Path(self.logFilePath) / DATABASE_FILE_NAME
        update_csv_database(database_file_path, self.database)

        # Calculate final statistics
        resize_error_count = len(resize_errors)
        upload_error_count = len(error_files)
        total_files_found = total_processed + self.already_synced_count
        
        # Create comprehensive final report
        self.log_message("="*80)
        self.log_message("ASSESSMENT")
        self.log_message("="*80)
        self.log_message(f"Files already synced: {self.already_synced_count}")
        self.log_message(f"Files to upload: {total_processed}")
        self.log_message(f"Total size to upload: {convert_bytes(self.total_upload_size)} (original size: {convert_bytes(self.total_original_size)})")
        self.log_message(f"Available storage on Cloudinary: {convert_bytes(self.cloudinary_available_storage)}")
        self.log_message("="*80)
        self.log_message("UPLOAD")
        self.log_message("="*80)
        self.log_message(f"Starting upload phase with {len(self.files_to_upload)} direct uploads and {len(self.files_to_resize)} files to resize")
        if len(self.files_to_resize) > 0:
            self.log_message(f"Number of files to resize: {len(self.files_to_resize)}")
        if len(self.files_to_upload) > 0 or len(self.files_to_resize) > 0:
            self.log_message(f"Uploading {total_processed} files...")
        self.log_message("="*80)
        self.log_message("FINAL UPLOAD REPORT")
        self.log_message("="*80)
        self.log_message(f"Total pictures processed: {total_files_found}")
        self.log_message(f"Pictures already on Cloudinary: {self.already_synced_count}")
        self.log_message(f"Pictures successfully uploaded: {uploaded_count}")
        self.log_message(f"Pictures skipped due to resize errors: {resize_error_count}")
        self.log_message(f"Pictures skipped due to upload errors: {upload_error_count}")
        self.log_message(f"Total errors: {resize_error_count + upload_error_count}")
        
        if resize_errors:
            self.log_message("\nRESIZE ERRORS:")
            for error_message in resize_errors:
                self.log_message(f"  - {error_message}", "ERROR")
        
        if error_files:
            self.log_message("\nUPLOAD ERRORS:")
            for error_message in error_files:
                self.log_message(f"  - {error_message}", "ERROR")
        
        self.log_message("="*80)
        
        # Legacy logging for compatibility
        self.log_message(f"Already synced: {self.already_synced_count}")
        self.log_message(f"Uploaded: {uploaded_count}")
        self.log_message(f"Errors: {len(error_files)}")
        
        # Log session end
        session_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_message("=" * 50)
        self.log_message("UPLOAD SESSION COMPLETE")
        self.log_message(f"Session ended: {session_end}")
        self.log_message(f"Files uploaded: {uploaded_count}")
        self.log_message(f"Files with errors: {len(error_files) + resize_error_count}")
        self.log_message("=" * 50)
        
        # Close log file
        if self.log_file_handle:
            self.log_file_handle.close()
            self.log_file_handle = None
        
        # Close file logger
        if self.file_logger:
            for handler in self.file_logger.handlers:
                handler.close()
            self.file_logger.handlers.clear()
            self.file_logger = None
        
        # Emit upload complete signal
        upload_data = [uploaded_count, len(error_files) + resize_error_count]
        self.upload_complete_signal.emit(upload_data)

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
            debug_errors(f"Warning: Could not load database: {e}")


def get_actual_resource_count(cloudinary_updater_instance):
    """Get the actual count of resources by fetching and counting them ourselves."""
    try:
        debug_business(f"Getting actual resource count by fetching all assets...")
        
        total_assets = 0
        
        # Method 1: Count all assets by actually fetching them (most reliable)
        try:
            debug_business(f"Fetching all resources to count them...")
            next_cursor = None
            batch_count = 0
            
            while True:
                # Fetch resources in batches
                if next_cursor:
                    resources_response = cloudinary.api.resources(
                        max_results=100, 
                        next_cursor=next_cursor
                    )
                else:
                    resources_response = cloudinary.api.resources(max_results=100)
                
                # Count assets in this batch
                assets_in_batch = len(resources_response.get('resources', []))
                total_assets += assets_in_batch
                batch_count += 1
                
                debug_business(f"Batch {batch_count}: {assets_in_batch} assets (total so far: {total_assets})")
                
                # Check if there are more pages
                next_cursor = resources_response.get('next_cursor')
                if not next_cursor:
                    break
                
                # Safety limit to prevent infinite loops
                if batch_count > 100:  # Max 10,000 assets
                    debug_business(f"Safety limit reached after {batch_count} batches")
                    break
            
            debug_business(f"Method 1 - Counted {total_assets} assets by fetching all resources")
            
        except Exception as e:
            debug_errors(f"Method 1 (fetch count) failed: {e}")
            total_assets = 0
        
        # Method 2: Fallback to total_count from a single API call
        if total_assets == 0:
            try:
                resources_response = cloudinary.api.resources(max_results=1)
                total_assets = resources_response.get('total_count', 0)
                debug_cloudinary(f"Method 2 - Using total_count from API: {total_assets}")
            except Exception as e:
                debug_errors(f"Method 2 (total_count) failed: {e}")
                total_assets = 0
        
        # Method 3: Try specific resource types if general count failed
        if total_assets == 0:
            try:
                image_count = 0
                raw_count = 0
                video_count = 0
                
                # Count images
                try:
                    image_resources = cloudinary.api.resources(resource_type="image", max_results=1)
                    image_count = image_resources.get('total_count', 0)
                except:
                    pass
                
                # Count raw files
                try:
                    raw_resources = cloudinary.api.resources(resource_type="raw", max_results=1)
                    raw_count = raw_resources.get('total_count', 0)
                except:
                    pass
                
                # Count videos
                try:
                    video_resources = cloudinary.api.resources(resource_type="video", max_results=1)
                    video_count = video_resources.get('total_count', 0)
                except:
                    pass
                
                total_assets = image_count + raw_count + video_count
                debug_cloudinary(f"Method 3 - By resource types: {total_assets} (images: {image_count}, raw: {raw_count}, video: {video_count})")
                
            except Exception as e:
                debug_errors(f"Method 3 (by type) failed: {e}")
                total_assets = 0
        
        debug_business(f"Final counted resource count: {total_assets}")
        return total_assets if total_assets > 0 else None
        
    except Exception as e:
        debug_errors(f"Error getting actual resource count: {e}")
        return None

def get_cloudinary_status(cloudinary_updater_instance):
    """Get Cloudinary usage details."""
    try:
        debug_cloudinary("Starting Cloudinary status check...")
        result = usage()
        debug_cloudinary(f"Cloudinary API result: {result}")
        
        api_key = cloudinary_updater_instance.apiKey
        api_secret = cloudinary_updater_instance.apiSecret
        url = f"https://api.cloudinary.com/v1_1/{cloudinary_updater_instance.cloudName}/usage"

        debug_cloudinary("in get_cloudinary_status")
        debug_cloudinary(f"Cloudinary API URL: {url}")
        debug_cloudinary(f"Cloudinary API Key: {api_key}")

        response = requests.get(url, auth=HTTPBasicAuth(api_key, api_secret))
        headers = response.headers

        transformations = result.get('transformations', {})
        transformationsCount = transformations.get('usage', 'N/A')
        transformationsCredits = transformationsCount / 1000 if isinstance(transformationsCount, (int, float)) else 0

        storage = result.get('storage', {})
        storageBytes = storage.get('usage', 0)
        storageCount = convert_bytes(storage.get('usage', 0))
        storageCredits = convert_to_gb(storage.get('usage', 0))

        bandwidth = result.get('bandwidth', {})
        bandwidthCount = convert_bytes(bandwidth.get('usage', 0))
        bandwidthCredits = convert_to_gb(bandwidth.get('usage', 0))

        # Use a default credits limit (25 GB = 25 credits)
        CREDITS_MAX = 25
        usedCredits = transformationsCredits + storageCredits + bandwidthCredits
        remainingCredits = CREDITS_MAX - usedCredits
        remainingStorage = (remainingCredits) * 1024 * 1024 * 1024  
        
        # Get actual resource count from resources API (more accurate)
        actual_resource_count = get_actual_resource_count(cloudinary_updater_instance)
        if actual_resource_count is not None and actual_resource_count > 0:
            num_files = actual_resource_count
            debug_cloudinary(f"Using actual resource count: {num_files}")
        else:
            # Fallback to usage API count (this is actually more reliable for billing)
            num_files = result.get('resources', 0)
            debug_cloudinary(f"Using usage API resource count (this is the authoritative count for billing): {num_files}")
        
        average_file_size = 0
        if num_files > 0:
            average_file_size = storageBytes / num_files
        else:
            average_file_size = cloudinary_updater_instance.maxFileSize

        debug_business(f"\n--- CLOUDINARY STATUS SUMMARY ---")
        debug_business(f"Storage Credits: {storageCredits}")
        debug_business(f"Bandwidth Credits: {bandwidthCredits}")
        debug_business(f"Transformations Credits: {transformationsCredits}")
        debug_business(f"Total Used Credits: {usedCredits}")
        debug_business(f"Remaining Credits: {remainingCredits}")
        
        debug_business(f"\nPercentage calculations:")
        debug_business(f"  CREDITS_MAX: {CREDITS_MAX}")
        
        # Calculate the actual percentages
        storage_percentage = (storageCredits / CREDITS_MAX) * 100
        transformations_percentage = (transformationsCredits / CREDITS_MAX) * 100
        bandwidth_percentage = (bandwidthCredits / CREDITS_MAX) * 100
        
        debug_business(f"  Storage %: {storage_percentage:.2f}%")
        debug_business(f"  Transformations %: {transformations_percentage:.2f}%")
        debug_business(f"  Bandwidth %: {bandwidth_percentage:.2f}%")

        # Return status data in expected format
        return_data = [
            True,  # Success flag
            transformationsCount,  # Transformations usage
            storageCount,  # Storage usage (formatted)
            bandwidthCount,  # Bandwidth usage (formatted) 
            num_files,  # Number of files
            transformations_percentage,  # Transformation credits % - FIXED: Now actually percentage!
            storage_percentage,  # Storage credits % - FIXED: Now actually percentage!
            bandwidth_percentage,  # Bandwidth credits % - FIXED: Now actually percentage!
            storageCredits,  # Storage credits value
            transformationsCredits,  # Transformations credits value
            bandwidthCredits,  # Bandwidth credits value
            remainingCredits,  # Remaining credits
            average_file_size,  # Average file size
            remainingStorage  # Remaining storage
        ]
        
        debug_cloudinary(f"\nReturn data array:")
        for i, item in enumerate(return_data):
            debug_cloudinary(f"  [{i}]: {item} (type: {type(item)})")
        
        return return_data
        
    except Exception as e:
        debug_errors(f"Error in get_cloudinary_status: {e}")
        return [False, f"Connection error: {str(e)}"]

def convert_bytes(size):
    """Convert bytes to human readable format"""
    if size == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def convert_to_gb(size):
    """Convert bytes to GB"""
    return size / (1024 * 1024 * 1024)


# Missing function definitions needed for compilation
def load_csv_database(csv_path):
    """
    Load the CSV database into a dictionary and validate its structure.
    Handles both legacy single keys and new incremental keys for duplicate (size+filetype).
    """
    database = {}
    if csv_path.exists():
        with open(csv_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            key_counters = {}  # Track how many times we've seen each (size+filetype)
            
            for row in reader:
                try:
                    base_key = (int(row['original_size']), row['filetype'])
                    
                    # Handle duplicate keys by using incremental identifiers
                    if base_key in key_counters:
                        key_counters[base_key] += 1
                        db_key = (base_key, key_counters[base_key])
                    else:
                        key_counters[base_key] = 0
                        db_key = base_key  # First occurrence uses simple key
                    
                    database[db_key] = {
                        'file_name': row['file_name'],
                        'original_size': int(row['original_size']),
                        'resized_size': int(row['resized_size']) if row['resized_size'] else None,
                        'filetype': row['filetype'],
                        'public_id': row.get('public_id', ''),  # Add public_id field with fallback
                        'url': row.get('url', ''),  # Add url field with fallback
                        'upload_date': row.get('upload_date', '')  # Add upload_date field with fallback
                    }
                except KeyError as e:
                    debug_errors(f"Missing field in CSV row: {e}. Row: {row}")
                except ValueError as e:
                    debug_errors(f"Invalid value in CSV row: {e}. Row: {row}")
    return database

def update_csv_database(csv_path, database):
    """Update the CSV database with new entries."""
    debug_cloudinary(f"Updating database with {len(database)} entries")
    with open(csv_path, mode='w', newline='') as file:
        fieldnames = ['file_name', 'original_size', 'resized_size', 'filetype', 'public_id', 'url', 'upload_date']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        # Sort database entries by resized_size for consistent ordering
        sorted_entries = sorted(database.values(), key=lambda x: x.get('resized_size', 0))
        for data in sorted_entries:
            writer.writerow(data)

def get_local_temp_dir():
    """Returns a writable temporary subdirectory."""
    temp_dir = Path(tempfile.gettempdir()) / "my_temp_folder"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir

def list_all_files():
    """List all files from Cloudinary."""
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
    return all_files

def assessment_phase(self, local_directory, database, cloudinary_files, resized_dir, sync_files_mode):
    """Placeholder assessment phase function - unused in new workflow."""
    return [], [], 0, 0

def upload_phase(self, files_to_upload, files_to_resize, temp_dir_path, local_directory, database):
    """Placeholder upload phase function - unused in new workflow."""
    return 0, [], []

def get_cloudinary_credits(self):
    """Get Cloudinary credit information."""
    try:
        result = usage()
        return result
    except Exception as e:
        debug_errors(f"Failed to get Cloudinary credits: {e}")
        return None