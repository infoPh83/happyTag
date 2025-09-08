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

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        # File handler will be added dynamically per session
    ]
)

# Cloudinary configuration, needed for the method usage() to work
# cloudinary.config(
#    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
#    api_key=os.getenv('CLOUDINARY_API_KEY'),
#    api_secret=os.getenv('CLOUDINARY_API_SECRET')
# )

#
# cloudinary.config(
#     cloud_name="dnkcbkdgk",
#     api_key=***REMOVED***,
#     api_secret="***REMOVED***"
# )



def debug_log(message):
    """Log a message if debug mode is enabled."""
    if DEBUG:
        logging.info(f"[DEBUG] {message}")

def convert_bytes(size):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def convert_to_gb(size):
    """Convert bytes to GB."""
    size_in_gb = size / (1024 ** 3)
    return round(size_in_gb, 2)

def updateAssessmentBar(self, value):
    self.update_assessment_bar_signal.emit(value)

def updateUploadResizeBar(self, value):
    self.updateResizeInUploadProgressBar_signal.emit(value)

def get_cloudinary_status(self):
    try:
        """Get Cloudinary usage details."""
        print("in get_cloudinary_status A")
        result = usage()
        print(f"Cloudinary API URL: {result}")
        # api_key = os.getenv('CLOUDINARY_API_KEY')
        # api_secret = os.getenv('CLOUDINARY_API_SECRET')
        # url = f"https://api.cloudinary.com/v1_1/{os.getenv('CLOUDINARY_CLOUD_NAME')}/usage"

        # old way
        # api_key = ***REMOVED***
        # api_secret = "***REMOVED***"
        # url = "https://api.cloudinary.com/v1_1/dnkcbkdgk/usage"

        # new way

        api_key = self.apiKey
        api_secret = self.apiSecret
        url = f"https://api.cloudinary.com/v1_1/{self.cloudName}/usage"

        print("in get_cloudinary_status")
        print(f"Cloudinary API URL: {url}")
        print(f"Cloudinary API Key: {api_key}")
        print(f"Cloudinary API Secret: {api_secret}")

        response = requests.get(url, auth=HTTPBasicAuth(api_key, api_secret))
        headers = response.headers

        transformations = result.get('transformations', {})
        transformationsCount = transformations.get('usage', 'N/A')
        transformationsCredits = transformationsCount / 1000

        storage = result.get('storage', {})
        storageBytes = storage.get('usage', 0)
        storageCount = convert_bytes(storage.get('usage', 0))
        storageCredits = convert_to_gb(storage.get('usage', 0))

        bandwidth = result.get('bandwidth', {})
        bandwidthCount = convert_bytes(bandwidth.get('usage', 0))
        bandwidthCredits = convert_to_gb(bandwidth.get('usage', 0))

        usedCredits = transformationsCredits + storageCredits + bandwidthCredits
        remainingCredits = CREDITS_MAX - usedCredits
        remainingStorage = (remainingCredits) * 1024 * 1024 * 1024  
        num_files = result.get('resources', {})
        average_file_size = 0
        if num_files > 0 :
            average_file_size = storageBytes/num_files
        else:
            average_file_size = self.maxFileSize

        print(f"\n--- LIMITS FROM HEADERS ---")
        print(f"Total Limit: {headers.get('X-FeatureRateLimit-Limit', 'N/A')}")
        print(f"Remaining Calls: {headers.get('X-FeatureRateLimit-Remaining', 'N/A')}")
        print(f"Reset Time: {headers.get('X-FeatureRateLimit-Reset', 'N/A')}")

        allowanceText = f"{CREDITS_MAX} allowance"
        usedCreditsText = f"{round(usedCredits, 2)} used"
        remainingCreditsText = f"{round(remainingCredits, 2)} still available"

        print(f"\n--- CREDITS / STORAGE USAGE ---")
        print(f"\nCredits          :\t{CREDITS_MAX} allowance\t-\t{round(usedCredits, 2)} used\t\t-\t{round(remainingCredits, 2)} still available")
        print(f"Credits breakdown:\t{storageCredits} storage\t-\t{round(transformationsCredits, 2)} transformations\t-\t{bandwidthCredits} bandwidth")
        print(f"Currently stored :\t{storageCount}  \t-\t{num_files} images\t\t-\t{convert_bytes(average_file_size)} average size")
        print(f"Storage available:\t{convert_bytes(remainingStorage)}\t-\t{calculate_pictures(remainingCredits - 1, average_file_size)} images\t\t-\twith {convert_bytes(self.maxFileSize)} max size, keeping 1gb for bandwidth")

        storageCreditsPerc = (storageCredits / CREDITS_MAX) * 100
        transformationsCreditsPerc = (transformationsCredits / CREDITS_MAX) * 100
        bandwidthCreditsPerc = (bandwidthCredits / CREDITS_MAX) * 100

        data = []
        # status
        data.append(True)                               # (0) True = successfully retrieved Cloudinary Status
        data.append("")                                 # (1) Error message

        # credits
        data.append(allowanceText)                      # (2) lab_nowAllowance
        data.append(usedCreditsText)                    # (3)  lab_nowUsedCredits
        data.append(remainingCreditsText)               # (4) lab_nowRemainingCredits
        # credits breakdown for bar
        data.append(storageCreditsPerc)                 # (5) bar
        data.append(transformationsCreditsPerc)         # (6) bar
        data.append(bandwidthCreditsPerc)               # (7) bar
        # credit breakdown for text
        data.append(storageCredits)                     # (8) lab_nowCreditsStorage
        data.append(round(transformationsCredits, 2))   # (9) lab_nowTransformationsCredits
        data.append(bandwidthCredits)                   # (10) lab_nowCreditsBandwidth
        # currently stored
        data.append(storageCount)                       # (11) lab_nowStored
        data.append(num_files)                          # (12) lab_nowImageCount
        data.append(convert_bytes(average_file_size))   # (13) lab_nowAverageSize
        # storage available
        data.append(convert_bytes(remainingStorage))    # (14) lab_nowStorageAvailable
        data.append(calculate_pictures(remainingCredits - 1, average_file_size))    # (15) lab_nowImageCountAvailable
        data.append(convert_bytes(self.maxFileSize))       # (16) lab_nowMaxSize
        # managed so far
    except Exception as e:
        data = []
        data.append(False)                               # (0) True = successfully retrieved Cloudinary Status
        data.append(f"Error in retrieving cloudinary status: {e}")                                 # (1) Error message


    # return allowanceText, usedCreditsText, remainingCreditsText, storageCreditsPerc, transformationsCreditsPerc, bandwidthCreditsPerc
    return data

