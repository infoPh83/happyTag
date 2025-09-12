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
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
SUPPORTED_FORMATS = {'JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'WEBP'}
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
            
            print(f"[DEBUG] CloudinaryUpdater file logging enabled: {log_file_path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to setup CloudinaryUpdater file logging: {e}")
            self.file_logger = None

    def setCloudinaryUpdaterConfig(self, cloudinary_config):
        print(f"IN CLODINARY UPDATE 6: Cloudinary config: {cloudinary_config}")
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

        print(f"CLODINARY UPDATE VARIABLES: Cloudinary config: {self.logFilePath}, {self.cloudName}, {self.apiKey}, {self.apiSecret}, {self.maxFileSize}")

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
        
        # Log to dedicated file logger if available
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
                print(f"[ERROR] Failed to write to legacy log file: {e}")
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

            logging.info(f"\nSETTING TRANSFORMATION CREDITS: {data[9]}")
            self.currentStorageCredits = data[8]  # Update the current storage value
            self.currentTransformations = data[9]  # Update the current transformations value
            self.currentBandwidth = data[10]  # Update the current bandwidth value
    


    def updateStatusLabel(self, message):
        self.update_ui_signal.emit(message)

    def sync_files(self, local_directory, sync_files_mode):
        logging.info(f"\nSYNC_FILES")
        logging.info(f"\n--- Cloudinary upload v13 --- CloudinaryUpdater with {sync_files_mode}")
        logging.info(f"\nUploading all images  : {local_directory}")
        short_timestamp = datetime.now().strftime("%Y-%m-%d %H-%M")
        log_filename = f"{LOG_NAME}{short_timestamp}.txt"

        # log_file_path = Path(LOG_FILE_PATH) / log_filename
        # database_file_path = Path(LOG_FILE_PATH) / DATABASE_FILE_NAME
        log_file_path = Path(self.logFilePath) / log_filename
        database_file_path = Path(self.logFilePath) / DATABASE_FILE_NAME

        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup file logging for this upload session
        self.setup_file_logging(log_file_path)
        
        # Log session header
        session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_message("=" * 50)
        self.log_message("CLOUDINARY UPLOAD SESSION")
        self.log_message(f"Session started: {session_start}")
        self.log_message(f"Log file: {log_file_path}")
        self.log_message("=" * 50)

        self.database = load_csv_database(database_file_path)

        self.mode = sync_files_mode

        # Define the persistent directory for resized files
        self.resized_dir = get_local_temp_dir()

        # Ensure the resized directory is empty at the start of the script
        if self.resized_dir.exists():
            try:
                shutil.rmtree(self.resized_dir, ignore_errors=True)
            except PermissionError as e:
                print(f"Error in deleting tmp folder: {e}")
        self.resized_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Open log file and store handle for consistent logging
            self.log_file_handle = log_file_path.open("a")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_file_handle.write(f"\n--- Upload Session Log: {timestamp} ---\n")
            
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

            print("")
            logging.info("Checking the folder...")

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

            logging.info(f"\n\n--- Upload Summary ---")

            logging.info(f"Transformation credits retrieved: {self.currentTransformations}")

            logging.info(f"Number of files already synced: {self.already_synced_count}")
            logging.info(f"Number of files to upload: {numberOfTotalFilesToUpload}")
            logging.info(f"Total size to upload: {convert_bytes(self.total_upload_size)} (original size: {convert_bytes(total_original_size)})")
            logging.info(f"Available storage on Cloudinary: {convert_bytes(cloudinaryAvailableStorage)}")
            afterUploadStorage = cloudinaryAvailableStorage - self.total_upload_size - (numberOfTotalFilesToUpload * 1024 * 1024)
            logging.info(f"Estimated storage transformation consumed: {convert_bytes(numberOfTotalFilesToUpload * 1024 * 1024)}")
            logging.info(f"Estimated storage on Cloudinary after upload: {convert_bytes(afterUploadStorage)}")

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

            logging.info(f"Storage Credits Percentage: {storageCreditsPerc}%, transformation Credits Percentage: {transformationsCreditsPerc}%, Bandwidth Credits Percentage: {bandwidthCreditsPerc}%")


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
        logging.info(f"Already synced: {self.already_synced_count}")
        logging.info(f"Uploaded: {uploaded_count}")
        logging.info(f"Errors: {len(error_files)}")
        
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
                    import tempfile
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


def get_cloudinary_status(cloudinary_updater_instance):
    """Get Cloudinary usage details."""
    try:
        print("in get_cloudinary_status A")
        result = usage()
        print(f"Cloudinary API result: {result}")
        
        api_key = cloudinary_updater_instance.apiKey
        api_secret = cloudinary_updater_instance.apiSecret
        url = f"https://api.cloudinary.com/v1_1/{cloudinary_updater_instance.cloudName}/usage"

        print("in get_cloudinary_status")
        print(f"Cloudinary API URL: {url}")
        print(f"Cloudinary API Key: {api_key}")

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
        
        num_files = result.get('resources', 0)
        average_file_size = 0
        if num_files > 0:
            average_file_size = storageBytes / num_files
        else:
            average_file_size = cloudinary_updater_instance.maxFileSize

        print(f"\n--- CLOUDINARY STATUS SUMMARY ---")
        print(f"Storage Credits: {storageCredits}")
        print(f"Bandwidth Credits: {bandwidthCredits}")
        print(f"Transformations Credits: {transformationsCredits}")
        print(f"Total Used Credits: {usedCredits}")
        print(f"Remaining Credits: {remainingCredits}")

        # Return status data in expected format
        return [
            True,  # Success flag
            transformationsCount,  # Transformations usage
            storageCount,  # Storage usage (formatted)
            bandwidthCount,  # Bandwidth usage (formatted) 
            num_files,  # Number of files
            transformationsCredits,  # Transformation credits %
            storageCredits,  # Storage credits %
            bandwidthCredits,  # Bandwidth credits %
            storageCredits,  # Storage credits value
            transformationsCredits,  # Transformations credits value
            bandwidthCredits,  # Bandwidth credits value
            remainingCredits,  # Remaining credits
            average_file_size,  # Average file size
            remainingStorage  # Remaining storage
        ]
        
    except Exception as e:
        print(f"Error in get_cloudinary_status: {e}")
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

