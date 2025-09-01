import os
import pickle
import sys
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5 import uic

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(resource_path('ui/settingsDialog.ui'), self)
        
        # File paths
        self.b2b_final_path = ""
        self.non_tle_path = ""
        self.cloudinary_tags_path = ""
        self.buildings_file_path = ""
        
        # Connect buttons to file selection
        self.pushButton.clicked.connect(self.select_b2b_file)
        self.pushButton_2.clicked.connect(self.select_non_tle_file)
        self.pushButton_3.clicked.connect(self.select_cloudinary_tags_file)
        self.pushButton_4.clicked.connect(self.select_buildings_file)
        
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
            "Spreadsheet files (*.ods *.xlsx);;All files (*.*)"
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
            "Spreadsheet files (*.ods *.xlsx);;All files (*.*)"
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
            "Spreadsheet files (*.ods *.xlsx);;All files (*.*)"
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
            "Spreadsheet files (*.ods *.xlsx);;All files (*.*)"
        )
        
        if file_path:
            self.buildings_file_path = file_path
            self.buildings_path.setText(file_path)
            self.buildings_checkbox.setChecked(True)
            self.update_all_set_checkbox()
            
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
            elif not self.b2b_final_path.lower().endswith(('.ods', '.xlsx')):
                valid_b2b = False
                self.B2B_final_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "B2B + B2C final file must be .ods or .xlsx format.")
        
        # Validate NON TLE file if selected
        if self.nonTLE_checkbox.isChecked():
            if not self.non_tle_path or not os.path.exists(self.non_tle_path):
                valid_non_tle = False
                self.nonTLE_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "NON TLE tenants list file does not exist or is invalid.")
            elif not self.non_tle_path.lower().endswith(('.ods', '.xlsx')):
                valid_non_tle = False
                self.nonTLE_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "NON TLE tenants list file must be .ods or .xlsx format.")
        
        # Validate Cloudinary tags file if selected
        if self.cloudinaryTags_checkbox.isChecked():
            if not self.cloudinary_tags_path or not os.path.exists(self.cloudinary_tags_path):
                valid_cloudinary = False
                self.cloudinaryTags_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Cloudinary tags file does not exist or is invalid.")
            elif not self.cloudinary_tags_path.lower().endswith(('.ods', '.xlsx')):
                valid_cloudinary = False
                self.cloudinaryTags_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Cloudinary tags file must be .ods or .xlsx format.")
        
        # Validate Buildings file if selected
        if self.buildings_checkbox.isChecked():
            if not self.buildings_file_path or not os.path.exists(self.buildings_file_path):
                valid_buildings = False
                self.buildings_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Buildings and Streets file does not exist or is invalid.")
            elif not self.buildings_file_path.lower().endswith(('.ods', '.xlsx')):
                valid_buildings = False
                self.buildings_checkbox.setChecked(False)
                QMessageBox.warning(self, "Validation Error", 
                                  "Buildings and Streets file must be .ods or .xlsx format.")
        
        # Update ALL SET checkbox after validation
        self.update_all_set_checkbox()
        
        return valid_b2b and valid_non_tle and valid_cloudinary and valid_buildings
        
    def accept_settings(self):
        """Handle OK button click"""
        if self.validate_files():
            self.save_settings()
            self.accept()
        # If validation fails, dialog stays open
            
    def save_settings(self):
        """Save settings to pickle file"""
        settings = {
            'b2b_final_path': self.b2b_final_path if self.B2B_final_checkbox.isChecked() else "",
            'non_tle_path': self.non_tle_path if self.nonTLE_checkbox.isChecked() else "",
            'cloudinary_tags_path': self.cloudinary_tags_path if self.cloudinaryTags_checkbox.isChecked() else "",
            'buildings_path': self.buildings_file_path if self.buildings_checkbox.isChecked() else ""
        }
        
        try:
            with open('settings.pkl', 'wb') as f:
                pickle.dump(settings, f)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save settings: {str(e)}")
            
    def load_settings(self):
        """Load settings from pickle file"""
        try:
            if os.path.exists('settings.pkl'):
                with open('settings.pkl', 'rb') as f:
                    settings = pickle.load(f)
                    
                # Load B2B file settings
                if settings.get('b2b_final_path'):
                    self.b2b_final_path = settings['b2b_final_path']
                    if os.path.exists(self.b2b_final_path):
                        self.B2B_final_path.setText(self.b2b_final_path)
                        self.B2B_final_checkbox.setChecked(True)
                    else:
                        # File no longer exists
                        self.B2B_final_path.setText("File not found")
                        self.B2B_final_checkbox.setChecked(False)
                        
                # Load NON TLE file settings
                if settings.get('non_tle_path'):
                    self.non_tle_path = settings['non_tle_path']
                    if os.path.exists(self.non_tle_path):
                        self.nonTLE_path.setText(self.non_tle_path)
                        self.nonTLE_checkbox.setChecked(True)
                    else:
                        # File no longer exists
                        self.nonTLE_path.setText("File not found")
                        self.nonTLE_checkbox.setChecked(False)
                        
                # Load Cloudinary tags file settings
                if settings.get('cloudinary_tags_path'):
                    self.cloudinary_tags_path = settings['cloudinary_tags_path']
                    if os.path.exists(self.cloudinary_tags_path):
                        self.cloudinaryTags_path.setText(self.cloudinary_tags_path)
                        self.cloudinaryTags_checkbox.setChecked(True)
                    else:
                        # File no longer exists
                        self.cloudinaryTags_path.setText("File not found")
                        self.cloudinaryTags_checkbox.setChecked(False)
                        
                # Load Buildings file settings
                if settings.get('buildings_path'):
                    self.buildings_file_path = settings['buildings_path']
                    if os.path.exists(self.buildings_file_path):
                        self.buildings_path.setText(self.buildings_file_path)
                        self.buildings_checkbox.setChecked(True)
                    else:
                        # File no longer exists
                        self.buildings_path.setText("File not found")
                        self.buildings_checkbox.setChecked(False)
                        
                # Update ALL SET checkbox
                self.update_all_set_checkbox()
            else:
                # No settings file exists, try to load bundled defaults
                self.try_load_bundled_defaults()
                        
        except Exception as e:
            print(f"Could not load settings: {str(e)}")
            # Try to set default paths to bundled files
            self.try_load_bundled_defaults()
            
    def try_load_bundled_defaults(self):
        """Try to load default bundled files"""
        try:
            # Check for bundled default files
            b2b_default = resource_path('docs/B2B + B2C final.ods')
            non_tle_default = resource_path('docs/NON TLE tenants list.ods')
            buildings_default = resource_path('docs/Buildings and ssssStreets.ods')
            
            # B2B + B2C final file
            if os.path.exists(b2b_default):
                self.b2b_final_path = b2b_default
                self.B2B_final_path.setText(b2b_default)
                self.B2B_final_checkbox.setChecked(True)
            else:
                self.B2B_final_path.setText('locate "B2B + B2C final.ods"')
                self.B2B_final_checkbox.setChecked(False)
            
            # NON TLE tenants list file
            if os.path.exists(non_tle_default):
                self.non_tle_path = non_tle_default
                self.nonTLE_path.setText(non_tle_default)
                self.nonTLE_checkbox.setChecked(True)
            else:
                self.nonTLE_path.setText('locate "NON TLE tenants list.ods"')
                self.nonTLE_checkbox.setChecked(False)
            
            # Buildings and Streets file
            if os.path.exists(buildings_default):
                self.buildings_file_path = buildings_default
                self.buildings_path.setText(buildings_default)
                self.buildings_checkbox.setChecked(True)
            else:
                self.buildings_path.setText('locate "Buildings and Streets.ods"')
                self.buildings_checkbox.setChecked(False)
            
            # Cloudinary tags (no default bundled)
            self.cloudinaryTags_path.setText('locate "Cloudinary tags.ods"')
            self.cloudinaryTags_checkbox.setChecked(False)
            
            self.update_all_set_checkbox()
            
        except Exception as e:
            print(f"Could not load bundled defaults: {str(e)}")
            # Set fallback values
            self.B2B_final_path.setText('locate "B2B + B2C final.ods"')
            self.nonTLE_path.setText('locate "NON TLE tenants list.ods"')
            self.cloudinaryTags_path.setText('locate "Cloudinary tags.ods"')
            self.buildings_path.setText('locate "Buildings and Streets.ods"')
            self.B2B_final_checkbox.setChecked(False)
            self.nonTLE_checkbox.setChecked(False)
            self.cloudinaryTags_checkbox.setChecked(False)
            self.buildings_checkbox.setChecked(False)
            self.update_all_set_checkbox()
            
    @staticmethod
    def get_saved_settings():
        """Static method to get saved settings from anywhere in the application"""
        try:
            if os.path.exists('settings.pkl'):
                with open('settings.pkl', 'rb') as f:
                    settings = pickle.load(f)
                return settings
        except Exception as e:
            print(f"Could not load settings: {str(e)}")
        return {'b2b_final_path': '', 'non_tle_path': '', 'cloudinary_tags_path': '', 'buildings_path': ''}