def get_cloudinary_credits(self):
    # global MAX_FILE_SIZE
    """Get Cloudinary usage details."""
    result = usage()
    # api_key = os.getenv('CLOUDINARY_API_KEY')
    # api_secret = os.getenv('CLOUDINARY_API_SECRET')
    # url = f"https://api.cloudinary.com/v1_1/{os.getenv('CLOUDINARY_CLOUD_NAME')}/usage"

    # old way
    # api_key = ***REMOVED***
    # api_secret = "***REMOVED***"
    # url = "https://api.cloudinary.com/v1_1/dnkcbkdgk/usage"

    # new way
    api_key = self.apiKey
    api_secret = self.apiSecret
    url = f"https://api.cloudinary.com/v1_1/{self.cloudName}/usage"

    logging.info("in get_cloudinary_credits")
    logging.info(f"Cloudinary API URL: {url}")
    logging.info(f"Cloudinary API Key: {api_key}")
    logging.info(f"Cloudinary API Secret: {api_secret}")


    response = requests.get(url, auth=HTTPBasicAuth(api_key, api_secret))
    headers = response.headers

    transformations = result.get('transformations', {})
    transformationsCount = transformations.get('usage', 'N/A')
    transformationsCredits = transformationsCount / 1000

    storage = result.get('storage', {})
    storageBytes = storage.get('usage', 0)
    storageCount = convert_bytes(storage.get('usage', 0))
    storageCredits = convert_to_gb(storage.get('usage', 0))

    bandwidth = result.get('bandwidth', {})
    bandwidthCount = convert_bytes(bandwidth.get('usage', 0))
    bandwidthCredits = convert_to_gb(bandwidth.get('usage', 0))

    usedCredits = transformationsCredits + storageCredits + bandwidthCredits
    remainingCredits = CREDITS_MAX - usedCredits
    remainingStorage = (remainingCredits - 1) * 1024 * 1024 * 1024  # Keeping at least 1Gb for bandwidth
    num_files = result.get('resources', {})
    average_file_size = 0
    if num_files > 0 :
        average_file_size = storageBytes/num_files
    else:
        average_file_size = self.maxFileSize

    print(f"\n--- LIMITS FROM HEADERS ---")
    print(f"Total Limit: {headers.get('X-FeatureRateLimit-Limit', 'N/A')}")
    print(f"Remaining Calls: {headers.get('X-FeatureRateLimit-Remaining', 'N/A')}")
    print(f"Reset Time: {headers.get('X-FeatureRateLimit-Reset', 'N/A')}")

    print(f"\n--- CREDITS / STORAGE USAGE ---")
    print(f"\nCredits          :\t{CREDITS_MAX} allowance\t-\t{round(usedCredits, 2)} used\t\t-\t{round(remainingCredits, 2)} still available")
    print(f"Credits breakdown:\t{storageCredits} storage\t-\t{round(transformationsCredits, 2)} transformations\t-\t{bandwidthCredits} bandwidth")
    print(f"Currently stored :\t{storageCount}  \t-\t{num_files} images\t\t-\t{convert_bytes(average_file_size)} average size")
    print(f"Storage available:\t{convert_bytes(remainingStorage)}\t-\t{calculate_pictures(remainingCredits - 1, average_file_size)} images\t\t-\twith {convert_bytes(self.maxFileSize)} max size, keeping 1gb for bandwidth")

    return remainingStorage

