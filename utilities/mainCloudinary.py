# cd "/Volumes/Marketing/Simone Morciano/python working folder/myApp/design/"
# cd "/Volumes/Marketing/Simone Morciano/python working folder/myApp-2/"
# python3 main.py

# cd "/Users/simone/Library/Python/3.13/bin/pyside6-uic"
# cd "/Users/simone/Library/Python/3.13/bin"
# pyside6-uic "/Volumes/Marketing/Simone Morciano/python working folder/myApp/design/app_design.ui" -o "/Volumes/Marketing/Simone Morciano/python working folder/myApp/design/app_design.py"


# main.py
import sys
import os
import pickle
sys.path.append(os.path.join(os.path.dirname(__file__), 'design'))
import shutil
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QFileDialog, QProgressBar, QLabel
from PyQt5.QtCore import QDir, QThread, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QPixmap, QDoubleValidator
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from ui.cloudinaryMainDialog import Ui_CloudinaryMainDialog  # Import the generated UI class
from ui.cloudinarySettingsDialog import Ui_cloudinarySettingsDialog
from ui.cloudinaryCreditsBar import CloudinaryCreditsBar




from utilities.cloudinary_update_v13 import CloudinaryUpdater, FOLDER_MODE, FILES_MODE, SINGLE_FOLDER_MODE




STORAGE_COLOUR = "#b83232"
TRANSFORMATIONS_COLOUR = "#32a4ba"
BANDWIDTH_COLOUR = "#dbde3e"

class DragDropArea(QLabel):
    def __init__(self, parent=None, app_instance=None):
        super().__init__(parent)
        self.app_instance = app_instance  # Store the MyApp instance
        self.setText("Drag and drop files here")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px dashed #aaa; font-size: 16px; padding: 20px;")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.handleDroppedFiles(file_paths)
            event.accept()
        else:
            event.ignore()

    def handleDroppedFiles(self, file_paths):
        # Process the dropped files
        # QMessageBox.information(self, "Files Dropped", f"Files:\n{', '.join(file_paths)}")
        print("about to call start assesstment thread")
        if self.app_instance:  # Ensure the app_instance is set
            print(f"app_instance: {self.app_instance}")
            self.app_instance.startAssessmentThread(file_paths, FILES_MODE)
        print("Dropped files:", file_paths)

class Worker(QObject):
    # Signal to emit progress updates
    update_ui_signal = pyqtSignal(str)
    setPreviewImages_signal = pyqtSignal(list)
    beginning_signal = pyqtSignal(list)

    def __init__(self, updater, folder, mode):
        super().__init__()
        self.updater = updater
        self.folder = folder
        self.mode   = mode

    def run(self):
        """Long-running task to sync files."""
        try:
            # Call the sync_files method
            self.updater.sync_files_signal(self.folder, self.mode)
        except Exception as e:
            self.update_ui_signal.emit(f"Error: {e}")

class UploadWorker(QObject):
    # Signal to emit progress updates
    updatePreviewImage_signal = pyqtSignal(str)
    updateResizeInUploadProgressBar_signal = pyqtSignal(int)
    updateProgressBar_signal = pyqtSignal(int)
    updateUiUploadStatus_signal = pyqtSignal(str)
    setUploadPreviewImage_signal = pyqtSignal(str)
    uploadStarting_signal = pyqtSignal(bool)


    def __init__(self, updater):
        super().__init__()
        self.updater = updater
        # forward the signals
        self.updater.updateResizeInUploadProgressBar_signal.connect(self.updateResizeInUploadProgressBar_signal)
        self.updater.updateProgressBar_signal.connect(self.updateProgressBar_signal)
        self.updater.setUploadPreviewImage_signal.connect(self.setUploadPreviewImage_signal)
        self.updater.uploadStarting_signal.connect(self.uploadStarting_signal)

    def run(self):
        """Long-running task to sync files."""
        try:
            # Call the sync_files method
            self.updater.upload_files(self)
        except Exception as e:
            self.updateUiUploadStatus_signal.emit(f"Error: {e}")
            
def print_widget_tree(widget, indent=0):
    print(" " * indent + widget.objectName())
    for child in widget.children():
        if isinstance(child, QtWidgets.QWidget):
            print_widget_tree(child, indent + 4)

