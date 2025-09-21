import os
import pickle
import sys
import subprocess
import platform
from pathlib import Path
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5 import uic
from .debug_utils import debug_ui_events, debug_errors

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_settings_file_path():
    """ Get the path to the settings file in the user's home directory """
    home_dir = Path.home()
    settings_dir = home_dir / '.happytag'
    settings_dir.mkdir(exist_ok=True)  # Create directory if it doesn't exist
    return settings_dir / 'settings.pkl'

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(resource_path('ui/settingsDialog.ui'), self)
        
        # File paths (existing HappyTag settings)
        self.b2b_final_path = ""
        self.non_tle_path = ""
        self.cloudinary_tags_path = ""
        self.buildings_file_path = ""
        
        # Cloudinary settings
        self.log_folder_path = ""
        self.cloudinary_cloud_name = ""
        self.cloudinary_api_key = ""
        self.cloudinary_api_secret = ""
        
        # Connect existing HappyTag buttons to file selection
        self.pushButton.clicked.connect(self.select_b2b_file)
        self.pushButton_2.clicked.connect(self.select_non_tle_file)
        self.pushButton_3.clicked.connect(self.select_cloudinary_tags_file)
        self.pushButton_4.clicked.connect(self.select_buildings_file)
        
        # Connect Cloudinary buttons and controls
        self.logFolder_button.clicked.connect(self.select_log_folder)
        
        # Connect Cloudinary test connection button
        if hasattr(self, 'testCloudinaryConnection'):
            self.testCloudinaryConnection.clicked.connect(self.test_cloudinary_connection)
            self.testCloudinaryConnection.setEnabled(False)  # Initially disabled
            
            # Connect text change signals to enable/disable test button
            self.cloudName_text.textChanged.connect(self.update_test_button_state)
            self.apiKey_text.textChanged.connect(self.update_test_button_state)
            self.apiSecret_text.textChanged.connect(self.update_test_button_state)
        
        # Connect Cloudinary validate size button
        if hasattr(self, 'validateSize'):
            self.validateSize.clicked.connect(self.validate_cloudinary_capacity)
            
        # Make path labels clickable to open folders
        self.setup_clickable_paths()
        
        # Setup input validators for numeric fields
        self.setup_input_validators()
        
        # Connect OK/Cancel buttons
        self.buttonBox.accepted.connect(self.accept_settings)
        self.buttonBox.rejected.connect(self.reject)
        
        # Load saved settings
        self.load_settings()
        
        # Update ALL SET checkbox initially
        self.update_all_set_checkbox()
        
        # Set the settings file path in the label
        self.update_settings_path_label()
        
    def select_b2b_file(self):
        """Select B2B + B2C final file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select B2B + B2C final file",
            "",
            "Spreadsheet files (*.ods *.xlsx *.xlsm);;All files (*.*)"
        )
        
        if file_path:
            self.b2b_final_path = file_path
            self.B2B_final_path.setText(file_path)
            self.B2B_final_checkbox.setChecked(True)
            self.update_all_set_checkbox()
            
    def select_non_tle_file(self):
        """Select NON TLE tenants list file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select NON TLE tenants list file",
            "",
            "Spreadsheet files (*.ods *.xlsx *.xlsm);;All files (*.*)"
        )
        
        if file_path:
            self.non_tle_path = file_path
            self.nonTLE_path.setText(file_path)
            self.nonTLE_checkbox.setChecked(True)
            self.update_all_set_checkbox()
            
    def select_cloudinary_tags_file(self):
        """Select Cloudinary tags file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cloudinary tags file",
            "",
            "Spreadsheet files (*.ods *.xlsx *.xlsm);;All files (*.*)"
        )
        
        if file_path:
            self.cloudinary_tags_path = file_path
            self.cloudinaryTags_path.setText(file_path)
            self.cloudinaryTags_checkbox.setChecked(True)
            self.update_all_set_checkbox()
            
    def select_buildings_file(self):
        """Select Buildings and Streets file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Buildings and Streets file",
            "",
            "Spreadsheet files (*.ods *.xlsx *.xlsm);;All files (*.*)"
        )
        
        if file_path:
            self.buildings_file_path = file_path
            self.buildings_path.setText(file_path)
            self.buildings_checkbox.setChecked(True)
            self.update_all_set_checkbox()

    # ==================== CLOUDINARY SETTINGS METHODS ====================
    
    def select_log_folder(self):
        """Select Cloudinary log folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Log Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if folder_path:
            self.log_folder_path = folder_path
            self.logFile_path.setText(folder_path)
            
    def update_test_button_state(self):
        """Enable/disable the test connection button based on whether all fields are filled"""
        if hasattr(self, 'testCloudinaryConnection'):
            cloud_name = self.cloudName_text.text().strip()
            api_key = self.apiKey_text.text().strip()
            api_secret = self.apiSecret_text.text().strip()
            
            # Enable button only if all three fields have text
            all_filled = bool(cloud_name and api_key and api_secret)
            self.testCloudinaryConnection.setEnabled(all_filled)
            
            # Clear previous connection result when fields change
            if hasattr(self, 'CloudinaryConnectionResult'):
                if not all_filled:
                    self.CloudinaryConnectionResult.setText("")
    
    def test_cloudinary_connection(self):
        """Test connection to Cloudinary with the provided credentials"""
        if not hasattr(self, 'CloudinaryConnectionResult'):
            debug_ui_events("CloudinaryConnectionResult label not found")
            return
            
        # Get credentials from the form
        cloud_name = self.cloudName_text.text().strip()
        api_key = self.apiKey_text.text().strip()
        api_secret = self.apiSecret_text.text().strip()
        
        if not (cloud_name and api_key and api_secret):
            self.CloudinaryConnectionResult.setText("Please fill in all Cloudinary fields")
            return
        
        # Disable button during test
        self.testCloudinaryConnection.setEnabled(False)
        self.CloudinaryConnectionResult.setText("Testing connection...")
        
        try:
            # Import Cloudinary here to avoid import issues if not installed
            import cloudinary
            import cloudinary.api
            
            # Configure Cloudinary with test credentials
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Test the connection by getting account usage info
            # This is a simple API call that will fail if credentials are wrong
            response = cloudinary.api.usage()
            
            # Show simple success message
            self.CloudinaryConnectionResult.setText("✅ Connected to Cloudinary")
            debug_ui_events(f"Cloudinary connection test successful for cloud: {cloud_name}")
            
        except ImportError:
            self.CloudinaryConnectionResult.setText("❌ Cloudinary library not installed")
            debug_ui_events("Cloudinary library not available for connection test")
            
        except Exception as e:
            self.CloudinaryConnectionResult.setText("❌ Not connected to Cloudinary")
            debug_ui_events(f"Cloudinary connection test failed: {str(e)}")
            
        finally:
            # Re-enable button
            self.update_test_button_state()

    def validate_cloudinary_capacity(self):
        """Validate Cloudinary storage capacity and calculate hosting potential"""
        if not hasattr(self, 'validationResult'):
            debug_ui_events("validationResult label not found")
            return
            
        # Get credentials from the form
        cloud_name = self.cloudName_text.text().strip()
        api_key = self.apiKey_text.text().strip()
        api_secret = self.apiSecret_text.text().strip()
        max_size_text = self.maxSizeLineEdit.text().strip()
        longest_side_text = self.longestSideEdit.text().strip() if hasattr(self, 'longestSideEdit') else '4000'
        
        if not (cloud_name and api_key and api_secret):
            # Show error dialog for missing credentials
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Cloudinary Validation", 
                              "Cloudinary not connected. Check cloudinary settings")
            self.validationResult.setText("")
            return
        
        # Get max size (default to 3.2 if empty)
        try:
            max_size_mb = float(max_size_text) if max_size_text else 3.2
        except ValueError:
            max_size_mb = 3.2
            
        # Get longest side (default to 4000 if empty)
        try:
            longest_side_px = int(longest_side_text) if longest_side_text else 4000
        except ValueError:
            longest_side_px = 4000
        
        # Clear previous result and show "validating..." message
        self.validationResult.setText("Validating Cloudinary capacity...")
        
        try:
            # Import Cloudinary here to avoid import issues if not installed
            import cloudinary
            import cloudinary.api
            
            # Configure Cloudinary with credentials
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Get account usage info
            response = cloudinary.api.usage()
            debug_ui_events(f"Cloudinary usage response: {response}")
            
            # Extract storage information
            storage = response.get('storage', {})
            storage_used_bytes = storage.get('usage', 0)
            
            # Extract resources (number of assets) information
            resources_count = response.get('resources', 0)
            
            debug_ui_events(f"Storage info - used bytes: {storage_used_bytes}, resources count: {resources_count}, max_size_mb: {max_size_mb}, longest_side_px: {longest_side_px}")
            
            # Handle case where storage usage might be in different units or formats
            if storage_used_bytes is None:
                storage_used_bytes = 0
            if resources_count is None:
                resources_count = 0
            
            # Calculate credits and storage capacity
            # 1 credit = 1 GB according to user specification
            total_credits = 25  # Standard Cloudinary free tier (can be made configurable)
            storage_used_gb = storage_used_bytes / (1024 * 1024 * 1024)  # Convert bytes to GB
            remaining_storage_gb = max(0, total_credits - storage_used_gb)  # Ensure non-negative
            
            # Calculate hosting potential
            max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
            remaining_storage_bytes = remaining_storage_gb * 1024 * 1024 * 1024  # Convert GB to bytes
            
            # Calculate how many images can be hosted
            if max_size_bytes > 0:
                total_images_possible = int((total_credits * 1024 * 1024 * 1024) / max_size_bytes)
                remaining_images_possible = int(remaining_storage_bytes / max_size_bytes)
            else:
                total_images_possible = 0
                remaining_images_possible = 0
            
            # Ensure remaining images is not negative
            remaining_images_possible = max(0, remaining_images_possible)
            
            # Calculate average file size and predict based on actual usage
            average_file_size_bytes = 0
            predicted_images_based_on_average = 0
            
            if resources_count > 0 and storage_used_bytes > 0:
                average_file_size_bytes = storage_used_bytes / resources_count
                average_file_size_mb = average_file_size_bytes / (1024 * 1024)
                predicted_images_based_on_average = max(0, int(remaining_storage_bytes / average_file_size_bytes))
                debug_ui_events(f"Average file size: {average_file_size_mb:.2f} MB, predicted images: {predicted_images_based_on_average}")
            
            # Format the result message with line breaks
            result_message = (
                f"Cloudinary can host a total of {total_images_possible:,} images "
                f"with {max_size_mb:.1f} MB max size and {longest_side_px}px longest side.\n"
                f"Considering you consumed {storage_used_gb:.2f} GB of storage space, "
                f"you have room for at least other {remaining_images_possible:,} images."
            )
            
            # Add average file size information if we have uploaded assets
            if resources_count > 0 and average_file_size_bytes > 0:
                average_file_size_mb = average_file_size_bytes / (1024 * 1024)
                # Only show prediction if average size is reasonable (not smaller than 10KB or larger than max size)
                if 0.01 <= average_file_size_mb <= max_size_mb:
                    result_message += (
                        f"\nAssuming the average size of the files uploaded so far would stay the same "
                        f"(avg: {average_file_size_mb:.2f} MB), the number of images that can still be uploaded is {predicted_images_based_on_average:,}"
                    )
                else:
                    result_message += (
                        f"\nAverage file size ({average_file_size_mb:.2f} MB) seems unusual - "
                        f"calculations based on max file size limits."
                    )
            else:
                result_message += (
                    f"\nNo assets uploaded yet - calculations based on max file size limits."
                )
            
            self.validationResult.setText(result_message)
            debug_ui_events(f"Cloudinary capacity validation successful")
            debug_ui_events(f"Total credits: {total_credits}, Used storage: {storage_used_gb:.2f} GB")
            debug_ui_events(f"Resources count: {resources_count}, Max size: {max_size_mb} MB")
            if resources_count > 0 and average_file_size_bytes > 0:
                avg_size_mb = average_file_size_bytes / (1024 * 1024)
                debug_ui_events(f"Average file size: {avg_size_mb:.2f} MB")
            debug_ui_events(f"Result: {result_message}")
            
        except ImportError:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Cloudinary Validation", 
                              "Cloudinary library not installed")
            self.validationResult.setText("")
            debug_ui_events("Cloudinary library not available for capacity validation")
            
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Cloudinary Validation", 
                              "Cloudinary not connected. Check cloudinary settings")
            self.validationResult.setText("")
            debug_ui_events(f"Cloudinary capacity validation failed: {str(e)}")

    def validate_cloudinary_settings(self):
        """Validate Cloudinary settings (non-blocking, informational only)"""
        # Check if any Cloudinary fields are filled
        has_cloudinary_data = (
            self.cloudName_text.text().strip() or
            self.apiKey_text.text().strip() or
            self.apiSecret_text.text().strip() or
            self.maxSizeLineEdit.text().strip() or
            self.log_folder_path
        )
        
        if not has_cloudinary_data:
            return True  # No Cloudinary settings to validate
            
        # If any Cloudinary data exists, validate required fields
        # Note: This is now informational only and doesn't block saving
        missing_fields = []
        
        if not self.cloudName_text.text().strip():
            missing_fields.append("Cloud Name")
            
        if not self.apiKey_text.text().strip():
            missing_fields.append("API Key")
            
        if not self.apiSecret_text.text().strip():
            missing_fields.append("API Secret")
            
        # Validate max size if provided
        max_size_invalid = False
        if self.maxSizeLineEdit.text().strip():
            try:
                max_size = float(self.maxSizeLineEdit.text())
                if max_size <= 0:
                    max_size_invalid = True
            except ValueError:
                max_size_invalid = True
        
        # Show informational message if there are issues, but don't block saving
        if missing_fields or max_size_invalid:
            issues = []
            if missing_fields:
                issues.append(f"Missing required fields: {', '.join(missing_fields)}")
            if max_size_invalid:
                issues.append("Invalid max size value")
                
            QMessageBox.information(self, "Cloudinary Settings Info", 
                                  f"Note: Cloudinary integration may not work properly:\n"
                                  f"• {chr(10).join(issues)}\n\n"
                                  f"You can still use HappyTag as a tagging suite without Cloudinary.")
            return False  # Returns validation status for informational purposes
                
        return True

    @staticmethod
    def validate_cloudinary_complete_setup(cloudinary_settings=None, test_connection=True, show_messages=True):
        """
        Unified validation method for complete Cloudinary setup.
        
        This method:
        1. Checks that all required fields are present
        2. Optionally tests API connectivity 
        3. Returns comprehensive validation results
        
        Args:
            cloudinary_settings: Dict with settings, if None will load from saved settings
            test_connection: Whether to test API connectivity (default True)
            show_messages: Whether to show user messages (default True for dialog use)
            
        Returns:
            dict: {
                'valid': bool,           # Overall validation result
                'connected': bool,       # API connection successful (if tested)
                'missing_fields': list,  # List of missing required fields
                'issues': list,          # List of all validation issues
                'message': str           # User-friendly message
            }
        """
        # Get settings if not provided
        if cloudinary_settings is None:
            cloudinary_settings = SettingsDialog.get_cloudinary_settings()
        
        # Define required fields - separate credentials from other fields
        credential_fields = {
            'cloud_name': 'Cloud Name',
            'api_key': 'API Key', 
            'api_secret': 'API Secret'
        }
        
        additional_fields = {
            'max_size': 'Max Size',
            'longest_side': 'Longest Side',
            'log_folder': 'Log Folder'
        }
        
        # Check for missing credential fields
        missing_credentials = []
        for field_key, field_name in credential_fields.items():
            value = cloudinary_settings.get(field_key, '').strip()
            if not value:
                missing_credentials.append(field_name)
        
        # Check for missing additional fields
        missing_additional = []
        for field_key, field_name in additional_fields.items():
            value = cloudinary_settings.get(field_key, '').strip()
            if not value:
                missing_additional.append(field_name)
        
        # Initialize result structure
        result = {
            'valid': False,
            'connected': False,
            'missing_fields': missing_credentials + missing_additional,
            'issues': [],
            'message': ''
        }
        
        # If credentials are missing, don't show any dialogs or attempt connection test
        if missing_credentials:
            result['issues'].append(f"Missing credentials: {', '.join(missing_credentials)}")
            result['message'] = f"Cloudinary credentials missing: {', '.join(missing_credentials)}"
            # NO MESSAGE DIALOG - just return the result for status display
            return result
        
        # CREDENTIALS ARE VALID - Now test connection first to determine if we should show dialogs
        connection_valid = False
        if test_connection:
            try:
                # Import Cloudinary here to avoid import issues
                import cloudinary
                import cloudinary.api
                
                # Configure Cloudinary with credentials (test connection with just credentials)
                cloudinary.config(
                    cloud_name=cloudinary_settings['cloud_name'],
                    api_key=cloudinary_settings['api_key'],
                    api_secret=cloudinary_settings['api_secret']
                )
                
                # Test connection with a simple API call
                response = cloudinary.api.usage()
                connection_valid = True
                result['connected'] = True
                
            except ImportError:
                result['issues'].append("Cloudinary library not installed")
                result['message'] = "Cloudinary library not available"
                return result  # Don't show additional field dialogs if library missing
                
            except Exception as e:
                result['issues'].append(f"Connection failed: {str(e)}")
                result['message'] = f"Cloudinary connection failed: {str(e)}"
                return result  # Don't show additional field dialogs if connection failed
        
        # Only check additional fields and show dialogs if connection is valid
        if connection_valid or not test_connection:
            # Check if additional fields are missing (but only show dialog if connected)
            if missing_additional and show_messages and connection_valid:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(None, "Cloudinary Setup Incomplete", 
                                      f"Cloudinary credentials are valid, but the following fields are needed for full functionality:\n"
                                      f"• {chr(10).join([f'• {field}' for field in missing_additional])}\n\n"
                                      f"Configure these settings to enable all Cloudinary features.")
        
        # If additional fields are missing, mark as invalid even if connected
        if missing_additional:
            result['issues'].append(f"Missing additional fields: {', '.join(missing_additional)}")
            result['message'] = f"Cloudinary connected but incomplete setup. Missing: {', '.join(missing_additional)}"
            result['valid'] = False
            return result
        
        # Validate numeric fields (only if we're not missing additional fields)
        if not missing_additional:
            try:
                max_size = float(cloudinary_settings.get('max_size', '0'))
                if max_size <= 0:
                    result['issues'].append("Max size must be greater than 0")
            except ValueError:
                result['issues'].append("Max size must be a valid number")
                
            try:
                longest_side = int(cloudinary_settings.get('longest_side', '0'))
                if longest_side <= 0:
                    result['issues'].append("Longest side must be greater than 0")
            except ValueError:
                result['issues'].append("Longest side must be a valid number")
                
            # Validate log folder exists
            log_folder = cloudinary_settings.get('log_folder', '').strip()
            if log_folder and not os.path.exists(log_folder):
                result['issues'].append("Log folder path does not exist")
        
        # If there are validation issues with values, show them
        if result['issues'] and not missing_additional:
            result['message'] = f"Cloudinary configuration has issues: {'; '.join(result['issues'])}"
            if show_messages and connection_valid:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Cloudinary Configuration Issues", 
                                  f"Cloudinary connection successful, but settings have issues:\n"
                                  f"• {chr(10).join(result['issues'])}")
            return result
        
        # If we reach here and connection was valid, everything is good
        if connection_valid:
            result['valid'] = True
            result['message'] = "Cloudinary setup complete and connected successfully"
            
            if show_messages and not missing_additional and not result['issues']:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(None, "Cloudinary Connected", 
                                      "✅ Cloudinary is properly configured and connected!\n\n"
                                      "All features are now available.")
        else:
            # Connection not tested but all fields valid
            result['valid'] = True
            result['message'] = "Cloudinary configuration appears valid (connection not tested)"
        
        return result
            
    def update_all_set_checkbox(self):
        """Update the ALL SET checkbox based on other checkboxes"""
        all_checked = (self.B2B_final_checkbox.isChecked() and 
                      self.nonTLE_checkbox.isChecked() and 
                      self.cloudinaryTags_checkbox.isChecked() and 
                      self.buildings_checkbox.isChecked())
        self.allSet_checkbox.setChecked(all_checked)
            
    def validate_files(self):
        """Validate the selected files"""
        valid_b2b = True
        valid_non_tle = True
        valid_cloudinary = True
        valid_buildings = True
        
        # Validate B2B file if selected
        if self.B2B_final_checkbox.isChecked():
            if not self.b2b_final_path or not os.path.exists(self.b2b_final_path):
                valid_b2b = False
                self.B2B_final_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "B2B + B2C final file does not exist or is invalid.")
            elif not self.b2b_final_path.lower().endswith(('.ods', '.xlsx', '.xlsm')):
                valid_b2b = False
                self.B2B_final_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "B2B + B2C final file must be .ods, .xlsx, or .xlsm format.")
        
        # Validate NON TLE file if selected
        if self.nonTLE_checkbox.isChecked():
            if not self.non_tle_path or not os.path.exists(self.non_tle_path):
                valid_non_tle = False
                self.nonTLE_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "NON TLE tenants list file does not exist or is invalid.")
            elif not self.non_tle_path.lower().endswith(('.ods', '.xlsx', '.xlsm')):
                valid_non_tle = False
                self.nonTLE_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "NON TLE tenants list file must be .ods, .xlsx, or .xlsm format.")
        
        # Validate Cloudinary tags file if selected
        if self.cloudinaryTags_checkbox.isChecked():
            if not self.cloudinary_tags_path or not os.path.exists(self.cloudinary_tags_path):
                valid_cloudinary = False
                self.cloudinaryTags_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Cloudinary tags file does not exist or is invalid.")
            elif not self.cloudinary_tags_path.lower().endswith(('.ods', '.xlsx', '.xlsm')):
                valid_cloudinary = False
                self.cloudinaryTags_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Cloudinary tags file must be .ods, .xlsx, or .xlsm format.")
        
        # Validate Buildings file if selected
        if self.buildings_checkbox.isChecked():
            if not self.buildings_file_path or not os.path.exists(self.buildings_file_path):
                valid_buildings = False
                self.buildings_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Buildings and Streets file does not exist or is invalid.")
            elif not self.buildings_file_path.lower().endswith(('.ods', '.xlsx', '.xlsm')):
                valid_buildings = False
                self.buildings_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Buildings and Streets file must be .ods, .xlsx, or .xlsm format.")
        
        # Update ALL SET checkbox after validation
        self.update_all_set_checkbox()
        
        return valid_b2b and valid_non_tle and valid_cloudinary and valid_buildings
        
    def accept_settings(self):
        """Handle OK button click"""
        if self.validate_files():
            # Always save settings first (regardless of Cloudinary validation)
            self.save_settings()
            
            # After saving, perform comprehensive Cloudinary validation if any Cloudinary data exists
            saved_settings = SettingsDialog.get_cloudinary_settings()
            has_any_cloudinary_data = any([
                saved_settings.get('cloud_name', '').strip(),
                saved_settings.get('api_key', '').strip(),
                saved_settings.get('api_secret', '').strip(),
                saved_settings.get('log_folder', '').strip(),
                saved_settings.get('max_size', '').strip(),
                saved_settings.get('longest_side', '').strip()
            ])
            
            if has_any_cloudinary_data:
                # Perform comprehensive validation (with API test and all required fields)
                validation_result = SettingsDialog.validate_cloudinary_complete_setup(
                    cloudinary_settings=saved_settings,
                    test_connection=True,
                    show_messages=True  # Show user messages about validation result
                )
                debug_ui_events(f"Post-save Cloudinary validation result: {validation_result['message']}")
            
            # Close dialog regardless of Cloudinary validation result
            self.accept()
        # If file validation fails, dialog stays open
            
    def save_settings(self):
        """Save settings to pickle file"""
        settings = {
            # Existing HappyTag settings
            'b2b_final_path': self.b2b_final_path if self.B2B_final_checkbox.isChecked() else "",
            'non_tle_path': self.non_tle_path if self.nonTLE_checkbox.isChecked() else "",
            'cloudinary_tags_path': self.cloudinary_tags_path if self.cloudinaryTags_checkbox.isChecked() else "",
            'buildings_path': self.buildings_file_path if self.buildings_checkbox.isChecked() else "",
            
            # Cloudinary settings
            'cloudinary_log_folder': self.log_folder_path,
            'cloudinary_cloud_name': self.cloudName_text.text().strip(),
            'cloudinary_api_key': self.apiKey_text.text().strip(),
            'cloudinary_api_secret': self.apiSecret_text.text().strip(),
            'cloudinary_max_size': self.maxSizeLineEdit.text().strip() or '3.2',
            'cloudinary_longest_side': (self.longestSideEdit.text().strip() if hasattr(self, 'longestSideEdit') else '') or '4000',
            
            # UI preferences (these will be updated by the main application)
            'text_size': getattr(self, 'text_size', 12),  # Default to 12px if not set
            'last_path': getattr(self, 'last_path', '')  # Last import path for both files and folders
        }
        
        try:
            settings_file = get_settings_file_path()
            with open(settings_file, 'wb') as f:
                pickle.dump(settings, f)
            debug_ui_events(f"Settings saved to: {settings_file}")
            
            # Update the path label after saving (in case directory was just created)
            self.update_settings_path_label()
            
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save settings: {str(e)}")
            
    def load_settings(self):
        """Load settings from pickle file"""
        try:
            settings_file = get_settings_file_path()
            if settings_file.exists():
                with open(settings_file, 'rb') as f:
                    settings = pickle.load(f)
                    
                # Load B2B file settings
                if settings.get('b2b_final_path'):
                    self.b2b_final_path = settings['b2b_final_path']
                    if os.path.exists(self.b2b_final_path):
                        self.B2B_final_path.setText(self.b2b_final_path)
                        self.B2B_final_checkbox.setChecked(True)
                    else:
                        # File no longer exists, clear the setting and show placeholder
                        self.b2b_final_path = ""
                        self.B2B_final_path.setText('Click "Browse" to select B2B_final_path.ods')
                        self.B2B_final_checkbox.setChecked(False)
                        
                # Load NON TLE file settings
                if settings.get('non_tle_path'):
                    self.non_tle_path = settings['non_tle_path']
                    if os.path.exists(self.non_tle_path):
                        self.nonTLE_path.setText(self.non_tle_path)
                        self.nonTLE_checkbox.setChecked(True)
                    else:
                        # File no longer exists, clear the setting and show placeholder
                        self.non_tle_path = ""
                        self.nonTLE_path.setText('Click "Browse" to select NON_TLE_tenants_list.ods')
                        self.nonTLE_checkbox.setChecked(False)
                        
                # Load Cloudinary tags file settings
                if settings.get('cloudinary_tags_path'):
                    self.cloudinary_tags_path = settings['cloudinary_tags_path']
                    if os.path.exists(self.cloudinary_tags_path):
                        self.cloudinaryTags_path.setText(self.cloudinary_tags_path)
                        self.cloudinaryTags_checkbox.setChecked(True)
                    else:
                        # File no longer exists, clear the setting and show placeholder
                        self.cloudinary_tags_path = ""
                        self.cloudinaryTags_path.setText('Click "Browse" to select Cloudinary_tags.ods')
                        self.cloudinaryTags_checkbox.setChecked(False)
                        
                # Load Buildings file settings
                if settings.get('buildings_path'):
                    self.buildings_file_path = settings['buildings_path']
                    if os.path.exists(self.buildings_file_path):
                        self.buildings_path.setText(self.buildings_file_path)
                        self.buildings_checkbox.setChecked(True)
                    else:
                        # File no longer exists, clear the setting and show placeholder
                        self.buildings_file_path = ""
                        self.buildings_path.setText('Click "Browse" to select Buildings_and_Streets.ods')
                        self.buildings_checkbox.setChecked(False)
                
                # Load Cloudinary settings
                self.load_cloudinary_settings(settings)
                        
                # Update ALL SET checkbox
                self.update_all_set_checkbox()
            else:
                # No settings file exists, set initial placeholder text
                self.set_initial_placeholders()
                        
        except Exception as e:
            debug_errors(f"Could not load settings: {str(e)}")
            # Set initial placeholder text on error
            self.set_initial_placeholders()
            
    def load_cloudinary_settings(self, settings):
        """Load Cloudinary settings from the settings dictionary"""
        # Load log folder path
        if settings.get('cloudinary_log_folder'):
            self.log_folder_path = settings['cloudinary_log_folder']
            if os.path.exists(self.log_folder_path):
                self.logFile_path.setText(self.log_folder_path)
            else:
                # Folder no longer exists, clear the setting
                self.log_folder_path = ""
                self.logFile_path.setText("Click 'Locate..' to select folder")
        else:
            self.logFile_path.setText("Click 'Locate..' to select folder")

        # Load Cloudinary API settings
        self.cloudName_text.setText(settings.get('cloudinary_cloud_name', ''))
        self.apiKey_text.setText(settings.get('cloudinary_api_key', ''))
        self.apiSecret_text.setText(settings.get('cloudinary_api_secret', ''))
        
        # Update test button state after loading settings
        self.update_test_button_state()
        self.maxSizeLineEdit.setText(settings.get('cloudinary_max_size', '3.2'))
        
        # Load longest side setting
        if hasattr(self, 'longestSideEdit'):
            self.longestSideEdit.setText(settings.get('cloudinary_longest_side', '4000'))
        
        # Store values in instance variables
        self.cloudinary_cloud_name = settings.get('cloudinary_cloud_name', '')
        self.cloudinary_api_key = settings.get('cloudinary_api_key', '')
        self.cloudinary_api_secret = settings.get('cloudinary_api_secret', '')
            
    def set_initial_placeholders(self):
        """Set initial placeholder text for file paths when no settings exist"""
        # HappyTag file placeholders
        self.B2B_final_path.setText('Click "Browse" to select B2B_final_path.ods')
        self.nonTLE_path.setText('Click "Browse" to select NON_TLE_tenants_list.ods')
        self.cloudinaryTags_path.setText('Click "Browse" to select Cloudinary_tags.ods')
        self.buildings_path.setText('Click "Browse" to select Buildings_and_Streets.ods')
        
        # Cloudinary placeholders
        self.logFile_path.setText("Click 'Locate..' to select folder")
        self.cloudName_text.setText("")
        self.apiKey_text.setText("")
        self.apiSecret_text.setText("")
        self.maxSizeLineEdit.setText("3.2")
        
        # Set default value for longest side if widget exists
        if hasattr(self, 'longestSideEdit'):
            self.longestSideEdit.setText("4000")
        
        # All checkboxes unchecked initially
        self.B2B_final_checkbox.setChecked(False)
        self.nonTLE_checkbox.setChecked(False)
        self.cloudinaryTags_checkbox.setChecked(False)
        self.buildings_checkbox.setChecked(False)
        self.update_all_set_checkbox()
        
        # Update test button state
        self.update_test_button_state()
        
    def setup_clickable_paths(self):
        """Setup clickable functionality for path labels"""
        # Make settings path label clickable
        if hasattr(self, 'settingsPathLabel'):
            self.settingsPathLabel.setCursor(QCursor(Qt.PointingHandCursor))
            self.settingsPathLabel.setStyleSheet("QLabel { color: blue; text-decoration: underline; }")
            self.settingsPathLabel.mousePressEvent = lambda event: self.open_settings_folder()
            self.settingsPathLabel.setToolTip("Click to open the settings folder in your file manager")
            debug_ui_events("Settings path label made clickable")
        
        # Make log folder path label clickable
        if hasattr(self, 'logFile_path'):
            self.logFile_path.setCursor(QCursor(Qt.PointingHandCursor))
            self.logFile_path.setStyleSheet("QLabel { color: blue; text-decoration: underline; }")
            self.logFile_path.mousePressEvent = lambda event: self.open_log_folder()
            self.logFile_path.setToolTip("Click to open the log folder in your file manager")
            debug_ui_events("Log file path label made clickable")
    
    def setup_input_validators(self):
        """Setup input validators for numeric fields"""
        from PyQt5.QtGui import QDoubleValidator, QIntValidator
        
        # Validator for max size (decimal MB values)
        double_validator = QDoubleValidator(0.1, 999.0, 2)  # Min 0.1MB, Max 999MB, 2 decimal places
        self.maxSizeLineEdit.setValidator(double_validator)
        self.maxSizeLineEdit.setPlaceholderText("3.2")
        
        # Validator for longest side (integer pixels)
        int_validator = QIntValidator(100, 50000)  # Min 100px, Max 50000px
        if hasattr(self, 'longestSideEdit'):
            self.longestSideEdit.setValidator(int_validator)
            self.longestSideEdit.setPlaceholderText("4000")
        
        debug_ui_events("Input validators configured for numeric fields")
    
    def open_settings_folder(self):
        """Open the settings folder in the system file manager"""
        settings_folder = None
        try:
            settings_file_path = get_settings_file_path()
            settings_folder = settings_file_path.parent
            
            if settings_folder.exists():
                self.open_folder_in_file_manager(str(settings_folder))
                debug_ui_events(f"Opened settings folder: {settings_folder}")
            else:
                # Silent failure - folder doesn't exist yet, which is normal
                debug_ui_events(f"Settings folder does not exist yet: {settings_folder}")
        except Exception as e:
            debug_errors(f"Error opening settings folder: {e}")
            folder_path = str(settings_folder) if settings_folder else "Unknown path"
            QMessageBox.warning(self, "Error", 
                              f"Could not open settings folder.\n\n"
                              f"You can manually navigate to:\n{folder_path}\n\n"
                              f"Error details: {str(e)}")
    
    def open_log_folder(self):
        """Open the log folder in the system file manager"""
        try:
            # Get the displayed text from the label
            displayed_text = self.logFile_path.text() if hasattr(self, 'logFile_path') else "No label"
            
            debug_ui_events(f"open_log_folder called")
            debug_ui_events(f"  self.log_folder_path: '{self.log_folder_path}'")
            debug_ui_events(f"  Label displayed text: '{displayed_text}'")
            debug_ui_events(f"  Path exists check: {os.path.exists(self.log_folder_path) if self.log_folder_path else 'N/A - empty path'}")
            
            # Determine which path to use - prefer self.log_folder_path, fallback to displayed text
            path_to_use = None
            if self.log_folder_path and os.path.exists(self.log_folder_path):
                path_to_use = self.log_folder_path
            elif displayed_text and displayed_text != "Click 'Locate..' to select folder" and os.path.exists(displayed_text):
                path_to_use = displayed_text
                debug_ui_events(f"Using displayed text as fallback path: {displayed_text}")
            
            if path_to_use:
                debug_ui_events(f"Opening folder: {path_to_use}")
                self.open_folder_in_file_manager(path_to_use)
                debug_ui_events(f"Successfully opened folder: {path_to_use}")
            else:
                # Show error dialog when log folder is not configured
                debug_ui_events(f"No valid log folder path found")
                QMessageBox.information(self, "Log Folder Not Set", 
                                      "The log folder has not been configured yet.\n\n"
                                      "Please click the 'Locate..' button to select a folder for storing logs.")
        except Exception as e:
            debug_errors(f"Error opening log folder: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Could not open log folder.\n\n"
                              f"You can manually navigate to:\n{self.log_folder_path if self.log_folder_path else 'No path set'}\n\n"
                              f"Error details: {str(e)}")
    
    def open_folder_in_file_manager(self, folder_path):
        """Open a folder in the system's default file manager"""
        try:
            debug_ui_events(f"open_folder_in_file_manager called with path: '{folder_path}'")
            debug_ui_events(f"Path type: {type(folder_path)}")
            debug_ui_events(f"Path exists: {os.path.exists(folder_path)}")
            
            current_platform = platform.system().lower()
            
            if current_platform == 'windows':
                # Windows: Convert forward slashes to backslashes for explorer compatibility
                windows_path = os.path.normpath(folder_path)
                debug_ui_events(f"Normalized Windows path: '{windows_path}'")
                
                # Windows: use explorer (don't check return code as explorer sometimes returns non-zero even on success)
                debug_ui_events(f"Executing: explorer '{windows_path}'")
                result = subprocess.run(['explorer', windows_path], capture_output=True, text=True)
                debug_ui_events(f"Explorer command result: return code {result.returncode}")
                debug_ui_events(f"Explorer stdout: {result.stdout}")
                debug_ui_events(f"Explorer stderr: {result.stderr}")
                # Don't raise exception for non-zero return codes from explorer
                
            elif current_platform == 'darwin':
                # macOS: use open
                result = subprocess.run(['open', folder_path], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"open command failed with return code {result.returncode}: {result.stderr}")
                    
            elif current_platform == 'linux':
                # Linux: try xdg-open (most common), fallback to other options
                try:
                    result = subprocess.run(['xdg-open', folder_path], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise subprocess.CalledProcessError(result.returncode, 'xdg-open', result.stderr)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Try alternatives for different desktop environments
                    for file_manager in ['nautilus', 'dolphin', 'thunar', 'pcmanfm']:
                        try:
                            result = subprocess.run([file_manager, folder_path], capture_output=True, text=True)
                            if result.returncode == 0:
                                break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
                    else:
                        raise Exception("No suitable file manager found")
            else:
                raise Exception(f"Unsupported platform: {current_platform}")
                
            debug_ui_events(f"Successfully opened folder: {folder_path}")
            
        except Exception as e:
            debug_errors(f"Failed to open folder {folder_path}: {e}")
            raise
        
    def update_settings_path_label(self):
        """Update the settings path label to show where the settings file is stored"""
        try:
            settings_file_path = get_settings_file_path()
            # Check if the widget exists before trying to update it
            if hasattr(self, 'settingsPathLabel'):
                # Use forward slashes for better readability, even on Windows
                display_path = str(settings_file_path).replace('\\', '/')
                self.settingsPathLabel.setText(display_path)
                
                # Add a helpful tooltip (updated for clickability)
                self.settingsPathLabel.setToolTip(
                    "This is where HappyTag stores your settings file.\n"
                    f"Full path: {display_path}\n"
                    "The file contains all your configuration preferences.\n"
                    "Click to open the settings folder in your file manager."
                )
                
                debug_ui_events(f"Settings path label updated: {display_path}")
            else:
                debug_ui_events("settingsPathLabel widget not found in UI")
        except Exception as e:
            debug_errors(f"Error updating settings path label: {e}")
            if hasattr(self, 'settingsPathLabel'):
                self.settingsPathLabel.setText("Error: Could not determine settings path")
                self.settingsPathLabel.setToolTip("There was an error determining the settings file location.")
                
    @staticmethod
    def get_settings_path_display():
        """Get the settings file path for display purposes"""
        try:
            settings_file_path = get_settings_file_path()
            return str(settings_file_path).replace('\\', '/')
        except Exception:
            return "Error: Could not determine settings path"
            
    @staticmethod
    def get_saved_settings():
        """Static method to get saved settings from anywhere in the application"""
        try:
            settings_file = get_settings_file_path()
            if settings_file.exists():
                with open(settings_file, 'rb') as f:
                    settings = pickle.load(f)
                return settings
        except Exception as e:
            debug_errors(f"Could not load settings: {str(e)}")
        return {
            # HappyTag settings
            'b2b_final_path': '', 
            'non_tle_path': '', 
            'cloudinary_tags_path': '', 
            'buildings_path': '',
            # Cloudinary settings
            'cloudinary_log_folder': '',
            'cloudinary_cloud_name': '',
            'cloudinary_api_key': '',
            'cloudinary_api_secret': '',
            'cloudinary_max_size': '',
            'cloudinary_longest_side': '4000',
            # UI preferences
            'text_size': 12,
            'last_file_path': '',
            'last_folder_path': ''
        }

    @staticmethod
    def get_cloudinary_settings():
        """Static method to get only Cloudinary settings"""
        settings = SettingsDialog.get_saved_settings()
        return {
            'log_folder': settings.get('cloudinary_log_folder', ''),
            'cloud_name': settings.get('cloudinary_cloud_name', ''),
            'api_key': settings.get('cloudinary_api_key', ''),
            'api_secret': settings.get('cloudinary_api_secret', ''),
            'max_size': settings.get('cloudinary_max_size', '3.2'),
            'longest_side': settings.get('cloudinary_longest_side', '4000')
        }
        
    @staticmethod
    def is_cloudinary_configured():
        """Check if Cloudinary is properly configured"""
        cloudinary_settings = SettingsDialog.get_cloudinary_settings()
        return (
            cloudinary_settings['cloud_name'] and
            cloudinary_settings['api_key'] and
            cloudinary_settings['api_secret']
        )

    @staticmethod
    def save_ui_preferences(text_size=None, last_path=None):
        """Save UI preferences (text size, last path) without opening the settings dialog"""
        try:
            # Load existing settings first
            settings = SettingsDialog.get_saved_settings()
            
            # Update only the provided preferences
            if text_size is not None:
                settings['text_size'] = text_size
            if last_path is not None:
                settings['last_path'] = last_path
            
            # Save back to file
            settings_file = get_settings_file_path()
            with open(settings_file, 'wb') as f:
                pickle.dump(settings, f)
            debug_ui_events(f"UI preferences saved: text_size={text_size}, last_path={last_path}")
            
        except Exception as e:
            debug_errors(f"Could not save UI preferences: {str(e)}")

    @staticmethod
    def get_ui_preferences():
        """Get UI preferences (text size, last path)"""
        settings = SettingsDialog.get_saved_settings()
        return {
            'text_size': settings.get('text_size', 12),
            'last_path': settings.get('last_path', '')
        }