def calculate_pictures(total_gb, picture_size):
    """Calculate the number of pictures that can be stored."""
    total_mb = total_gb * 1024
    picture_size_mb = picture_size / 1024 / 1024
    num_pictures = total_mb // (picture_size_mb)
    return int(num_pictures)

def calculate_picturesOld(total_gb, picture_size_mb):
    """Calculate the number of pictures that can be stored."""
    total_mb = total_gb * 1024
    num_pictures = total_mb // picture_size_mb
    return int(num_pictures)

def load_csv_database(csv_path):
    """Load the CSV database into a dictionary and validate its structure."""
    database = {}
    if csv_path.exists():
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
                except KeyError as e:
                    logging.error(f"Missing field in CSV row: {e}. Row: {row}")
                except ValueError as e:
                    logging.error(f"Invalid value in CSV row: {e}. Row: {row}")
    return database

def update_csv_database(csv_path, database):
    logging.info(f"************ UPDATING DATABASE with {len(database)} entries  **************")
    with open(csv_path, mode='w', newline='') as file:
        fieldnames = ['file_name', 'original_size', 'resized_size', 'filetype']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row
        for data in database.values():  # Iterate over the values (dictionaries) in the database
            writer.writerow(data)  # Write each dictionary as a row
            logging.debug(f"Updated database: {data}")


# Function to check if a file is in the database using original_size and filetype
def is_file_in_database(database, original_size, filetype, debugThis):
    """
    Check if a file exists in the database based on original_size and filetype.
    """
    
    if debugThis:
        logging.info(f"Checking database for file with original_size={original_size}, filetype={filetype}")

    # Create the key to look up
    db_key = (original_size, filetype)

    # Check if the key exists in the database
    if db_key in database:
        if debugThis:
            logging.info(f"File found in database: {database[db_key]}")
        return True
    else:
        if debugThis:
            logging.info("File not found in database.")
        return False




