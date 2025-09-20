import os
import pickle
import sys
from pathlib import Path
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
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
        self.cloudinary_max_size = ""
        
        # Connect existing HappyTag buttons to file selection
        self.pushButton.clicked.connect(self.select_b2b_file)
        self.pushButton_2.clicked.connect(self.select_non_tle_file)
        self.pushButton_3.clicked.connect(self.select_cloudinary_tags_file)
        self.pushButton_4.clicked.connect(self.select_buildings_file)
        
        # Connect Cloudinary buttons and controls
        self.logFolder_button.clicked.connect(self.select_log_folder)
        self.maxSizeSetButton.clicked.connect(self.set_max_size)
        
        # Connect OK/Cancel buttons
        self.buttonBox.accepted.connect(self.accept_settings)
        self.buttonBox.rejected.connect(self.reject)
        
        # Load saved settings
        self.load_settings()
        
        # Update ALL SET checkbox initially
        self.update_all_set_checkbox()
        
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
            
    def set_max_size(self):
        """Handle max size set button click"""
        try:
            max_size = float(self.maxSizeLineEdit.text())
            if max_size <= 0:
                QMessageBox.warning(self, "Invalid Size", "Max size must be greater than 0.")
                return
            
            # Store the max size value
            self.cloudinary_max_size = str(max_size)
            QMessageBox.information(self, "Max Size Set", f"Max size set to {max_size} MB")
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for max size.")
            
    def validate_cloudinary_settings(self):
        """Validate Cloudinary settings"""
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
        if not self.cloudName_text.text().strip():
            QMessageBox.warning(self, "Cloudinary Validation", "Cloud Name is required for Cloudinary integration.")
            return False
            
        if not self.apiKey_text.text().strip():
            QMessageBox.warning(self, "Cloudinary Validation", "API Key is required for Cloudinary integration.")
            return False
            
        if not self.apiSecret_text.text().strip():
            QMessageBox.warning(self, "Cloudinary Validation", "API Secret is required for Cloudinary integration.")
            return False
            
        # Validate max size if provided
        if self.maxSizeLineEdit.text().strip():
            try:
                max_size = float(self.maxSizeLineEdit.text())
                if max_size <= 0:
                    QMessageBox.warning(self, "Cloudinary Validation", "Max size must be greater than 0.")
                    return False
            except ValueError:
                QMessageBox.warning(self, "Cloudinary Validation", "Max size must be a valid number.")
                return False
                
        return True
            
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
        if self.validate_files() and self.validate_cloudinary_settings():
            self.save_settings()
            self.accept()
        # If validation fails, dialog stays open
            
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
            'cloudinary_max_size': self.maxSizeLineEdit.text().strip()
        }
        
        try:
            settings_file = get_settings_file_path()
            with open(settings_file, 'wb') as f:
                pickle.dump(settings, f)
            debug_ui_events(f"Settings saved to: {settings_file}")
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
                self.logFile_path.setText("Click 'Log Folder..' to select folder")
        else:
            self.logFile_path.setText("Click 'Log Folder..' to select folder")
            
        # Load Cloudinary API settings
        self.cloudName_text.setText(settings.get('cloudinary_cloud_name', ''))
        self.apiKey_text.setText(settings.get('cloudinary_api_key', ''))
        self.apiSecret_text.setText(settings.get('cloudinary_api_secret', ''))
        self.maxSizeLineEdit.setText(settings.get('cloudinary_max_size', ''))
        
        # Store values in instance variables
        self.cloudinary_cloud_name = settings.get('cloudinary_cloud_name', '')
        self.cloudinary_api_key = settings.get('cloudinary_api_key', '')
        self.cloudinary_api_secret = settings.get('cloudinary_api_secret', '')
        self.cloudinary_max_size = settings.get('cloudinary_max_size', '')
            
    def set_initial_placeholders(self):
        """Set initial placeholder text for file paths when no settings exist"""
        # HappyTag file placeholders
        self.B2B_final_path.setText('Click "Browse" to select B2B_final_path.ods')
        self.nonTLE_path.setText('Click "Browse" to select NON_TLE_tenants_list.ods')
        self.cloudinaryTags_path.setText('Click "Browse" to select Cloudinary_tags.ods')
        self.buildings_path.setText('Click "Browse" to select Buildings_and_Streets.ods')
        
        # Cloudinary placeholders
        self.logFile_path.setText("Click 'Log Folder..' to select folder")
        self.cloudName_text.setText("")
        self.apiKey_text.setText("")
        self.apiSecret_text.setText("")
        self.maxSizeLineEdit.setText("")
        
        # All checkboxes unchecked initially
        self.B2B_final_checkbox.setChecked(False)
        self.nonTLE_checkbox.setChecked(False)
        self.cloudinaryTags_checkbox.setChecked(False)
        self.buildings_checkbox.setChecked(False)
        self.update_all_set_checkbox()
            
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
            'cloudinary_max_size': ''
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
            'max_size': settings.get('cloudinary_max_size', '')
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
