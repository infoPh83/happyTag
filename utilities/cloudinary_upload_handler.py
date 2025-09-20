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

from PIL import Image
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.exceptions import Error as CloudinaryError
from PyQt5.QtCore import QObject, pyqtSignal

from utilities.debug_utils import debug_upload, debug_assessment, debug_timings
from utilities.session_logger import log_session_message
from utilities.image_assessment import ImageAssessment
import subprocess
import sys

# Import exiftool utilities
from utilities.exiftool_utils import (
    write_cloudinary_metadata_to_file, 
    get_cloudinary_public_id_from_metadata
)
from utilities.exiftool_detector import get_exiftool_info

# Import filename sanitization utilities
from utilities.filename_sanitizer import sanitize_filename_for_cloudinary, create_cloudinary_public_id



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
    
    def __init__(self, cloudinary_updater=None, image_assessment=None, main_app=None):
        super().__init__()
        self.cloudinary_updater = cloudinary_updater
        self.image_assessment = image_assessment  # Add reference to ImageAssessment for shared resize logic
        self.main_app = main_app  # Add reference to main app for orphaned cleanup
        self.assessment_data = None
        self.tag_widgets = []  # Will store references to tag input widgets
        self.source_folder_name = None  # Will store the folder name extracted from first file
        self.metadata_write_failures = []  # Track files where metadata writing failed
        
    def get_metadata_failure_summary(self):
        """
        Get a summary of metadata write failures for user display.
        
        Returns:
            dict: Summary with details for user notification
        """
        if not self.metadata_write_failures:
            return None
        # Get current ExifTool status
        exiftool_info = get_exiftool_info()
            
        return {
            'count': len(self.metadata_write_failures),
            'files': [failure['file'] for failure in self.metadata_write_failures],
            'reasons': [failure['reason'] for failure in self.metadata_write_failures],
            'exiftool_available': exiftool_info['available'],
            'exiftool_path': exiftool_info['path'],
            'recommendation': self._get_metadata_failure_recommendation()
        }
    
    def _get_metadata_failure_recommendation(self):
        """Get recommendation for fixing metadata write failures"""
        exiftool_info = get_exiftool_info()
        if not exiftool_info['available']:
            return (
                "ExifTool is not available. To save metadata to image files:\n"
                "• Download ExifTool from https://exiftool.org/\n"
                "• Place exiftool.exe in the 'utilities' folder\n"
                "• Restart the application"
            )
        else:
            return (
                "ExifTool is available but metadata writing failed. This may be due to:\n"
                "• File permission issues\n"
                "• Read-only files\n"
                "• Unsupported file formats"
            )
    
    def reset_upload_handler(self):
        """Reset all upload handler data for a new processing session"""
        debug_upload("Resetting upload handler for new processing session")
        self.assessment_data = None
        self.tag_widgets = []
        self.source_folder_name = None
        self.metadata_write_failures = []  # Reset metadata failure tracking
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
                        # Split by semicolons only and clean up each tag
                        widget_tags = [tag.strip() for tag in tag_text.split(';') if tag.strip()]
                        tags.extend(widget_tags)
                        debug_upload(f"Extracted tags from text widget: {widget_tags}")
                elif hasattr(widget, 'text') and callable(widget.text):
                    # This is a QLineEdit or similar widget
                    tag_text = str(widget.text()).strip()
                    if tag_text:
                        # Split by semicolons only and clean up each tag
                        widget_tags = [tag.strip() for tag in tag_text.split(';') if tag.strip()]
                        tags.extend(widget_tags)
                        debug_upload(f"Extracted tags from line widget: {widget_tags}")
                elif hasattr(widget, 'get_tags') and callable(widget.get_tags):
                    # This is an ImageCardWidget with get_tags method
                    widget_tags = widget.get_tags()
                    if isinstance(widget_tags, list):
                        # If it's a list, check each item for semicolon separation
                        for tag_item in widget_tags:
                            if isinstance(tag_item, str) and ';' in tag_item:
                                # Split semicolon-separated tags
                                for tag in tag_item.split(';'):
                                    clean_tag = tag.strip()
                                    if clean_tag:
                                        tags.append(clean_tag)
                            else:
                                tags.append(tag_item)
                        debug_upload(f"Extracted tags from card widget: {widget_tags}")
                    elif isinstance(widget_tags, str) and widget_tags.strip():
                        # Split by semicolons only for string tags
                        widget_tags_list = [tag.strip() for tag in widget_tags.split(';') if tag.strip()]
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
        Start the NEW Cloudinary upload phase.
        Processes files based on simplified categorization:
        - files_for_tag_update_only: update tags only (no reupload)  
        - files_not_on_cloudinary: resize + upload
        """
        if not self.assessment_data:
            debug_upload("ERROR: No assessment data available for upload")
            self.upload_status_signal.emit("Error: No assessment data available")
            return
            
        if not self.cloudinary_updater:
            debug_upload("ERROR: No CloudinaryUpdater instance available")
            self.upload_status_signal.emit("Error: No Cloudinary configuration available")
            return
            
        debug_upload("Starting NEW Cloudinary upload phase")
        self.upload_status_signal.emit("Uploading on Cloudinary...")
        
        # START UPLOAD TIMING
        upload_start = time.time()

        try:
            # Extract data from NEW assessment structure
            files_for_tag_update = self.assessment_data.get('files_for_tag_update_only', [])
            files_not_on_cloudinary = self.assessment_data.get('files_not_on_cloudinary', [])
            already_synced_count = self.assessment_data.get('already_synced_count', 0)
            
            debug_upload(f"NEW upload phase:")
            log_session_message(f"NEW upload phase:", "UPLOAD")
            debug_upload(f"  Files for tag update only: {len(files_for_tag_update)}")
            log_session_message(f"  Files for tag update only: {len(files_for_tag_update)}", "UPLOAD")
            debug_upload(f"  Files not on Cloudinary (resize + upload): {len(files_not_on_cloudinary)}")
            log_session_message(f"  Files not on Cloudinary (resize + upload): {len(files_not_on_cloudinary)}", "UPLOAD")
            debug_upload(f"  Files already synced (no action): {already_synced_count}")
            log_session_message(f"  Files already synced (no action): {already_synced_count}", "UPLOAD")
            
            # Show detailed file information for each category
                    
            if files_for_tag_update:
                debug_upload("Files needing tag updates only:")
                log_session_message("Files needing tag updates only:", "UPLOAD")
                for i, file_data in enumerate(files_for_tag_update, 1):
                    file_path = file_data.get('file_path', 'Unknown')
                    ui_tags = file_data.get('ui_tags', [])
                    public_id = file_data.get('public_id', 'Unknown')
                    file_msg = f"  {i}. {Path(file_path).name} - Tags: {ui_tags} - ID: {public_id}"
                    debug_upload(file_msg)
                    log_session_message(file_msg, "UPLOAD")
                    
            if files_not_on_cloudinary:
                debug_upload("Files not on Cloudinary needing full upload:")
                for i, file_data in enumerate(files_not_on_cloudinary, 1):
                    file_path = file_data.get('file_path', 'Unknown')
                    ui_tags = file_data.get('ui_tags', [])
                    debug_upload(f"  {i}. {Path(file_path).name} - Tags: {ui_tags}")
            
            total_files_to_process = len(files_for_tag_update) + len(files_not_on_cloudinary)
            total_msg = f"Total files to process: {total_files_to_process}"
            debug_upload(total_msg)
            log_session_message(total_msg, "UPLOAD")
            
            if total_files_to_process == 0:
                debug_upload("No files to process - all files already synced")
                self.upload_status_signal.emit("All files already synced - no upload needed")
                self.upload_complete_signal.emit([0, 0])
                return
                
            # Process NEW upload batch
            uploaded_count, error_count = self._process_new_upload_batch(
                files_for_tag_update, files_not_on_cloudinary
            )
            
            # Report metadata write failures if any
            metadata_failures_count = len(self.metadata_write_failures)
            if metadata_failures_count > 0:
                debug_upload(f"⚠️  Metadata write failures: {metadata_failures_count} files")
                for failure in self.metadata_write_failures:
                    debug_upload(f"  - {failure['file']}: {failure['reason']}")
            
            completion_msg = f"NEW upload phase complete: {uploaded_count} uploaded/updated, {error_count} errors, {metadata_failures_count} metadata failures"
            debug_upload(completion_msg)
            log_session_message(completion_msg, "UPLOAD")
            
            # END UPLOAD TIMING and update main app
            upload_time = time.time() - upload_start
            debug_upload(f"Upload and post-upload phases completed in {upload_time:.3f} seconds")
            if self.main_app and hasattr(self.main_app, 'upload_timing'):
                self.main_app.upload_timing['upload_time'] = upload_time
                self.main_app.upload_timing['post_upload_time'] = 0.0  # Post-upload included in upload timing
            
            # Create detailed status message
            status_msg = f"Upload complete: {uploaded_count} files processed"
            if metadata_failures_count > 0:
                status_msg += f" (⚠️ {metadata_failures_count} metadata warnings)"
            
            self.upload_status_signal.emit(status_msg)
            self.upload_complete_signal.emit([uploaded_count, error_count, metadata_failures_count])
            
        except Exception as e:
            error_msg = f"NEW upload phase failed: {e}"
            debug_upload(f"ERROR: {error_msg}")
            self.upload_status_signal.emit(f"Upload failed: {str(e)}")
            self.upload_complete_signal.emit([0, 1])
            
    def _process_new_upload_batch(self, files_for_tag_update, files_not_on_cloudinary):
        """
        Process the NEW upload batch with categorized files.
        
        Args:
            files_on_cloudinary: List of file data for files on Cloudinary (resize+reupload)
            files_for_tag_update: List of file data for files needing tag updates only
            files_not_on_cloudinary: List of file data for files not on Cloudinary (full upload)
            
        Returns:
            tuple: (uploaded_count, error_count)
        """
        uploaded_count = 0
        error_count = 0
        
        # Initialize detailed timing counters for upload phase breakdown
        detailed_timing = {
            'total_resize_time': 0.0,
            'total_upload_api_time': 0.0,
            'total_metadata_write_time': 0.0,
            'total_widget_update_time': 0.0
        }
        
        # Calculate total work for progress tracking
        total_files = len(files_for_tag_update) + len(files_not_on_cloudinary)
        processed_files = 0
        
        debug_upload(f"Processing NEW upload batch: {total_files} total files")
        
        # Extract folder name from the first file for Cloudinary organization
        all_file_data = files_for_tag_update + files_not_on_cloudinary
        if all_file_data:
            first_file_path = all_file_data[0].get('file_path')
            if first_file_path:
                self._extract_source_folder_name_from_single_file(first_file_path)
        
        # Create temporary directory for resized files
        temp_dir = None
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="happytag_new_upload_"))
            debug_upload(f"Created temporary directory: {temp_dir}")
            
            # Process files that need tag updates only (no reupload)
            for file_data in files_for_tag_update:
                try:
                    file_path = file_data.get('file_path')
                    ui_tags = file_data.get('ui_tags', [])
                    public_id = file_data.get('public_id')
                    
                    updating_msg = f"Updating tags for existing Cloudinary file: {Path(file_path).name}"
                    debug_upload(updating_msg)
                    log_session_message(updating_msg, "UPLOAD")
                    self.upload_preview_signal.emit(f"Updating tags: {Path(file_path).name}")
                    
                    success = self._update_cloudinary_tags_only(public_id, ui_tags)
                    if success == True:
                        uploaded_count += 1
                        debug_upload(f"Tag update successful for {Path(file_path).name}")
                        log_session_message(f"Tag update successful for {Path(file_path).name}", "UPLOAD")
                    elif success == "ORPHANED_404":
                        # Handle orphaned public_id - this should be rare since orphaned cleanup
                        # happens during the loading phase, but handle gracefully if it occurs
                        orphan_msg = f"File {Path(file_path).name} has orphaned public_id - re-uploading as new file"
                        debug_upload(orphan_msg)
                        log_session_message(orphan_msg, "UPLOAD")
                        
                        # Note: No cleanup needed here since it's already done during loading phase
                        # Just treat this as a new upload and let the upload process handle it
                        error_count += 1
                        log_session_message(f"File {Path(file_path).name} needs manual re-upload after orphaned cleanup", "UPLOAD")
                    else:
                        error_count += 1
                        error_msg = f"Tag update failed for {Path(file_path).name}"
                        debug_upload(error_msg)
                        log_session_message(error_msg, "UPLOAD")
                    
                    processed_files += 1
                    progress = int((processed_files / total_files) * 100)
                    self.upload_progress_signal.emit(progress)
                    
                except Exception as e:
                    debug_upload(f"Error updating tags for {file_data}: {e}")
                    error_count += 1
                    processed_files += 1
            
            # Process files not on Cloudinary (full upload)
            for file_data in files_not_on_cloudinary:
                try:
                    file_path = file_data.get('file_path')
                    ui_tags = file_data.get('ui_tags', [])
                    
                    debug_upload(f"Full upload for new file: {Path(file_path).name}")
                    self.upload_preview_signal.emit(f"Uploading: {Path(file_path).name}")
                    
                    # TIMING: Resize phase
                    resize_start = time.time()
                    resized_path = self._resize_file_for_upload(file_path, temp_dir)
                    resize_time = time.time() - resize_start
                    detailed_timing['total_resize_time'] += resize_time
                    debug_timings(f"Resize time for {Path(file_path).name}: {resize_time:.3f}s")
                    
                    if resized_path:
                        # TIMING: Upload API phase
                        upload_start = time.time()
                        success = self._upload_file_to_cloudinary(resized_path, ui_tags, original_file_path=file_path)
                        upload_time = time.time() - upload_start
                        detailed_timing['total_upload_api_time'] += upload_time
                        debug_timings(f"Upload API time for {Path(file_path).name}: {upload_time:.3f}s")
                        
                        if success:
                            uploaded_count += 1
                            debug_upload(f"Full upload successful for {Path(file_path).name}")
                        else:
                            error_count += 1
                            debug_upload(f"Full upload failed for {Path(file_path).name}")
                    else:
                        error_count += 1
                        debug_upload(f"Resize failed for full upload: {Path(file_path).name}")
                    
                    processed_files += 1
                    progress = int((processed_files / total_files) * 100)
                    self.upload_progress_signal.emit(progress)
                    
                except Exception as e:
                    debug_upload(f"Error processing full upload for {file_data}: {e}")
                    error_count += 1
                    processed_files += 1
        
        finally:
            # Clean up temporary directory
            if temp_dir and temp_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    debug_upload(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    debug_upload(f"Warning: Failed to clean up temp directory {temp_dir}: {e}")
        
        # Generate detailed upload phase timing report
        self._generate_detailed_upload_report(detailed_timing, total_files, uploaded_count, error_count)
        
        return uploaded_count, error_count
            
    def _process_upload_batch(self, files_to_upload, files_to_resize):
        """
        Process the upload batch, handling both ready files and files that need resizing.
        
        Args:
            files_to_upload: List of file paths ready for direct upload
            files_to_resize: List of file paths that need resizing before upload
            
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
                    
                    success = self._upload_file_to_cloudinary(file_path, [])
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
                        success = self._upload_file_to_cloudinary(resized_path, [], original_file_path=file_path)
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
    
    def _extract_source_folder_name_from_single_file(self, file_path):
        """Extract source folder name from a single file path"""
        try:
            if file_path:
                file_path_obj = Path(file_path)
                self.source_folder_name = file_path_obj.parent.name
                debug_upload(f"Source folder name extracted: {self.source_folder_name}")
            else:
                self.source_folder_name = None
        except Exception as e:
            debug_upload(f"Error extracting source folder name from single file: {e}")
            self.source_folder_name = None
    
    def _update_cloudinary_tags_only(self, public_id, ui_tags):
        """Update tags on Cloudinary for an existing file without reuploading"""
        try:
            tag_msg = f"Tag-only update for public_id {public_id}: {ui_tags}"
            debug_upload(tag_msg)
            log_session_message(tag_msg, "UPLOAD")
            
            # Use Cloudinary Admin API to update tags for existing resource
            # First, remove all existing tags, then add the new ones
            try:
                # Remove all existing tags (replace with empty array)
                cloudinary.api.update(public_id, tags=[])
                debug_upload(f"Cleared existing tags for {public_id}")
                
                # Add new tags if any
                if ui_tags:
                    # Convert tags to strings and filter out empty ones
                    clean_tags = [str(tag).strip() for tag in ui_tags if str(tag).strip()]
                    if clean_tags:
                        cloudinary.api.update(public_id, tags=clean_tags)
                        debug_upload(f"Successfully updated tags for {public_id}: {clean_tags}")
                    else:
                        debug_upload(f"No valid tags to set for {public_id}")
                else:
                    debug_upload(f"No tags provided for {public_id} - tags cleared")
                
                return True
                
            except CloudinaryError as ce:
                error_msg = f"Cloudinary API error updating tags for {public_id}: {ce}"
                debug_upload(error_msg)
                log_session_message(error_msg, "UPLOAD")
                
                # Check if this is a 404 error (resource not found) - indicates orphaned public_id
                if "404" in str(ce) or "Resource not found" in str(ce):
                    orphan_msg = f"Detected orphaned public_id {public_id} - resource no longer exists on Cloudinary"
                    debug_upload(orphan_msg)
                    log_session_message(orphan_msg, "UPLOAD")
                    log_session_message(f"This file should be treated as a new upload with fresh public_id", "UPLOAD")
                    
                    # Set a flag to indicate this was an orphaned file error
                    # The caller can check this and potentially re-process as new upload
                    return "ORPHANED_404"
                
                return False
                
        except Exception as e:
            error_msg = f"Error updating tags for {public_id}: {e}"
            debug_upload(error_msg)
            log_session_message(error_msg, "UPLOAD")
            return False
            
            
    def _upload_file_to_cloudinary(self, file_path, upload_tags, original_file_path=None):
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
            
            # Generate folder name and public_id based on original filename with sanitization
            folder = self._generate_folder_name()
            
            # Get original filename and sanitize it for Cloudinary compatibility
            original_filename = file_path_obj.stem  # Gets filename without extension
            original_extension = file_path_obj.suffix  # Gets the extension (.jpg, .png, etc.)
            full_filename = f"{original_filename}{original_extension}"  # Complete filename with extension
            
            # Sanitize the filename to avoid encoding issues with special characters
            sanitized_filename = sanitize_filename_for_cloudinary(full_filename)
            
            debug_upload(f"Upload parameters - folder: {folder}")
            debug_upload(f"  Original filename: {full_filename}")
            debug_upload(f"  Sanitized filename: {sanitized_filename}")
            debug_upload(f"  Tags: {upload_tags}")
            
            # Upload to Cloudinary with folder structure AND sanitized filename
            response = cloudinary.uploader.upload(
                str(file_path),
                folder=folder,                    # This creates the folder structure
                public_id=sanitized_filename,     # Use sanitized filename to avoid encoding issues
                resource_type='image',
                tags=upload_tags if upload_tags else [],
                unique_filename=False,            # Don't add suffix since we're using sanitized filename
                use_filename=True                 # Use the filename as basis for public_id
            )
            
            # Log success with filename-based public_id
            cloudinary_url = response.get('url', '')
            final_public_id = response.get('public_id', '')
            debug_upload(f"Upload successful - public_id: {final_public_id}, url: {cloudinary_url}")
            
            # Write both public_id and tags to image metadata for future reference
            if final_public_id:
                # Always write to the original file, not the resized temporary file
                metadata_file_path = Path(original_file_path) if original_file_path else file_path_obj
                
                # Get current tags from UI if available (for enhanced metadata saving)
                current_tags = upload_tags if upload_tags else []
                
                # Write comprehensive metadata (public_id + tags)
                metadata_result = write_cloudinary_metadata_to_file(
                    metadata_file_path, 
                    final_public_id, 
                    tags=current_tags
                )
                
                # Track metadata write failures for user notification
                if not metadata_result['success']:
                    self.metadata_write_failures.append({
                        'file': os.path.basename(metadata_file_path),
                        'reason': metadata_result['message'],
                        'details': metadata_result['details']
                    })
                    debug_upload(f"❌ Metadata write failed for {os.path.basename(metadata_file_path)}: {metadata_result['message']}")
                else:
                    debug_upload(f"✅ Metadata written successfully for {os.path.basename(metadata_file_path)}")
                
                # Update the widget's public_id immediately after successful metadata write
                # Use the original file path that serves as the widget key
                widget_key_path = original_file_path if original_file_path else str(file_path_obj)
                self._update_widget_public_id(widget_key_path, final_public_id)
                
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
        
    def _update_widget_public_id(self, file_path, public_id):
        """
        Update the widget's public_id immediately after successful upload.
        This keeps the in-memory widget state synchronized with the metadata.
        
        Args:
            file_path: Path to the uploaded file (should match image_widgets key)
            public_id: The Cloudinary public_id returned from the upload
        """
        try:
            # Check if we have access to the main app and its image flow manager
            if not self.main_app or not hasattr(self.main_app, 'image_flow_manager'):
                debug_upload("No main_app or image_flow_manager available for widget update")
                return
                
            image_flow_manager = self.main_app.image_flow_manager
            if not image_flow_manager or not hasattr(image_flow_manager, 'image_widgets'):
                debug_upload("No image_widgets available in image_flow_manager")
                return
                
            # Convert file_path to string for comparison
            file_path_str = str(file_path)
            
            # DEBUG: Show what keys are available and what we're looking for
            debug_upload(f"Looking for widget with key: {file_path_str}")
            debug_upload(f"Available widget keys: {list(image_flow_manager.image_widgets.keys())[:3]}...")  # Show first 3 for brevity
            
            # Find the widget corresponding to this file
            widget = image_flow_manager.image_widgets.get(file_path_str)
            if widget and hasattr(widget, 'set_cloudinary_public_id'):
                widget.set_cloudinary_public_id(public_id)
                debug_upload(f"✅ Updated widget public_id for {os.path.basename(file_path_str)}: {public_id}")
            elif widget:
                debug_upload(f"⚠️ Widget found but missing set_cloudinary_public_id method for {os.path.basename(file_path_str)}")
            else:
                debug_upload(f"⚠️ Widget not found for {os.path.basename(file_path_str)}")
                # Try to find a partial match (in case of path normalization issues)
                basename = os.path.basename(file_path_str)
                matching_keys = [k for k in image_flow_manager.image_widgets.keys() if os.path.basename(k) == basename]
                if matching_keys:
                    debug_upload(f"Found potential matches by basename: {matching_keys}")
                    # Use the first match
                    widget = image_flow_manager.image_widgets[matching_keys[0]]
                    if hasattr(widget, 'set_cloudinary_public_id'):
                        widget.set_cloudinary_public_id(public_id)
                        debug_upload(f"✅ Updated widget public_id via basename match for {basename}: {public_id}")
                    else:
                        debug_upload(f"⚠️ Matching widget missing set_cloudinary_public_id method for {basename}")
                
        except Exception as e:
            debug_upload(f"Error updating widget public_id for {os.path.basename(str(file_path))}: {e}")
    
    def _generate_detailed_upload_report(self, detailed_timing, total_files, uploaded_count, error_count):
        """Generate a detailed timing breakdown report for the upload phase"""
        try:
            debug_timings("=" * 60)
            debug_timings("DETAILED UPLOAD PHASE TIMING BREAKDOWN")
            debug_timings("=" * 60)
            debug_timings(f"Files processed: {total_files} total, {uploaded_count} successful, {error_count} errors")
            debug_timings("-" * 60)
            
            # Show individual phase timings
            debug_timings(f"1. Image Resizing:      {detailed_timing['total_resize_time']:.3f} seconds")
            debug_timings(f"2. Cloudinary API:      {detailed_timing['total_upload_api_time']:.3f} seconds")
            debug_timings(f"3. Metadata Writing:    {detailed_timing['total_metadata_write_time']:.3f} seconds")
            debug_timings(f"4. Widget Updates:      {detailed_timing['total_widget_update_time']:.3f} seconds")
            
            # Calculate total and per-file averages
            total_detailed_time = sum(detailed_timing.values())
            debug_timings("-" * 60)
            debug_timings(f"Total detailed time:    {total_detailed_time:.3f} seconds")
            
            if total_files > 0:
                avg_per_file = total_detailed_time / total_files
                debug_timings(f"Average per file:       {avg_per_file:.3f} seconds/file")
            
            # Performance analysis for each phase
            if total_detailed_time > 0:
                debug_timings("-" * 60)
                debug_timings("UPLOAD PHASE BREAKDOWN:")
                
                resize_pct = (detailed_timing['total_resize_time'] / total_detailed_time) * 100
                api_pct = (detailed_timing['total_upload_api_time'] / total_detailed_time) * 100
                metadata_pct = (detailed_timing['total_metadata_write_time'] / total_detailed_time) * 100
                widget_pct = (detailed_timing['total_widget_update_time'] / total_detailed_time) * 100
                
                debug_timings(f"  Resizing:     {resize_pct:5.1f}% of upload time")
                debug_timings(f"  API calls:    {api_pct:5.1f}% of upload time")
                debug_timings(f"  Metadata:     {metadata_pct:5.1f}% of upload time")
                debug_timings(f"  Widgets:      {widget_pct:5.1f}% of upload time")
                
                # Specific recommendations
                debug_timings("-" * 60)
                debug_timings("BOTTLENECK ANALYSIS:")
                if api_pct > 60:
                    debug_timings("🔥 Cloudinary API calls are the main bottleneck (>60%)")
                    debug_timings("   → Consider: image optimization, network connection, or API performance")
                elif resize_pct > 30:
                    debug_timings("🔥 Image resizing is taking significant time (>30%)")
                    debug_timings("   → Consider: pre-processing images or optimizing resize algorithm")
                elif metadata_pct > 20:
                    debug_timings("🔥 Metadata writing is slow (>20%)")
                    debug_timings("   → Consider: ExifTool optimization or batch operations")
                else:
                    debug_timings("✅ No major bottlenecks detected - good performance balance")
                    
            debug_timings("=" * 60)
            
        except Exception as e:
            debug_upload(f"Error generating detailed upload report: {e}")