# Assuming SUPPORTED_FORMATS, MAX_DIMENSION, MAX_FILE_SIZE, and resized_count are defined elsewhere

def resize_image_to_fit(self, file_path):
    """Resize an image to fit within the specified dimensions and file size."""
    global resized_count
    try:
        with Image.open(file_path) as img:
            start_time = time.time()  # Start the clock
            iterations = 0

            original_format = img.format

            logging.info(f"Original format of {file_path.name}: {original_format}")  # Debug lin

            if original_format not in SUPPORTED_FORMATS:
                logging.warning(f"Skipping unsupported format: {file_path.name} (Format: {original_format})")
                return None

            original_width, original_height = img.size
            if original_format == 'GIF' and img.mode == 'P':
                img = img.convert('RGB')

            if max(original_width, original_height) > MAX_DIMENSION:
                if original_width > original_height:
                    new_width = MAX_DIMENSION
                    new_height = int((MAX_DIMENSION / original_width) * original_height)
                else:
                    new_height = MAX_DIMENSION
                    new_width = int((MAX_DIMENSION / original_height) * original_width)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                new_width = original_width
                new_height = original_height

            quality = 95
            
            while True:
                buffer = BytesIO()
                image_format = original_format.upper() if original_format else 'JPEG'
                # logging.info(f"In the loop {iterations} | Image format of {file_path.name}: {image_format}")  # Debug lin
                if image_format in ['JPG', 'JPEG']:
                    image_format = 'JPEG'
                    img.save(buffer, format=image_format, quality=quality)
                elif image_format == 'PNG':
                    image_format = 'PNG'
                    img.save(buffer, format=image_format, optimize=True)
                elif image_format == 'TIFF':
                    image_format = 'TIFF'
                    img.save(buffer, format=image_format, compression="tiff_deflate")
                elif image_format == 'GIF':
                    image_format = 'JPEG'
                    img.save(buffer, format=image_format, quality=quality)
                else:
                    logging.warning(f"Unsupported format detected: {image_format}. Defaulting to JPEG.")
                    image_format = 'JPEG'
                    img.save(buffer, format=image_format, quality=quality)

                # logging.info(f"In the loop after saving it {iterations} | Image format of {file_path.name}: {img.format}")  # Debug lin

                resize_params = (image_format, quality, new_width, new_height, iterations)
                new_status, new_buffer, new_img, new_resize_params = resize_logic(self, 1, file_path, img, buffer, start_time, resize_params)
                status, buffer, img, resize_params = new_status, new_buffer, new_img, new_resize_params
                image_format, quality, new_width, new_height, iterations = resize_params  # Update the variables with new values
                if status == 1:
                    return buffer

    except Exception as e:
        logging.info(f"resize_image_to_fit. Failed to process {file_path.name}: {e}")
        raise Exception(f"resize_image_to_fit. Failed to process {file_path.name}: {e}")
    