class SettingsDialog(QDialog, Ui_cloudinarySettingsDialog):
    def __init__(self, parent=None, cloudinary_updater=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent  # Store the MyApp instance
        self.cloudinary_updater = cloudinary_updater  # Store the CloudinaryUpdater instance

        self.pushButton.clicked.connect(self.logFileFolderChanged)

        # Example usage
        #data_to_save = ["string1", "string2", "string3", "string4"]

        saved_data = load_data()
        if saved_data:
            try:
                if saved_data[0]:
                    self.logFile_path.setText(saved_data[0])
                if saved_data[1]:
                    self.cloudName_text.setText(saved_data[1])
                if saved_data[2]:
                    self.apiKey_text.setText(saved_data[2])
                if saved_data[3]:
                    self.apiSecret_text.setText(saved_data[3])
                if saved_data[4]:
                    self.maxSizeLineEdit.setText(saved_data[4])
            
            except IndexError:
                self.parent.blockUI("Please set your Cloudinary credentials in the settings dialog.")
                # Handle the case where saved_data does not have enough elements")
        else:
            print("No data found SSSSSSSSSSSSSSSSS")
            self.parent.blockUI("Please set your Cloudinary credentials in the settings dialog.")
                

        # Save data and call cloudinary Updater when the dialog is accepted
        self.buttonBox.accepted.connect(self.save_settings)

        # max Size validator
        # Set validator to allow only numbers with 2 decimal places

        print("SONO IN SettingsDialog e chiamo ValidateConfig")

        self.setFieldsValidators()
        self.validateConfig()

    def setFieldsValidators(self):
        # Validator for maxSizeLineEdit: allows only numbers with 2 decimal places
        validatorMaxSize = QDoubleValidator()
        validatorMaxSize.setDecimals(2)
        validatorMaxSize.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.maxSizeLineEdit.setValidator(validatorMaxSize)
        self.maxSizeLineEdit.editingFinished.connect(self.maxSizeChanged)

        # Validator for cloudName_text: text without spaces and not empty
        self.cloudName_text.textChanged.connect(self.cloudNameChanged)

        # Validator for apiKey_text: string of digits, no spaces
        self.apiKey_text.textChanged.connect(self.apiKeyChanged)

        # Validator for apiSecret_text: text without spaces and not empty
        self.apiSecret_text.textChanged.connect(self.apiSecretChanged)

    def cloudNameChanged(self):
        self.validateCloudName()
        self.validateConfig()

    def maxSizeChanged(self):
        self.validateMaxSize()
        self.validateConfig()

    def apiKeyChanged(self):
        self.validateApiKey()
        self.validateConfig()

    def apiSecretChanged(self):
        self.validateApiSecret()
        self.validateConfig()

    def maxSizeChanged(self):
        self.validateMaxSize()
        self.validateConfig()

    def logFileFolderChanged(self):
        self.openLogFilePathDialog()
        self.validateConfig()

    def openLogFilePathDialog(self):
        """Open a folder dialog to select a directory."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", QDir.homePath(), QFileDialog.ShowDirsOnly)

        if folder:
            self.logFile_path.setText(folder)  # Set the selected folder path to the label
        else:
            QMessageBox.warning(self, "No Folder Selected", "No folder was selected.")

    def validateMaxSize(self, silentMode=False):
        text = self.maxSizeLineEdit.text()
        try:
            number = float(text)
            formatted = f"{number:.2f}"  # Ensures 2 decimal places
            self.maxSizeLineEdit.setText(formatted)
            return True
        except ValueError:
            if not silentMode:
                QMessageBox.warning(self, "Invalid Input", "Max size must be a numeric value.")
            self.maxSizeLineEdit.setText("")
            return False

    def validateCloudName(self, silentMode=False):
        text = self.cloudName_text.text()
        if " " in text or not text:
            if not silentMode:
                QMessageBox.warning(self, "Invalid Input", "Cloud Name must not contain spaces and cannot be empty.")
            self.cloudName_text.setText("")
            return False
        else:
            return True

    def validateApiKey(self, silentMode=False):
        text = self.apiKey_text.text()
        if not text.isdigit() or " " in text:
            if not silentMode:
                QMessageBox.warning(self, "Invalid Input", "API Key must be a string of digits with no spaces.")
            self.apiKey_text.setText("")
            return False
        else:
            return True

    def validateApiSecret(self, silentMode=False):
        text = self.apiSecret_text.text()
        if " " in text or not text:
            if not silentMode:
                QMessageBox.warning(self, "Invalid Input", "API Secret must not contain spaces and cannot be empty.")
            self.apiSecret_text.setText("")
            return False
        else:
            return True


    def validateLogFilePath(self, silentMode=False):
        text = self.logFile_path.text()
        if not os.path.exists(text):
            if not silentMode:
                QMessageBox.warning(self, "Invalid Path", "Log file path does not exist.")
            self.logFile_path.setText("")
            return False
        else:
            return True

    def validateConfig(self):
        """Validate the configuration settings."""
        # cloudName_text.text(): add validation
        if self.validateLogFilePath(True):
            if self.validateCloudName(True):
                if self.validateApiKey(True):
                    if self.validateApiSecret(True):
                        if self.validateMaxSize(True):
                            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
                            return True
                       
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        return False
     

    def save_settings(self):
        data_to_save = [
            self.logFile_path.text(),
            self.cloudName_text.text(),
            self.apiKey_text.text(),
            self.apiSecret_text.text(),
            self.maxSizeLineEdit.text()
        ]
        save_data(data_to_save)

        # Call cloud_status using the cloudinary_updater instance
        if self.cloudinary_updater:
            self.cloudinary_updater.setCloudinaryUpdaterConfig(data_to_save)
            self.cloudinary_updater.cloud_status()



################## PICKLE SETTINGS ###################

def get_user_data_path():
    """Get a safe path to save user data in the home directory."""
    home_dir = os.path.expanduser("~")  # Get the user's home directory
    app_data_dir = os.path.join(home_dir, ".cloudinaryUploadAppData")  # Create a hidden folder for your app
    os.makedirs(app_data_dir, exist_ok=True)  # Ensure the directory exists
    return os.path.join(app_data_dir, "user_config.pkl")  # Path to the data file

def save_data(data):
    """Save data to a binary file."""
    file_path = get_user_data_path()
    with open(file_path, "wb") as file:
        pickle.dump(data, file)
    print(f"Data saved to {file_path}")

def load_data():
    """Load data from a binary file."""
    file_path = get_user_data_path()
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            data = pickle.load(file)
        print(f"Data loaded from {file_path}")
        return data
    else:
        print("No data file found.")
        return None
    
################## PICKLE SETTINGS ENDS ###################

class MyApp(QDialog, Ui_CloudinaryMainDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Set up the UI from the design file

        # folder or files uplaod mode
        self.synch_mode = 0

        # Create an instance of CloudinaryUpdater
        self.cloudinary_updater = CloudinaryUpdater()

        print("STO PER INIZIALIZZARE SETTINGS DIALOG")
        self.settings_dialog = SettingsDialog(parent=self, cloudinary_updater=self.cloudinary_updater)


        # Load the data
        retrieved_data = load_data()
        print("Retrieved Data:", retrieved_data)

        if not self.settings_dialog.validateConfig():
            self.openSettingsDialog()


 #       if retrieved_data and len(retrieved_data) >= 5:  # Ensure retrieved_data is not None and has at least 4 elements
 #           print("Data loaded successfully.")
 #       else:
 #           print("Data not found")
 #           print("QUI APRO DI FORZA IL SETTINGS DIALOG")
 #           self.openSettingsDialog()  # Open the settings dialog to allow the user to input data
 #           # config_dialog = SettingsDialog(self)
 #           # config_dialog.exec_()  # Show the settings dialog to allow the user to input data

        # print(sys.path)

        # Call this function in __init__ after setupUi
        # print_widget_tree(self)


        # these 3 signals are in the assessment worker
        # update_ui_signal = pyqtSignal(str)
        # setPreviewImages_signal = pyqtSignal(list)
        # beginning_signal = pyqtSignal(list)

        # Connect signals and slots
        self.cloudinary_updater.beginning_signal.connect(self.beginning)
        self.cloudinary_updater.setPreviewImages_signal.connect(self.setPreviewImages)
        self.cloudinary_updater.update_ui_signal.connect(self.update_ui)

        self.cloudinary_updater.assessment_complete_signal.connect(self.on_assessment_complete)
        self.cloudinary_updater.upload_complete_signal.connect(self.on_upload_complete)
        self.cloudinary_updater.update_assessment_bar_signal.connect(self.updateAssessmentBar)
        
        
        self.cloudinary_updater.update_assessment_file_count.connect(self.updateAssessmentFileCount)

        # SIGNALS FOR UPLOAD PHASE
        # updates the uploadResizeCountLabel
        # uploadResizeCount_signal = pyqtSignal(str)
        # update_uploadResizeProgressBar_signal = pyqtSignal(int)  # Signal to update the progress bar
        #self.cloudinary_updater.update_uploadResizeProgressBar_signal               # uploadResizeCountLabel
        # self.cloudinary_updater.updateResizeInUploadProgressBar_signal.connect(self.updateUploadResizeProgressBar)

        # Credits bars are created by the UI file - just make them visible and set properties
        print("DEBUG: Setting up credits bars that already exist from UI file")
        
        # The credits bars should already exist from setupUi call
        if hasattr(self, 'creditsBar'):
            print(f"DEBUG: Found creditsBar from UI file")
            # Set proper size policy to prevent it from expanding too much
            self.creditsBar.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
            self.creditsBar.setMaximumWidth(300)  # Prevent it from taking full width
            # Remove any stylesheet that might hide it
            self.creditsBar.setStyleSheet("")
            # Force visibility
            self.creditsBar.setVisible(True)
            self.creditsBar.show()
            self.creditsBar.update()
            print(f"DEBUG: creditsBar visible after forcing: {self.creditsBar.isVisible()}")
        else:
            print("ERROR: creditsBar not found from UI file!")
            
        if hasattr(self, 'creditsBar_assessment'):
            print(f"DEBUG: Found creditsBar_assessment from UI file")
            # Set proper size policy to prevent it from expanding too much  
            self.creditsBar_assessment.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
            self.creditsBar_assessment.setMaximumWidth(300)  # Prevent it from taking full width
            self.creditsBar_assessment.setVisible(False)  # Should be invisible at launch
            # Set the same colors as the main creditsBar
            self.creditsBar_assessment.setColors(STORAGE_COLOUR, TRANSFORMATIONS_COLOUR, BANDWIDTH_COLOUR)
            print(f"DEBUG: creditsBar_assessment visible: {self.creditsBar_assessment.isVisible()}")
        else:
            print("ERROR: creditsBar_assessment not found from UI file!")
        
        # Setup cloudinary updater and connect signals
        print(f"Main window layout: {type(self.layout()) if self.layout() else 'No layout'}")
        if self.layout():
            print(f"Main layout children count: {self.layout().count()}")
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item:
                    widget = item.widget()
                    layout = item.layout()
                    print(f"  Item {i}: {type(widget) if widget else type(layout) if layout else 'Unknown'}")
                    
        # Check if gridLayout exists and its structure
        if hasattr(self, 'gridLayout'):
            print(f"GridLayout found: {type(self.gridLayout)}")
            print(f"GridLayout parent: {type(self.gridLayout.parent()) if self.gridLayout.parent() else 'No parent'}")
            print(f"GridLayout items count: {self.gridLayout.count()}")
            print("GridLayout contents:")
            for i in range(self.gridLayout.count()):
                item = self.gridLayout.itemAt(i)
                if item:
                    row, col, rowspan, colspan = self.gridLayout.getItemPosition(i)
                    widget = item.widget()
                    print(f"  Position ({row},{col}) span({rowspan},{colspan}): {type(widget).__name__ if widget else 'Layout/Spacer'}")
                    if widget and hasattr(widget, 'objectName'):
                        print(f"    Object name: {widget.objectName()}")
        else:
            print("GridLayout NOT found!")
            
        print(f"DEBUG: Looking for creditsBar attribute: {hasattr(self, 'creditsBar')}")
        if hasattr(self, 'creditsBar'):
            print(f"DEBUG: creditsBar found, type: {type(self.creditsBar)}")
            print(f"DEBUG: creditsBar parent: {type(self.creditsBar.parent())}")
            print(f"DEBUG: creditsBar geometry: {self.creditsBar.geometry()}")
            
            # Check what layout the credits bar is currently in
            current_parent = self.creditsBar.parent()
            current_layout = current_parent.layout() if current_parent else None
            print(f"DEBUG: creditsBar current parent layout: {type(current_layout) if current_layout else 'None'}")
            
            if current_layout:
                print(f"DEBUG: creditsBar current layout item count: {current_layout.count()}")
                # Find position in current layout
                index = current_layout.indexOf(self.creditsBar)
                print(f"DEBUG: creditsBar current position index: {index}")
                if hasattr(current_layout, 'getItemPosition') and index >= 0:
                    try:
                        row, col, rowspan, colspan = current_layout.getItemPosition(index)
                        print(f"DEBUG: creditsBar current grid position: ({row},{col}) span({rowspan},{colspan})")
                    except:
                        print("DEBUG: Could not get grid position (not a grid layout)")
            
            # Just set colors and make visible - NO manual repositioning
            self.creditsBar.setColors(STORAGE_COLOUR, TRANSFORMATIONS_COLOUR, BANDWIDTH_COLOUR)
            print(f"DEBUG: creditsBar set to visible: {self.creditsBar.isVisible()}")
        else:
            print("DEBUG: creditsBar attribute NOT found!")
        
        # print(f"DEBUG: Looking for creditsBar_assessment attribute: {hasattr(self, 'creditsBar_assessment')}")
        # if hasattr(self, 'creditsBar_assessment'):
        #     print(f"DEBUG: creditsBar_assessment found, type: {type(self.creditsBar_assessment)}")
        #     print(f"DEBUG: creditsBar_assessment parent: {type(self.creditsBar_assessment.parent())}")
        #     print(f"DEBUG: creditsBar_assessment geometry: {self.creditsBar_assessment.geometry()}")
        #     
        #     # Check what layout the credits bar is currently in
        #     current_parent = self.creditsBar_assessment.parent()
        #     current_layout = current_parent.layout() if current_parent else None
        #     print(f"DEBUG: creditsBar_assessment current parent layout: {type(current_layout) if current_layout else 'None'}")
        #     
        #     if current_layout:
        #         print(f"DEBUG: creditsBar_assessment current layout item count: {current_layout.count()}")
        #         # Find position in current layout
        #         index = current_layout.indexOf(self.creditsBar_assessment)
        #         print(f"DEBUG: creditsBar_assessment current position index: {index}")
        #         if hasattr(current_layout, 'getItemPosition') and index >= 0:
        #             try:
        #                 row, col, rowspan, colspan = current_layout.getItemPosition(index)
        #                 print(f"DEBUG: creditsBar_assessment current grid position: ({row},{col}) span({rowspan},{colspan})")
        #             except:
        #                 print("DEBUG: Could not get grid position (not a grid layout)")
        #     
        #     # Just set colors - NO manual repositioning 
        #     self.creditsBar_assessment.setColors(STORAGE_COLOUR, TRANSFORMATIONS_COLOUR, BANDWIDTH_COLOUR)
        #     print(f"DEBUG: creditsBar_assessment remains invisible: {self.creditsBar_assessment.isVisible()}")
        # else:
        #     print("DEBUG: creditsBar_assessment attribute NOT found!")
            
        print("="*50)
        print("CREDITS BAR LAYOUT DEBUGGING - PHASE 5: Finding ALL Credits Bars")
        print("="*50)
        
        # Search for ALL widgets that might be credits bars
        all_widgets = self.findChildren(QtWidgets.QWidget)
        credits_bar_widgets = []
        
        for widget in all_widgets:
            # Check by class type
            if type(widget).__name__ == 'CreditsBar':
                credits_bar_widgets.append(widget)
                print(f"Found CreditsBar by type: {widget}")
                print(f"  Object name: {widget.objectName()}")
                print(f"  Parent: {type(widget.parent())}")
                print(f"  Geometry: {widget.geometry()}")
                print(f"  Visible: {widget.isVisible()}")
                print(f"  Parent layout: {type(widget.parent().layout()) if widget.parent() and widget.parent().layout() else 'None'}")
                
                # Check if it's in a layout and where
                if widget.parent() and widget.parent().layout():
                    parent_layout = widget.parent().layout()
                    index = parent_layout.indexOf(widget)
                    print(f"  Layout index: {index}")
                    if hasattr(parent_layout, 'getItemPosition') and index >= 0:
                        try:
                            row, col, rowspan, colspan = parent_layout.getItemPosition(index)
                            print(f"  Layout position: ({row},{col}) span({rowspan},{colspan})")
                        except:
                            print(f"  Layout position: Could not determine (not grid layout)")
                print()
            
            # Also check by object name
            if hasattr(widget, 'objectName') and 'creditsBar' in widget.objectName():
                if widget not in credits_bar_widgets:  # Avoid duplicates
                    credits_bar_widgets.append(widget)
                    print(f"Found credits bar by name: {widget.objectName()}")
                    print(f"  Type: {type(widget)}")
                    print(f"  Parent: {type(widget.parent())}")
                    print(f"  Geometry: {widget.geometry()}")
                    print(f"  Visible: {widget.isVisible()}")
                    print()
        
        print(f"TOTAL CREDITS BAR WIDGETS FOUND: {len(credits_bar_widgets)}")
        print("="*50)
        print("CREDITS BAR LAYOUT DEBUGGING - PHASE 4: Final State")
        print("="*50)
        
        # Final verification of grid layout state
        if hasattr(self, 'gridLayout'):
            print("Final GridLayout contents:")
            for i in range(self.gridLayout.count()):
                item = self.gridLayout.itemAt(i)
                if item:
                    row, col, rowspan, colspan = self.gridLayout.getItemPosition(i)
                    widget = item.widget()
                    print(f"  Position ({row},{col}) span({rowspan},{colspan}): {type(widget).__name__ if widget else 'Layout/Spacer'}")
                    if widget and hasattr(widget, 'objectName'):
                        print(f"    Object name: {widget.objectName()}")
                        if 'creditsBar' in widget.objectName():
                            print(f"    Geometry: {widget.geometry()}")
                            print(f"    Visible: {widget.isVisible()}")
                            print(f"    Size hint: {widget.sizeHint()}")
        
        print("="*50)
        self.lab_colour_credit.setStyleSheet(f"background-color: {STORAGE_COLOUR};")
        self.lab_colour_Transformations.setStyleSheet(f"background-color: {TRANSFORMATIONS_COLOUR};")
        self.lab_colour_Bandwidth.setStyleSheet(f"background-color: {BANDWIDTH_COLOUR};")

        # Replace the QLabel with the DragDropArea
        placeholderDrop = self.findChild(QLabel, "dragDropArea")
        print(f"Placeholder geometry: {placeholderDrop.geometry()}")  # Debugging
        parentTab = placeholderDrop.parent()
        self.newDragDropArea = DragDropArea(parentTab, app_instance=self)
        self.newDragDropArea.setGeometry(placeholderDrop.geometry())
        placeholderDrop.setParent(None)  # Remove the placeholder

        # Initialise widgets in the dialog
        self.inizialiseSelectFiles()



        # Connect buttons to their respective functions
        self.select_files_button.clicked.connect(self.select_files)
        print(f"FOLDER MODE: {FOLDER_MODE}")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.select_single_folder.clicked.connect(self.select_single_folder_method)
        self.settingsButton.clicked.connect(self.openSettingsDialog)
        
        self.confirm_upload.clicked.connect(self.on_confirm_upload)  # Assuming you have a confirm button
        
        # Connect buttonBox Close button to close the application
        self.buttonBox.rejected.connect(self.close)

        # Initialise dialog widgets
        self.assessmentProgressBar = self.findChild(QProgressBar, "AssessmentProgressBar")
        self.uploadResizeProgressBar = self.findChild(QProgressBar, "UploadResizeProgressBar")
        self.uploadProgressBar = self.findChild(QProgressBar, "UploadProgressBar")

        # Check if the progress bar was found
        if self.assessmentProgressBar is not None:
            self.assessmentProgressBar.setValue(0)
        else:
            print("Error: QProgressBar not found!")

         # Check if the progress bar was found
        if self.uploadResizeProgressBar is not None:
            self.uploadResizeProgressBar.setValue(0)
        else:
            print("Error: QProgressBar not found!")

        if self.uploadResizeProgressBar is not None:
            self.uploadResizeProgressBar.setValue(0)
        else:
            print("Error: QProgressBar not found!")

        self.thread = None  # Initialize thread attribute
        self.uploadThread = None

        # Call cloud_status to update the UI with Cloudinary status
        if self.settings_dialog.validateConfig():
            self.inizialiseSelectFiles()
            self.settings_dialog.save_settings()
            self.cloudinary_updater.cloud_status()
        else:
            self.blockUI("Please set your Cloudinary credentials in the settings dialog.")
            # self.cloudinary_updater.cloud_status()


    def openSettingsDialog(self):
        self.settings_dialog.exec_()


    def updateAssessmentFileCount(self, countNumber):
        self.lab_assessingCount.setText(f"Assessing {countNumber} files..")

    def inizialiseSelectFiles(self):
        self.creditsBar.setVisible(True)
        self.select_files_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        self.select_single_folder.setEnabled(True)
        self.confirm_upload.setEnabled(False)
        self.status_label.setEnabled(False)
        self.AssessmentProgressBar.setEnabled(False)
        self.AssessmentProgressBar.setValue(0)
        self.UploadResizeProgressBar.setEnabled(False)
        self.UploadResizeProgressBar.setValue(0)
        self.lab_assessingCount.setText("")
        self.creditsBar_assessment.setVisible(False)
        self.label_5.setVisible(False)
        self.labelImage1.setVisible(False)
        self.labelImage2.setVisible(False)
        self.tabWidget.setCurrentIndex(0)           # # 0 select files  # 1 assessment 2 upload
        self.tabWidget.setTabEnabled(0, True)       # enable select files
        self.tabWidget.setTabEnabled(1, False)      # disable assessment files whilst selecting
        self.tabWidget.setTabEnabled(2, False)      # disable upload files whilst selecting

    def blockUI(self, message):
        self.creditsBar.setVisible(False)
        self.creditsBar_assessment.setVisible(False)
        self.select_files_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        self.select_single_folder.setEnabled(False)
        self.confirm_upload.setEnabled(False)
        self.AssessmentProgressBar.setEnabled(False)
        self.update_ui(message)      # contatins error message

    def updateAssessmentBar(self, value):
        """Handle the completion of the assessment phase."""
        self.assessmentProgressBar.setValue(value)

    def updateUploadResizeProgressBar(self, value):
        """Handle the completion of the assessment phase."""
        self.uploadResizeProgressBar.setValue(value)

    def updateUploadProgressBar(self, value):
        """Handle the completion of the assessment phase."""
        print(f"UPLOADING UPLOAD PROGRESS BAR VALUE: {value}")
        self.uploadProgressBar.setValue(value)

    def uiAssessmentStarted(self):
        self.confirm_upload.setEnabled(False)
        self.status_label.setEnabled(True)
        self.status_label.setText("Assessment in progress")
        self.AssessmentProgressBar.setEnabled(True)
        self.AssessmentProgressBar.setValue(0)
        self.tabWidget.setCurrentIndex(1)    # 0 select files 1 assessment 2 upload
        self.tabWidget.setTabEnabled(1, True)      # disable select files whilst assessing
        self.tabWidget.setTabEnabled(0, False)
        self.tabWidget.setTabEnabled(2, False)

    def select_files(self):
        """Open a file dialog to select multiple image files."""
        self.synch_mode = FILES_MODE
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.jpg *.jpeg *.tiff *.tif *.png, *.gif *.bmp *.webp)")
        file_dialog.setViewMode(QFileDialog.Detail)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            print(f"SELECTED FILES TYPE : {type(selected_files)}")
            if selected_files:
                # QMessageBox.information(self, "Selected Files", f"Selected files:\n{', '.join(selected_files)}")
                self.startAssessmentThread(selected_files, FILES_MODE)
                # self.uiAssessmentStarted()
            else:
                QMessageBox.warning(self, "No Files Selected", "No files were selected.")

    def startAssessmentThread(self, folder, mode):
        self.uiAssessmentStarted()
        print(f"SELECTED FOLDER TYPE : {type(folder)}")

        # Clean up any existing threads first
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
            
        if self.uploadThread is not None:
            self.uploadThread.quit()
            self.uploadThread.wait()
            self.uploadThread = None

        # Create a QThread and a Worker object
        self.thread = QThread()
        self.worker = Worker(self.cloudinary_updater, folder, mode)

        # Move the worker to the thread
        self.worker.moveToThread(self.thread)

        # Connect signals and slots
        self.worker.update_ui_signal.connect(self.update_ui)  # Ensure this connection
        self.worker.beginning_signal.connect(self.beginning)
        self.worker.setPreviewImages_signal.connect(self.setPreviewImages)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: setattr(self, 'thread', None))

        # Start the thread
        self.thread.start()

    def startUploadThread(self):
        # self.uiAssessmentStarted()
        print("starting upload thread")

        # Clean up any existing upload thread first
        if self.uploadThread is not None:
            self.uploadThread.quit()
            self.uploadThread.wait()
            self.uploadThread = None

        # Create a QThread and a Worker object
        self.uploadThread  = QThread()
        self.uploadWorker = UploadWorker(self.cloudinary_updater)

        # Move the worker to the thread
        self.uploadWorker.moveToThread(self.uploadThread)

        ####HERE
        numberOfFilesToResize = len(self.cloudinary_updater.files_to_resize)
        if numberOfFilesToResize > 0:
            self.update_uploadResizeCountLabel(f"Resizing {numberOfFilesToResize} files..")
            self.uploadResizeProgressBar.setEnabled(True)
        else:
            self.update_uploadResizeCountLabel("No files to resize")
            self.uploadResizeCountLabel.setEnabled(False)
            self.uploadResizeProgressBar.setEnabled(False)

        numberOfFilesToUpload = len(self.cloudinary_updater.files_to_upload) + numberOfFilesToResize
        self.update_uploadCountLabel(f"Uploading {numberOfFilesToUpload} files..")
        self.uploadCountLabel.setEnabled(False)
        self.uploadProgressBar.setEnabled(False)
        

        # Connect signals and slots
        self.uploadWorker.updateProgressBar_signal.connect(self.updateUploadProgressBar)  # Ensure this connection
        self.uploadWorker.updateResizeInUploadProgressBar_signal.connect(self.updateUploadResizeProgressBar)  # Ensure this connection
        self.uploadWorker.updateUiUploadStatus_signal.connect(self.update_ui)  # Ensure this connection
        self.uploadWorker.setUploadPreviewImage_signal.connect(self.setUploadPreviewImage)  # Ensure this connection
        
        self.uploadThread.started.connect(self.uploadWorker.run)
        self.uploadThread.finished.connect(self.uploadThread.deleteLater)
        self.uploadThread.finished.connect(lambda: setattr(self, 'uploadThread', None))

        # Start the thread
        self.uploadThread.start()
        

    def uploadStarting(self):
      
        self.update_uploadResizeCountLabel.setEnabled(False)
        self.uploadResizeProgressBar.setEnabled(False)

        self.update_uploadCountLabel.enable(True)
        self.uploadProgressBar.setEnabled(True)

    def select_folder(self):
        """Open a folder dialog to select a directory."""
        self.synch_mode = FOLDER_MODE
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", QDir.homePath(), QFileDialog.ShowDirsOnly)

        if folder:
            self.startAssessmentThread(folder, FOLDER_MODE)
        else:
            QMessageBox.warning(self, "No Folder Selected", "No folder was selected.")

    def select_single_folder_method(self):
        """Open a folder dialog to select a directory (non-recursive scan)."""
        self.synch_mode = SINGLE_FOLDER_MODE
        folder = QFileDialog.getExistingDirectory(self, "Select Single Folder", QDir.homePath(), QFileDialog.ShowDirsOnly)

        if folder:
            self.startAssessmentThread(folder, SINGLE_FOLDER_MODE)
        else:
            QMessageBox.warning(self, "No Folder Selected", "No folder was selected.")

    def update_ui(self, message):
        """Update the UI with the given message."""
        print("updating status label with: ", message)
        self.status_label.setText(message)  # Assuming you have a QLabel named status_label

    def update_uploadResizeCountLabel(self, message):
        self.uploadResizeCountLabel.setText(message)

    def update_uploadCountLabel(self, message):
        self.uploadCountLabel.setText(message)

    def beginning(self, dataList):
        """Update the UI with Cloudinary status."""

        print(f"[DEBUG] mainCloudinary.beginning() called with dataList:")
        for i, field in enumerate(dataList):
            print(f"  dataList[{i}]: {field} (type: {type(field)})")
        
        if dataList[0]:         # true if cloudinary status retrieved
            print(f"[DEBUG] Cloudinary status retrieved successfully")
            self.lab_nowAllowance.setText(dataList[2])
            self.lab_nowUsedCredits.setText(dataList[3])
            self.lab_nowRemainingCredits.setText(dataList[4])
            
            print(f"[DEBUG] About to call creditsBar.setPercentages with:")
            print(f"  Storage (dataList[5]): {dataList[5]}")
            print(f"  Transformations (dataList[6]): {dataList[6]}")
            print(f"  Bandwidth (dataList[7]): {dataList[7]}")
            
            self.creditsBar.setPercentages(dataList[5], dataList[6], dataList[7])
            
            print(f"[DEBUG] creditsBar.setPercentages completed")
            
            self.lab_nowCreditsStorage.setText(f"{dataList[8]:.2f} storage") #float
            self.lab_nowTransformationsCredits.setText(f"{dataList[9]:.2f} transformations") #float
            self.lab_nowCreditsBandwidth.setText(f"{dataList[10]:.2f} bandwidth") #float
            self.lab_nowStored.setText(dataList[11]) #str
            self.lab_nowImageCount.setText(f"{dataList[12]} images") #int
            self.lab_nowAverageSize.setText(dataList[13] + " average size") #str
            self.lab_nowStorageAvailable.setText(dataList[14]) #str
            self.lab_nowImageCountAvailable.setText(f"{dataList[15]} images") #int
            self.lab_nowMaxSize.setText("with " + dataList[16] + " max size") #str

            self.creditsBar.setVisible(True)
            self.select_files_button.setEnabled(True)
            self.select_folder_button.setEnabled(True)

        else:
            self.blockUI(dataList[1])
            

    def setPreviewImages(self, dataList):
        print(f"ABOUT TO SET THIS IMAGE: {dataList[0]}")
        self.set_image(self.labelImage1, dataList[0])   

    def setUploadPreviewImage(self, filePath):
        print(f"ABOUT TO SET THIS IMAGE: {filePath}")
        self.set_image(self.labelImage2, filePath)

    def set_image(self, label, image_path):
        # Load the image using QPixmap
        pixmap = QPixmap(image_path)
        label.setVisible(True)

        # Scale the image to fit the QLabel while maintaining aspect ratio
        label.setPixmap(pixmap.scaled(label.size(), QtCore.Qt.KeepAspectRatio))

    def on_assessment_complete(self, dataList):
        """Handle the completion of the assessment phase."""

        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
        for element in dataList:
            print(f"assessment complete: {element}")

        self.creditsBar_assessment.setPercentages(dataList[6], dataList[7], dataList[8])
        self.creditsBar_assessment.setVisible(True)
        self.label_5.setVisible(True) # "after upload" label
        self.label.setEnabled(False) # "current status" label
        self.creditsBar.setEnabled(False)

        self.tabWidget.setTabEnabled(0, True)      # enable select files whilst uploading
        print(f"confirm_upload: {self.confirm_upload}")
        self.confirm_upload.setEnabled(True)
        print("END OF AssesSMENt")
        

    def on_upload_complete(self, dataList):
        print("UPLOAD COMPLETE")
        uploaded_count = dataList[0]
        error_count = dataList[1]
        
        # Show completion message
        if error_count == 0:
            QMessageBox.information(self, "Upload Complete", 
                                  f"Upload completed successfully!\n{uploaded_count} files uploaded.")
        else:
            QMessageBox.warning(self, "Upload Complete with Errors", 
                              f"Upload completed.\n{uploaded_count} files uploaded successfully.\n{error_count} files had errors.")
        
        # Clean up upload thread
        if self.uploadThread is not None:
            self.uploadThread.quit()
            self.uploadThread.wait()
            self.uploadThread = None
        
        self.inizialiseSelectFiles()

    def closeEvent(self, a0):
        """Handle application close event to ensure threads are properly cleaned up."""
        # Clean up assessment thread
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()
            
        # Clean up upload thread  
        if self.uploadThread is not None:
            self.uploadThread.quit()
            self.uploadThread.wait()
            
        a0.accept()


    def on_confirm_upload(self):
        """Handle the user confirmation to proceed with the upload."""
        self.tabWidget.setCurrentIndex(2)    # 1 upload      # 0 select files
        self.tabWidget.setTabEnabled(2, True)      # disable select files whilst uploading
        self.tabWidget.setTabEnabled(0, False)      # disable select files whilst uploading
        self.tabWidget.setTabEnabled(1, False)      # disable assessment whilst uploading
        # self.tabWidget.tabBar().setTabTextColor(1, QtGui.QColor("dbde3e"))

        self.labelImage2.setVisible(True)
        
        self.startUploadThread()
        #startUploadThread
        self.UploadResizeProgressBar.setEnabled(True)
        self.UploadResizeProgressBar.setValue(0)
        

def delete_pycache(directory):
    for root, dirs, files in os.walk(directory):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))
            print(f"Deleted: {os.path.join(root, '__pycache__')}")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    delete_pycache(project_root)
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
