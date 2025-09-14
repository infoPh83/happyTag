"""
Cloudinary Upload Handler

This module handles the Cloudinary upload phase for HappyTag application.
Separated from main.py to improve code organization and maintainability.

Features:
- Processes files_to_upload (ready files) and files_to_resize (needs resizing first)
- Includes tag metadata from image widgets in uploads
- Uses categorized debug system with 'upload' category
- Integrates with existing CloudinaryUpdater and ImageAssessment systems
"""

import os
import re
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import CSV database functions
from utilities.cloudinary_update_v13 import update_csv_database, DATABASE_FILE_NAME
from PIL import Image
import cloudinary
import cloudinary.uploader
from PyQt5.QtCore import QObject, pyqtSignal

from utilities.debug_utils import debug_upload, debug_assessment
from utilities.image_assessment import ImageAssessment
import subprocess
import sys

# Import exiftool availability from main
try:
    from main import EXIFTOOL_AVAILABLE, EXIFTOOL_PATH
except ImportError:
    EXIFTOOL_AVAILABLE = False
    EXIFTOOL_PATH = None


def get_cloudinary_public_id_from_metadata(file_path):
    """
    Read stored Cloudinary public_id from image metadata using exiftool.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        str or None: The public_id if found, None if not found or error
    """
    if not EXIFTOOL_AVAILABLE or not EXIFTOOL_PATH:
        debug_upload(f"ExifTool not available for reading metadata from {file_path}")
        return None
        
    try:
        # Use exiftool to read UserComment field which stores our public_id
        result = subprocess.run([
            EXIFTOOL_PATH,
            '-UserComment',
            '-s3',  # Short format, no tag names
            str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            user_comment = result.stdout.strip()
            # Check if it contains our cloudinary public_id marker
            if user_comment.startswith('cloudinary_public_id:'):
                public_id = user_comment.replace('cloudinary_public_id:', '', 1)
                debug_upload(f"Found Cloudinary public_id in metadata: {public_id}")
                return public_id
        
        debug_upload(f"No Cloudinary public_id found in metadata for {os.path.basename(file_path)}")
        return None
        
    except Exception as e:
        debug_upload(f"Error reading metadata from {file_path}: {e}")
        return None


def write_cloudinary_public_id_to_metadata(file_path, public_id):
    """
    Write Cloudinary public_id to image metadata using exiftool.
    
    Args:
        file_path: Path to the image file
        public_id: The Cloudinary public_id to store
        
    Returns:
        bool: True if successful, False if error
    """
    if not EXIFTOOL_AVAILABLE or not EXIFTOOL_PATH:
        debug_upload(f"ExifTool not available for writing metadata to {file_path}")
        return False
        
    try:
        # Use exiftool to write public_id to UserComment field
        result = subprocess.run([
            EXIFTOOL_PATH,
            f'-UserComment=cloudinary_public_id:{public_id}',
            '-overwrite_original',  # Don't create backup files
            str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            debug_upload(f"Successfully wrote public_id to metadata: {os.path.basename(file_path)} -> {public_id}")
            return True
        else:
            debug_upload(f"Error writing metadata to {file_path}: {result.stderr}")
            return False
            
    except Exception as e:
        debug_upload(f"Exception writing metadata to {file_path}: {e}")
        return False


def check_file_cloudinary_status_by_metadata(file_path):
    """
    Check if a file is already uploaded to Cloudinary by reading its metadata.
    This can be used during the assessment phase to skip already-uploaded files.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        dict: {'already_synced': bool, 'public_id': str or None, 'reason': str}
    """
    public_id = get_cloudinary_public_id_from_metadata(file_path)
    
    if public_id:
        return {
            'already_synced': True,
            'public_id': public_id,
            'reason': f"Found Cloudinary public_id in metadata: {public_id}"
        }
    else:
        return {
            'already_synced': False,
            'public_id': None,
            'reason': "No Cloudinary public_id found in metadata"
        }


class CloudinaryUploadHandler(QObject):
    """
    Handles Cloudinary upload operations for HappyTag application.
    Integrates with existing CloudinaryUpdater and ImageAssessment systems.
    """
    
    # Upload progress signals
    upload_progress_signal = pyqtSignal(int)  # Progress percentage (0-100)
    upload_status_signal = pyqtSignal(str)    # Status message
    upload_complete_signal = pyqtSignal(list) # [uploaded_count, error_count]
    upload_preview_signal = pyqtSignal(str)   # Current file being processed
    
    def __init__(self, cloudinary_updater=None, image_assessment=None):
        super().__init__()
        self.cloudinary_updater = cloudinary_updater
        self.image_assessment = image_assessment  # Add reference to ImageAssessment for shared resize logic
        self.assessment_data = None
        self.tag_widgets = []  # Will store references to tag input widgets
        self.source_folder_name = None  # Will store the folder name extracted from first file
        
    def reset_upload_handler(self):
        """Reset all upload handler data for a new processing session"""
        debug_upload("Resetting upload handler for new processing session")
        self.assessment_data = None
        self.tag_widgets = []
        self.source_folder_name = None
        debug_upload("Upload handler reset complete - ready for new session")
        
    def set_assessment_data(self, assessment_data):
        """Set the assessment data containing files_to_upload and files_to_resize"""
        debug_upload("Setting assessment data for upload phase")
        self.assessment_data = assessment_data
        
    def set_tag_widgets(self, tag_widgets):
        """Set references to tag input widgets for extracting metadata"""
        debug_upload(f"Setting {len(tag_widgets)} tag widgets for metadata extraction")
        self.tag_widgets = tag_widgets
        
    def set_source_folder_name(self, source_folder_name):
        """Set the source folder name explicitly to avoid extraction from temp paths"""
        debug_upload(f"Setting explicit source folder name: '{source_folder_name}'")
        self.source_folder_name = source_folder_name
        
    def extract_tags_from_widgets(self):
        """Extract tags from UI widgets to include in upload metadata"""
        tags = []
        
        debug_upload("Extracting tags from UI widgets")
        
        for widget in self.tag_widgets:
            try:
                # Handle different widget types that might contain tag data
                if hasattr(widget, 'toPlainText') and callable(widget.toPlainText):
                    # This is a QPlainTextEdit or QTextEdit widget
                    tag_text = str(widget.toPlainText()).strip()
                    if tag_text:
                        # Split by commas and clean up each tag
                        widget_tags = [tag.strip() for tag in tag_text.split(',') if tag.strip()]
                        tags.extend(widget_tags)
                        debug_upload(f"Extracted tags from text widget: {widget_tags}")
                elif hasattr(widget, 'text') and callable(widget.text):
                    # This is a QLineEdit or similar widget
                    tag_text = str(widget.text()).strip()
                    if tag_text:
                        widget_tags = [tag.strip() for tag in tag_text.split(',') if tag.strip()]
                        tags.extend(widget_tags)
                        debug_upload(f"Extracted tags from line widget: {widget_tags}")
                elif hasattr(widget, 'get_tags') and callable(widget.get_tags):
                    # This is an ImageCardWidget with get_tags method
                    widget_tags = widget.get_tags()
                    if isinstance(widget_tags, list):
                        tags.extend(widget_tags)
                        debug_upload(f"Extracted tags from card widget: {widget_tags}")
                    elif isinstance(widget_tags, str) and widget_tags.strip():
                        widget_tags_list = [tag.strip() for tag in widget_tags.split(',') if tag.strip()]
                        tags.extend(widget_tags_list)
                        debug_upload(f"Extracted tags from card widget (string): {widget_tags_list}")
                elif hasattr(widget, 'currentText') and callable(widget.currentText):
                    tag_text = str(widget.currentText()).strip()
                    if tag_text:
                        tags.append(tag_text)
                        debug_upload(f"Extracted tag from combo: '{tag_text}'")
                elif hasattr(widget, 'value') and callable(widget.value):
                    tag_value = str(widget.value()).strip()
                    if tag_value:
                        tags.append(tag_value)
                        debug_upload(f"Extracted tag from value: '{tag_value}'")
                else:
                    debug_upload(f"Unknown widget type: {type(widget)}, available methods: {[method for method in dir(widget) if not method.startswith('_')]}")
                        
            except Exception as e:
                debug_upload(f"Error extracting tag from widget: {e}")
                
        # Remove duplicates while preserving order
        unique_tags = []
        seen = set()
        for tag in tags:
            if tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)
                
        debug_upload(f"Extracted {len(unique_tags)} unique tags: {unique_tags}")
        return unique_tags
        
    def start_upload_phase(self):
        """
        Start the Cloudinary upload phase.
        Processes both files_to_upload (ready) and files_to_resize (needs processing).
        """
        if not self.assessment_data:
            debug_upload("ERROR: No assessment data available for upload")
            self.upload_status_signal.emit("Error: No assessment data available")
            return
            
        if not self.cloudinary_updater:
            debug_upload("ERROR: No CloudinaryUpdater instance available")
            self.upload_status_signal.emit("Error: No Cloudinary configuration available")
            return
            
        debug_upload("Starting Cloudinary upload phase")
        self.upload_status_signal.emit("Starting Cloudinary upload...")
        
        try:
            # Extract data from assessment
            files_to_upload = self.assessment_data.get('files_to_upload', [])
            files_to_resize = self.assessment_data.get('files_to_resize', [])
            
            debug_upload(f"Upload phase: {len(files_to_upload)} files ready to upload")
            debug_upload(f"Upload phase: {len(files_to_resize)} files need resizing first")
            
            # ENHANCED DEBUG: Show detailed file information
            if files_to_upload:
                debug_upload("Files ready for direct upload:")
                for i, file_path in enumerate(files_to_upload, 1):
                    debug_upload(f"  {i}. {Path(file_path).name} (ready)")
                    
            if files_to_resize:
                debug_upload("Files that need resizing first:")
                for i, file_path in enumerate(files_to_resize, 1):
                    debug_upload(f"  {i}. {Path(file_path).name} (resize needed)")
            
            total_files_to_process = len(files_to_upload) + len(files_to_resize)
            debug_upload(f"Total files to process: {total_files_to_process}")
            
            if not files_to_upload and not files_to_resize:
                debug_upload("No files to upload - all files already synced")
                self.upload_status_signal.emit("All files already synced - no upload needed")
                self.upload_complete_signal.emit([0, 0])
                return
                
            # Extract tags from UI widgets
            upload_tags = self.extract_tags_from_widgets()
            
            # Process upload
            uploaded_count, error_count = self._process_upload_batch(
                files_to_upload, files_to_resize, upload_tags
            )
            
            # Save updated database to CSV after uploads complete
            self._save_database_after_upload()
            
            debug_upload(f"Upload phase complete: {uploaded_count} uploaded, {error_count} errors")
            self.upload_status_signal.emit(f"Upload complete: {uploaded_count} files uploaded")
            self.upload_complete_signal.emit([uploaded_count, error_count])
            
        except Exception as e:
            error_msg = f"Upload phase failed: {e}"
            debug_upload(f"ERROR: {error_msg}")
            self.upload_status_signal.emit(f"Upload failed: {str(e)}")
            self.upload_complete_signal.emit([0, 1])
            
    def _process_upload_batch(self, files_to_upload, files_to_resize, upload_tags):
        """
        Process the upload batch, handling both ready files and files that need resizing.
        
        Args:
            files_to_upload: List of file paths ready for direct upload
            files_to_resize: List of file paths that need resizing before upload
            upload_tags: List of tags to include in upload metadata
            
        Returns:
            tuple: (uploaded_count, error_count)
        """
        uploaded_count = 0
        error_count = 0
        total_files = len(files_to_upload) + len(files_to_resize)
        processed_files = 0
        
        debug_upload(f"Processing upload batch: {total_files} total files")
        
        # Extract folder name from the first file for Cloudinary organization
        self._extract_source_folder_name(files_to_upload, files_to_resize)
        
        # Create temporary directory for resized files
        temp_dir = None
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="happytag_upload_"))
            debug_upload(f"Created temporary directory: {temp_dir}")
            
            # Process files that are ready for direct upload
            for file_path in files_to_upload:
                try:
                    debug_upload(f"Uploading ready file: {file_path}")
                    self.upload_preview_signal.emit(str(file_path))
                    
                    success = self._upload_file_to_cloudinary(file_path, upload_tags)
                    if success:
                        uploaded_count += 1
                        debug_upload(f"Successfully uploaded: {file_path}")
                    else:
                        error_count += 1
                        debug_upload(f"Failed to upload: {file_path}")
                        
                    processed_files += 1
                    progress = int((processed_files / total_files) * 100)
                    self.upload_progress_signal.emit(progress)
                    
                except Exception as e:
                    debug_upload(f"Error uploading file {file_path}: {e}")
                    error_count += 1
                    processed_files += 1
                    
            # Process files that need resizing first
            for file_path in files_to_resize:
                try:
                    debug_upload(f"Processing file that needs resizing: {file_path}")
                    self.upload_preview_signal.emit(str(file_path))
                    
                    # Resize the file
                    resized_path = self._resize_file_for_upload(file_path, temp_dir)
                    if resized_path:
                        # Upload the resized file
                        success = self._upload_file_to_cloudinary(resized_path, upload_tags)
                        if success:
                            uploaded_count += 1
                            debug_upload(f"Successfully uploaded resized file: {file_path}")
                        else:
                            error_count += 1
                            debug_upload(f"Failed to upload resized file: {file_path}")
                    else:
                        error_count += 1
                        debug_upload(f"Failed to resize file: {file_path}")
                        
                    processed_files += 1
                    progress = int((processed_files / total_files) * 100)
                    self.upload_progress_signal.emit(progress)
                    
                except Exception as e:
                    debug_upload(f"Error processing file {file_path}: {e}")
                    error_count += 1
                    processed_files += 1
                    
        finally:
            # Clean up temporary directory
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    debug_upload(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    debug_upload(f"Warning: Could not clean up temp directory {temp_dir}: {e}")
                    
        return uploaded_count, error_count
        
    def _resize_file_for_upload(self, file_path, temp_dir):
        """
        Resize a file for upload using ImageAssessment's shared resize logic.
        This ensures consistency between assessment and upload phases.
        
        Args:
            file_path: Path to the file to resize
            temp_dir: Temporary directory for resized files
            
        Returns:
            Path to resized file or None if resize failed
        """
        try:
            file_path_obj = Path(file_path)
            debug_upload(f"Resizing file for upload: {file_path_obj.name}")
            
            # Use ImageAssessment's resize method for consistency
            if self.image_assessment and hasattr(self.image_assessment, '_resize_image_to_fit'):
                debug_upload(f"Using ImageAssessment resize method for {file_path_obj.name}")
                resized_buffer = self.image_assessment._resize_image_to_fit(file_path_obj)
                
                if resized_buffer:
                    # Save resized buffer to temp file
                    resized_file_path = temp_dir / file_path_obj.name
                    resized_file_path.write_bytes(resized_buffer.getvalue())
                    debug_upload(f"File resized successfully: {resized_file_path}")
                    return resized_file_path
                else:
                    debug_upload(f"ImageAssessment resize returned None for: {file_path}")
                    return None
            else:
                debug_upload(f"ImageAssessment resize method not available for: {file_path}")
                return None
            
        except Exception as e:
            debug_upload(f"Error resizing file {file_path}: {e}")
            return None
    
    def _extract_source_folder_name(self, files_to_upload, files_to_resize):
        """
        Extract the source folder name from the first file for Cloudinary folder organization.
        Note: This method is only used as fallback if source_folder_name wasn't set explicitly.
        
        Args:
            files_to_upload: List of files ready for upload
            files_to_resize: List of files that need resizing
        """
        try:
            # Skip extraction if folder name was already set explicitly
            if self.source_folder_name:
                debug_upload(f"Using explicitly set source folder name: '{self.source_folder_name}'")
                return
                
            # Get the first file from either list
            first_file = None
            if files_to_upload:
                first_file = files_to_upload[0]
            elif files_to_resize:
                first_file = files_to_resize[0]
            
            if first_file:
                file_path_obj = Path(first_file)
                # Get the parent directory name (the folder containing the images)
                extracted_name = file_path_obj.parent.name
                self.source_folder_name = extracted_name
                debug_upload(f"Extracted source folder name from file path: '{extracted_name}'")
                debug_upload(f"WARNING: This may be a temp folder - prefer setting explicit folder name")
                debug_upload(f"Cloudinary upload folder will be: 'Uploads/{self.source_folder_name}'")
            else:
                debug_upload("No files available to extract folder name from")
                self.source_folder_name = None
                
        except Exception as e:
            debug_upload(f"Error extracting source folder name: {e}")
            self.source_folder_name = None
            
    def _upload_file_to_cloudinary(self, file_path, upload_tags):
        """
        Upload a single file to Cloudinary with metadata.
        
        Args:
            file_path: Path to the file to upload
            upload_tags: List of tags to include in upload
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            file_path_obj = Path(file_path)
            debug_upload(f"Uploading to Cloudinary: {file_path_obj.name}")
            
            # Generate folder name and public_id based on original filename
            folder = self._generate_folder_name()
            
            # Create public_id based on original filename (WITH extension for uniqueness)
            original_filename = file_path_obj.stem  # Gets filename without extension
            original_extension = file_path_obj.suffix  # Gets the extension (.jpg, .png, etc.)
            full_filename = f"{original_filename}{original_extension}"  # Complete filename with extension
            
            debug_upload(f"Upload parameters - folder: {folder}, filename: {full_filename}, tags: {upload_tags}")
            
            # Upload to Cloudinary with folder structure AND filename preservation
            response = cloudinary.uploader.upload(
                str(file_path),
                folder=folder,                    # This creates the folder structure
                public_id=full_filename,          # This preserves the complete filename with extension
                resource_type='image',
                tags=upload_tags if upload_tags else [],
                unique_filename=False,            # Don't add suffix since we're using full filename
                use_filename=True                 # Use the filename as basis for public_id
            )
            
            # Log success with filename-based public_id
            cloudinary_url = response.get('url', '')
            final_public_id = response.get('public_id', '')
            debug_upload(f"Upload successful - public_id: {final_public_id}, url: {cloudinary_url}")
            
            # Update database if available
            if self.cloudinary_updater and hasattr(self.cloudinary_updater, 'database'):
                self._update_database_entry(file_path_obj, response)
            
            # Write public_id to image metadata for future reference
            if final_public_id:
                write_cloudinary_public_id_to_metadata(file_path_obj, final_public_id)
                
            return True
            
        except Exception as e:
            debug_upload(f"Cloudinary upload failed for {file_path}: {e}")
            return False
            
    def _generate_folder_name(self):
        """
        Generate folder name for Cloudinary upload based on source folder.
        
        Uses the extracted source folder name to create organized uploads like:
        - Source: c:\\my_data\\holidays_photos\\seaside.jpg
        - Cloudinary: Uploads/holidays_photos/
        """
        if self.source_folder_name:
            folder = f"Uploads/{self.source_folder_name}"
            debug_upload(f"Generated Cloudinary folder: '{folder}'")
        else:
            # Fallback to legacy logic or default
            if (self.cloudinary_updater and 
                hasattr(self.cloudinary_updater, 'original_folder_name') and 
                self.cloudinary_updater.original_folder_name):
                folder = f"Uploads/{self.cloudinary_updater.original_folder_name}"
                debug_upload(f"Using CloudinaryUpdater folder: '{folder}'")
            else:
                folder = "Uploads"
                debug_upload(f"Using default folder: '{folder}'")
        return folder
        
    def _update_database_entry(self, file_path, cloudinary_response):
        """
        Update the local database with upload information.
        Handles duplicate (size+filetype) keys by using incremental identifiers.
        """
        try:
            if not self.cloudinary_updater or not hasattr(self.cloudinary_updater, 'database'):
                debug_upload("Warning: CloudinaryUpdater database not available")
                return
                
            original_size = file_path.stat().st_size
            filetype = file_path.suffix.lower()
            base_key = (original_size, filetype)
            
            # Get resized size from response or use original size
            resized_size = cloudinary_response.get('bytes', original_size)
            
            # Extract auto-generated public_id and URL from Cloudinary response
            auto_public_id = cloudinary_response.get('public_id', '')
            cloudinary_url = cloudinary_response.get('secure_url', cloudinary_response.get('url', ''))
            
            # Handle duplicate keys: Check if this (size+filetype) already exists
            if base_key in self.cloudinary_updater.database:
                existing_entry = self.cloudinary_updater.database[base_key]
                existing_public_id = existing_entry.get('public_id', '')
                
                if existing_public_id != auto_public_id:
                    # Different file with same size+type - use incremental key
                    counter = 1
                    while (base_key, counter) in self.cloudinary_updater.database:
                        counter += 1
                    db_key = (base_key, counter)
                    debug_upload(f"Duplicate key detected: {base_key} -> using incremental key: {db_key}")
                else:
                    # Same file (same public_id) - update existing entry
                    db_key = base_key
                    debug_upload(f"Updating existing entry for same file: {base_key}")
            else:
                # New unique key
                db_key = base_key
                debug_upload(f"Using new unique key: {db_key}")
            
            # Store entry with resolved key
            self.cloudinary_updater.database[db_key] = {
                'file_name': file_path.name,
                'original_size': original_size,
                'resized_size': resized_size,
                'filetype': filetype,
                'public_id': auto_public_id,  # Store auto-generated public_id
                'url': cloudinary_url,        # Store Cloudinary URL
                'upload_date': datetime.now().isoformat()
            }
            
            debug_upload(f"Updated database entry for {file_path.name} - key: {db_key}, public_id: {auto_public_id}")
            
        except Exception as e:
            debug_upload(f"Warning: Could not update database entry for {file_path}: {e}")
    
    def _save_database_after_upload(self):
        """Save the updated database to CSV after upload completion"""
        try:
            if not self.cloudinary_updater or not hasattr(self.cloudinary_updater, 'database'):
                debug_upload("Warning: CloudinaryUpdater database not available for CSV save")
                return
                
            # Determine the database file path
            if hasattr(self.cloudinary_updater, 'logFilePath') and self.cloudinary_updater.logFilePath:
                database_path = Path(self.cloudinary_updater.logFilePath) / DATABASE_FILE_NAME
            else:
                # Fallback to logs directory if logFilePath not set
                database_path = Path("logs") / DATABASE_FILE_NAME
            
            # Ensure directory exists
            database_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save database to CSV with new public_id and url data
            update_csv_database(database_path, self.cloudinary_updater.database)
            
            debug_upload(f"Database saved to CSV: {database_path} with {len(self.cloudinary_updater.database)} entries")
            debug_upload("CSV now includes public_id and URL data from Cloudinary uploads")
            
        except Exception as e:
            debug_upload(f"Warning: Failed to save database to CSV after upload: {e}")