def resize_logic(self, logicMode, file_path, img, buffer, startTime, resize_params):
    """Resize logic. returns 1 when resize complete, 0 if needs new iteration """
    global resized_count

    thisImg = img
    thisImage_format, thisQuality, thisNew_width, thisNew_height, thisIterations = resize_params

    size = buffer.tell()
    original_size = file_path.stat().st_size  # Get the original file size

    
    if size <= self.maxFileSize and size <= original_size:
        buffer.seek(0)
        resized_count += 1
        return 1, buffer, thisImg, resize_params

    elapsed_time = time.time() - startTime  # Calculate elapsed time
    if elapsed_time > RESIZING_TIME_LIMIT:
        exceptionMessage = f"Time limit exceeded after {thisIterations} iterations: {elapsed_time:.2f} seconds for {file_path.name}"
        print(exceptionMessage)
        raise RuntimeError(exceptionMessage)
    
    thisIterations += 1

    # Calculate the resizing factor based on the current size and MAX_FILE_SIZE
    size_ratio = size / self.maxFileSize  # Calculate the size ratio
    if size_ratio > 2:
        resize_factor = 0.5  # Reduce size by 50% if the current size is more than twice the MAX_FILE_SIZE
    elif size_ratio > 1.5:
        resize_factor = 0.7  # Reduce size by 30% if the current size is more than 1.5 times the MAX_FILE_SIZE
    else:
        resize_factor = 0.9  # Reduce size by 10% if the current size is close to the MAX_FILE_SIZE


    # logging.info(f"i: {thisIterations} | original size {convert_bytes(original_size)} | Resized size {convert_bytes(size)} | for {file_path.name}")
    # logging.info(f"Current quality: {thisQuality} | Next ratio: {size_ratio} | format: {thisImage_format} | W x H: {int(thisImg.width)} x {int(thisImg.height)}")

    if thisImage_format == 'PNG':
        thisNew_width = int(thisImg.width * resize_factor)
        thisNew_height = int(thisImg.height * resize_factor)
        resizedImg = thisImg.resize((thisNew_width, thisNew_height), Image.Resampling.LANCZOS)
    else:
        if thisQuality > 60:
            thisQuality -= 5
            resizedImg = thisImg
        else:
            thisNew_width = int(thisImg.width * resize_factor)
            thisNew_height = int(thisImg.height * resize_factor)
            resizedImg = thisImg.resize((thisNew_width, thisNew_height), Image.Resampling.LANCZOS)

    # Update the resize_params tuple with new values
    thisResize_params = (thisImage_format, thisQuality, thisNew_width, thisNew_height, thisIterations)

    return 0, buffer, resizedImg, thisResize_params











     


def get_executable_directory():
    """Get the directory containing the executable."""
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def debug_cloudinary_metadata(cloudinary_files):
    """Debug function to inspect metadata of files uploaded to Cloudinary."""
    for file in cloudinary_files:
        debug_log(f"Cloudinary File: {file['public_id']}")
        debug_log(f"  - Size (bytes): {file.get('bytes')}")
        debug_log(f"  - Format: {file.get('format')}")
        debug_log(f"  - Created At: {file.get('created_at')}")
        debug_log(f"  - Context: {file.get('context', {})}")
        debug_log(f"  - Metadata: {file.get('metadata', {})}")

def is_file_synced(file_path, resized_size, cloudinary_files):
    """Check if a file already exists on Cloudinary."""
    filetype = file_path.suffix.lower().lstrip('.')  # Remove leading dot for consistency

    for cloudinary_file in cloudinary_files:
        cloudinary_size = int(cloudinary_file.get('bytes', 0))  # Convert to int safely
        if cloudinary_size == resized_size and cloudinary_file.get('format', '').lower() == filetype:
            # logging.info("file synced")
            return True

    # logging.info("file NOT synced")
    return False

# Function to check if a file is synced using resized_size and filetype
def is_file_synced_DeepSeek(database, resized_size, filetype):
    """
    Check if a file is synced (resized) in the database based on resized_size and filetype.
    """   
    for data in database.values():
        if data['resized_size'] == resized_size and data['filetype'] == filetype:
            return True
    return False



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

def upload_to_cloudinary(file_path, folder):
    """Upload a file to Cloudinary."""
    try:
        debug_log(f"Uploading file: {file_path.name} to folder: {folder}")
        response = cloudinary.uploader.upload(
            str(file_path),
            folder=folder,
            public_id=re.sub(r"[^\w]", "_", file_path.stem),
            resource_type='image',
            tags=["hello", "tag n.2", "I'm a cloudinary tag"]
        )
        debug_log(f"Upload successful: {file_path.name} -> {response['public_id']}")
        return response.get('public_id')
    except Exception as e:
        raise Exception (e)
    #    logging.error(f"Failed to upload {file_path.name}: {e}")
    #    return None


def assessment_phase(self, local_directory, database, cloudinary_files, resized_dir, sync_files_mode):
    global total_original_size
    print("in ASSESSMENT PHASE AA")

    """Assess files in the local directory and categorize them for processing."""
    files_to_upload = []  # Files to be uploaded (already resized)
    files_to_resize = []  # Files to be resized and uploaded in the upload phase
    files_to_be_resized_in_assessment = []    
    total_upload_size = 0
    already_synced_count = 0
    specific_file = False

    # Get the total number of files to process
    print(f"called assessment phase with {sync_files_mode}")
    all_files = []
    if sync_files_mode == FOLDER_MODE:
        
        all_files = list(Path(local_directory).rglob('*'))
        for paths in all_files:
                
                print (f"type: {type(paths)}, content: {paths}")
    elif sync_files_mode == SINGLE_FOLDER_MODE:
        # Only scan files in the current folder, not subdirectories
        all_files = list(Path(local_directory).glob('*'))
        # Store the folder name for later use in upload
        self.original_folder_name = Path(local_directory).name
        print(f"SINGLE_FOLDER_MODE: stored folder name = '{self.original_folder_name}'")
        for paths in all_files:
            print (f"single folder - type: {type(paths)}, content: {paths}")
    else:
        if sync_files_mode == FILES_MODE:
  
            all_files = [Path(path) for path in local_directory]

            # Convert the list of strings to a list of Path objects
            all_files = [Path(file_path) for file_path in local_directory]
            first_path = all_files[0]
            local_directory = str(first_path.parents[1])
            self.local_directory = local_directory
            
        else:
            # implement this
            print ("sync_files called without a proper mode")
                
                
    
    total_files = len([f for f in all_files if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS])

    
    # self.update_ui_signal.emit(f"Assessing {total_files} files...")
    self.update_assessment_file_count.emit(total_files)
    self.updateStatusLabel(f"Assessing {total_files} images (of {len(all_files)} files)...")

    processed_files = 0
    progress_checkpoint = 0  # Log progress every 10%

    logging.info(f"Assessing {total_files} images...")


    for file_path in all_files:
        if file_path.is_file() and file_path.suffix.lower() in VALID_EXTENSIONS:
            try:
                specific_file = False

                
                
                # Get file details
                original_size = file_path.stat().st_size
                filetype = file_path.suffix.lower()
                db_key = (original_size, filetype)  # Key for database lookup

                if is_file_in_database(database, original_size, filetype, specific_file):
                    
                # FILE IS IN THE DATABASE SO WE ALREADY KNOW ITS RESIZED SIZE AND WE COMPARE TO CLOUDINARY FILES
                    resized_size = database[db_key]['resized_size']
                    
                    if not is_file_synced(file_path, resized_size, cloudinary_files):
                        # FILE IS NOT SYNCHED WITH CLOUDINARY. IN UPLOAD PHASE IT WILL BE RESIZED AND UPLOADED
                        
                        files_to_resize.append(file_path)
                        total_upload_size += resized_size
                        total_original_size += original_size
                    else:
                        # FILE IS SYNCHED WITH CLOUDINARY: SKIP
                        
                        already_synced_count += 1
                else:
                    # FILE NOT IN DATABASE. BEING RESIZED NOW TO BE ABLE TO COMPARE IT WITH CLOUDINARY
                    files_to_be_resized_in_assessment.append(file_path)

            except Exception as e:
                exceptionMessage = f"assessment_phase. Failed to process {file_path.name}: {e}"
                self.log_message(exceptionMessage, "ERROR")

    
    numberOfFilesToBeResized = len(files_to_be_resized_in_assessment)
    processed_files = 0
    progress_checkpoint = 0

    self.updateStatusLabel(f"Resizing {numberOfFilesToBeResized} images")

    for file_path in files_to_be_resized_in_assessment:
        try:
            #this logic goes later

            # sending signal with first and last image paths
            imagesToShowList = []
            imagesToShowList.append(str(file_path))
            self.setPreviewImages_signal.emit(imagesToShowList)

            resized_buffer = resize_image_to_fit(self, file_path)
            if resized_buffer is None:
                exceptionMessage = f"assessment_phase. Failed to process {file_path.name}: resize failed"
                self.log_message(exceptionMessage, "WARNING")
                processed_files += 1
                continue

            print(f"FILE PATH CHECH: local directory: {local_directory}, relative: {file_path.relative_to(local_directory)}")
            # Save the resized file to the persistent directory
            resized_file_path = resized_dir / file_path.relative_to(local_directory)
            resized_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(resized_file_path, 'wb') as f:
                f.write(resized_buffer.getvalue())

            # Update the database with the resized size
            resized_size = resized_file_path.stat().st_size

            # Get file details
            original_size = file_path.stat().st_size
            filetype = file_path.suffix.lower()
            db_key = (original_size, filetype)  # Key for database lookup

            database[db_key] = {
                'file_name': file_path.name,
                'original_size': original_size,
                'resized_size': resized_size,
                'filetype': filetype
            }

            # Check if the file is already synced

            if not is_file_synced(file_path, resized_size, cloudinary_files):
                # FILE WAS NOT IN DATABASE (IT IS NOW) AND IT IS NOT SYNCHED. WILL BE UPLOADED
                
                # logging.info("ASSESSMENT. CASE 3       NOT in database and NOT synched: Resized and added to upload queue")
                files_to_upload.append(resized_file_path)
                total_upload_size += resized_size
                total_original_size += original_size
            else:
                # FILE WAS NOT IN DATABASE (IT IS NOW) AND IT IS ALREADY SYNCHED. SKIPPED

                already_synced_count += 1
            ## later logic ends

            # Update progress
            processed_files += 1
            progress = (processed_files / numberOfFilesToBeResized) * 100
            if progress >= progress_checkpoint:
                # logging.info(f"{int(progress_checkpoint)}% complete...")
                updateAssessmentBar(self, int(progress))
                progress_checkpoint += 1

        except Exception as e:
            exceptionMessage = f"assessment_phase. Failed to process {file_path.name}: {e}"
            self.log_message(exceptionMessage, "ERROR")


    # self.update_ui_signal.emit("Assessment complete")
    self.updateStatusLabel("Assessment complete")
    updateAssessmentBar(self, 100)
    logging.info("Assessment phase complete.")
    return files_to_upload, files_to_resize, total_upload_size, already_synced_count



def upload_phase(self, files_to_upload, files_to_resize, temp_dir_path, local_directory, database):
    """Phase 2: Upload files to Cloudinary"""
    try:
        print(f"UPLOAD PHASE: local directory: {local_directory}")
        
        uploaded_count = 0
        error_files = []
        resize_errors = []

        # Resize files marked for resizing
        total_files_to_resize = len(files_to_resize)
        
        if total_files_to_resize > 0:
            progress_checkpoint = 0  # Log progress every 10%
            i = 1

            for index, file_path in enumerate(files_to_resize, start=1):
                try:
                    resized_buffer = resize_image_to_fit(self, file_path)

                    self.update_uploadResizeCount_signal.emit(f"{i} / {total_files_to_resize}")
                    

                    if resized_buffer is None:
                        error_msg = f"Skipping file due to processing error: {file_path.name}"
                        self.log_message(error_msg, "WARNING")
                        resize_errors.append(error_msg)
                        continue

                    resized_file_path = temp_dir_path / file_path.relative_to(local_directory)

                    # update UI with preview
                    self.setUploadPreviewImage_signal.emit(str(resized_file_path))
                    
                    resized_file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(resized_file_path, 'wb') as f:
                        f.write(resized_buffer.getvalue())

                    # Update the database
                    original_size = file_path.stat().st_size
                    filetype = file_path.suffix.lower()
                    key = (original_size, filetype)
                    database[key] = {
                        'file_name': file_path.name,
                        'original_size': original_size,
                        'resized_size': resized_file_path.stat().st_size,
                        'filetype': filetype
                    }

                    # Add to files_to_upload
                    files_to_upload.append(resized_file_path)

                    # Update progress
                    progress = (index / total_files_to_resize) * 100
                    if progress >= progress_checkpoint:
                        self.updateResizeInUploadProgressBar_signal.emit(int(progress)) 
                        
                        self.log_message(f"Resizing progress: {int(progress)}% complete...")
                        # updateUploadResizeBar(self, int(progress_checkpoint))
                        progress_checkpoint += 1
                except Exception as e:
                    error_msg = f"Failed to resize {file_path.name}: {e}"
                    self.log_message(error_msg, "ERROR")
                    resize_errors.append(error_msg)

        self.uploadStarting_signal.emit(True)

        # Upload all files
        total_files_to_upload = len(files_to_upload)
        if total_files_to_upload > 0:
            print("")
            progress_checkpoint = 0  # Log progress every 10%

            for index, file_path in enumerate(files_to_upload, start=1):
                try:
                    # Create cloud folder path based on the upload mode
                    if self.mode == SINGLE_FOLDER_MODE and self.original_folder_name:
                        # Use the original folder name for single folder mode
                        cloud_folder = f"{CLOUDINARY_FOLDER_PREFIX}/{self.original_folder_name}".replace("\\", "/")
                    else:
                        # Use relative path for other modes
                        relative_path = file_path.relative_to(temp_dir_path).parent
                        cloud_folder = f"{CLOUDINARY_FOLDER_PREFIX}/{relative_path}".replace("\\", "/")
                    
                    # Clean up the folder name
                    cloud_folder = re.sub(r"[^\w/]", "_", cloud_folder)

                    public_id = upload_to_cloudinary(file_path, cloud_folder)
                    if public_id:
                        uploaded_count += 1

                    # Update progress
                    
                    # update UI with preview
                    self.setUploadPreviewImage_signal.emit(str(file_path))
                    progress = (index / total_files_to_upload) * 100
                    self.updateProgressBar_signal.emit(int(progress))
                    if progress >= progress_checkpoint:
                        progress_checkpoint += 10
                except Exception as e:
                    error_msg = f"Failed to upload {file_path.name}: {e}"
                    self.log_message(error_msg, "ERROR")
                    error_files.append(error_msg)
                    
    finally:
        # Clear the temp file where resized files are stored
        delete_resize_tmp_dir(temp_dir_path)
        # delete_resize_tmp_dir(self.resized_dir)
        

    return uploaded_count, error_files, resize_errors


# Get a suitable temporary directory
def get_local_temp_dir():
    """Returns a writable temporary subdirectory."""
    temp_dir = Path(tempfile.gettempdir()) / "my_temp_folder"
    temp_dir.mkdir(parents=True, exist_ok=True)  # Ensure it exists
    return temp_dir


def delete_resize_tmp_dir(temp_dir_path):
    try:
        # Clean up the resized directory at the end of the script
        if temp_dir_path.exists():
            for file in temp_dir_path.glob("*"):
                file.unlink()  # Delete all files in the directory
            temp_dir_path.rmdir()  # Remove the directory itself
                    
    except Exception as e:
        # print(f"error in deleting the temp folder {e}\nNow Forcing it")
        # Forcing deleting of tmp folder
        shutil.rmtree(temp_dir_path, ignore_errors=True)
    

# Main entry point
# if __name__ == "__main__":
#    local_directory = get_executable_directory()
#    sync_files(local_directory)
