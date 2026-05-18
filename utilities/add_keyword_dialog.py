"""
Add Keyword Dialog - Handles adding new tags to the tag widgets system

This module provides functionality for:
- Creating a dialog to add new tags with text, color, and category
- Updating the spreadsheet with new tag entries
- Integrating with the existing tag_widgets system

Structure based on analysis:
- Tags are stored in a spreadsheet with "TAGs" sheet
- Each row represents a category (column B)
- Tags are stored in columns D onwards in the same row as their category
- Each tag has: text, color, and category
"""

import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QComboBox, QColorDialog, 
                             QLabel, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPalette


class ColorPickerButton(QPushButton):
    """Custom button that displays selected color and opens color picker"""
    
    colorChanged = pyqtSignal(QColor)
    
    def __init__(self, initial_color="#E6E6FA", parent=None):
        super().__init__(parent)
        self.selected_color = QColor(initial_color)
        self.setText("Choose Color")
        self.setMinimumHeight(30)
        self.setMaximumWidth(120)
        self.update_button_style()
        self.clicked.connect(self.open_color_dialog)
    
    def update_button_style(self):
        """Update button style to show the selected color"""
        color_name = self.selected_color.name()
        text_color = "white" if self.selected_color.lightness() < 128 else "black"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_name};
                color: {text_color};
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
        """)
    
    def open_color_dialog(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(self.selected_color, self, "Choose Tag Color")
        if color.isValid():
            self.selected_color = color
            self.update_button_style()
            self.colorChanged.emit(color)
    
    def get_color(self):
        """Get the currently selected color"""
        return self.selected_color
    
    def set_color(self, color):
        """Set the color programmatically"""
        if isinstance(color, str):
            color = QColor(color)
        self.selected_color = color
        self.update_button_style()


class AddKeywordDialog(QDialog):
    """Dialog for adding new keywords/tags to the system"""
    
    # Signal emitted when a new tag is successfully added
    tagAdded = pyqtSignal(str, str, str)  # text, color, category
    
    def __init__(self, spreadsheet_path=None, parent=None):
        super().__init__(parent)
        self.spreadsheet_path = spreadsheet_path
        self.existing_categories = []
        self.category_colors = {}  # Add this line to store category colors
        self.init_ui()
        self.load_existing_categories()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Add New Keyword")
        self.setModal(True)
        self.setFixedSize(400, 280)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Form layout for inputs
        form_layout = QFormLayout()
        
        # Tag text input
        self.tag_text_input = QLineEdit()
        self.tag_text_input.setPlaceholderText("Enter tag text...")
        self.tag_text_input.setMinimumHeight(30)
        form_layout.addRow("Tag Text:", self.tag_text_input)
        
        # Category selection/input
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setMinimumHeight(30)
        self.category_combo.lineEdit().setPlaceholderText("Select existing or enter new category...")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        form_layout.addRow("Category:", self.category_combo)
        
        # Color picker (only for new categories)
        color_layout = QHBoxLayout()
        self.color_picker = ColorPickerButton("#DDA0DD")  # Default plum color
        self.color_picker_label = QLabel("Color (for new category):")
        self.color_picker.setEnabled(False)  # Initially disabled
        color_layout.addWidget(self.color_picker)
        color_layout.addStretch()
        form_layout.addRow(self.color_picker_label, color_layout)
        
        layout.addLayout(form_layout)
        
        # Information label
        self.info_label = QLabel("Select an existing category or type a new one.")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        layout.addWidget(self.info_label)
        
        # Add some spacing
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.add_button = QPushButton("Add Tag")
        self.add_button.setDefault(True)
        self.add_button.clicked.connect(self.add_tag)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.add_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect enter key to add tag
        self.tag_text_input.returnPressed.connect(self.add_tag)
    
    def on_category_changed(self, text):
        """Handle category change to enable/disable color picker"""
        is_new_category = text not in self.existing_categories
        self.color_picker.setEnabled(is_new_category)
        
        if is_new_category:
            self.info_label.setText("New category - please select a color.")
            self.color_picker_label.setText("Color (for new category):")
        else:
            self.info_label.setText("Existing category - color already set.")
            self.color_picker_label.setText("Color (existing category):")
    
    def set_spreadsheet_path(self, path):
        """Set the path to the spreadsheet file"""
        self.spreadsheet_path = path
        self.load_existing_categories()
    
    def load_existing_categories(self):
        """Load existing categories and their colors from the spreadsheet"""
        if not self.spreadsheet_path or not os.path.exists(self.spreadsheet_path):
            # Add some default categories if no spreadsheet is available
            default_categories = ["General", "Business", "Locations", "Colors", "Activities"]
            self.existing_categories = default_categories
            self.category_combo.addItems(default_categories)
            return
        
        try:
            # Determine file type and engine
            file_extension = os.path.splitext(self.spreadsheet_path)[1].lower().lstrip('.')
            
            if file_extension == 'ods':
                engine = 'odf'
            elif file_extension in ['xlsx', 'xlsm']:
                engine = 'openpyxl'
            elif file_extension == 'xls':
                engine = 'xlrd'
            else:
                engine = 'odf'
            
            # Read the TAGs sheet
            df = pd.read_excel(self.spreadsheet_path, sheet_name='TAGs', engine=engine)
            
            # Extract unique categories from column B (index 1) and colors from column A (index 0)
            categories = []
            self.category_colors = {}  # Store category colors
            
            for index, row in df.iterrows():
                if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip():
                    category_name = str(row.iloc[1]).strip()
                    if category_name not in categories:
                        categories.append(category_name)
                        # Get color from column A (index 0)
                        if len(row) > 0 and pd.notna(row.iloc[0]):
                            color_value = str(row.iloc[0]).strip()
                            # Validate it looks like a color (starts with # and has 6 hex digits)
                            if color_value.startswith('#') and len(color_value) == 7:
                                self.category_colors[category_name] = color_value
                            else:
                                self.category_colors[category_name] = "#DDA0DD"  # Default lavender
                        else:
                            self.category_colors[category_name] = "#DDA0DD"  # Default lavender
            
            self.existing_categories = sorted(categories)
            self.category_combo.addItems(self.existing_categories)
            
        except Exception as e:
            print(f"Error loading categories from spreadsheet: {e}")
            # Fallback to default categories
            default_categories = ["General", "Business", "Locations", "Colors", "Activities"]
            self.existing_categories = default_categories
            self.category_colors = {}
            self.category_combo.addItems(default_categories)
    
    def add_tag(self):
        """Add the new tag to the spreadsheet"""
        # Validate inputs
        tag_text = self.tag_text_input.text().strip()
        if not tag_text:
            QMessageBox.warning(self, "Invalid Input", "Please enter tag text.")
            return
        
        category = self.category_combo.currentText().strip()
        if not category:
            QMessageBox.warning(self, "Invalid Input", "Please select or enter a category.")
            return
        
        # Determine if this is a new category
        is_new_category = category not in self.existing_categories
        
        # Get color - only needed for new categories
        if is_new_category:
            if not self.color_picker.isEnabled():
                QMessageBox.warning(self, "Invalid Input", "Please select a color for the new category.")
                return
            category_color = self.color_picker.get_color().name()
        else:
            # Use existing category color
            category_color = self.category_colors.get(category, "#DDA0DD")
        
        # Try to update the spreadsheet
        if self.update_spreadsheet(tag_text, category, category_color, is_new_category):
            # Emit signal that tag was added
            self.tagAdded.emit(tag_text, category_color, category)
            
            # Show success message
            if is_new_category:
                QMessageBox.information(self, "Success", 
                                      f"New category '{category}' created with tag '{tag_text}'!")
            else:
                QMessageBox.information(self, "Success", 
                                      f"Tag '{tag_text}' added to existing category '{category}'!")
            
            # Close dialog
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to add tag to spreadsheet.")
    
    def update_spreadsheet(self, tag_text, category, color, is_new_category):
        """Update the spreadsheet with the new tag"""
        if not self.spreadsheet_path:
            print("No spreadsheet path specified")
            return False
        
        try:
            # Determine file type and engine
            file_extension = os.path.splitext(self.spreadsheet_path)[1].lower().lstrip('.')
            
            if file_extension == 'ods':
                engine = 'odf'
            elif file_extension in ['xlsx', 'xlsm']:
                engine = 'openpyxl'
            elif file_extension == 'xls':
                engine = 'xlrd'
            else:
                engine = 'odf'
            
            # Read the existing spreadsheet
            if os.path.exists(self.spreadsheet_path):
                df = pd.read_excel(self.spreadsheet_path, sheet_name='TAGs', engine=engine)
            else:
                # Create new dataframe if file doesn't exist
                df = pd.DataFrame()
            
            # Find if category already exists
            category_row_index = None
            for index, row in df.iterrows():
                if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip().lower() == category.lower():
                    category_row_index = index
                    break
            
            if category_row_index is not None and not is_new_category:
                # Category exists - add tag to the end of existing tags
                row = df.iloc[category_row_index]
                
                # Find the first empty column starting from column D (index 3)
                for col_idx in range(3, len(df.columns)):
                    if pd.isna(row.iloc[col_idx]) or str(row.iloc[col_idx]).strip() == '':
                        df.iloc[category_row_index, col_idx] = tag_text
                        break
                else:
                    # No empty column found, add a new column
                    new_col_name = f"Tag_{len(df.columns)}"
                    df[new_col_name] = ""
                    df.iloc[category_row_index, len(df.columns)-1] = tag_text
            else:
                # Category doesn't exist or is new - create new row
                new_row = [""] * max(len(df.columns), 4)  # Ensure at least 4 columns
                new_row[0] = color  # Color in column A
                new_row[1] = category  # Category in column B
                new_row[3] = tag_text  # First tag in column D
                
                # Extend dataframe if needed
                while len(new_row) > len(df.columns):
                    df[f"Tag_{len(df.columns)}"] = ""
                
                # Add the new row
                df.loc[len(df)] = new_row
            
            # Write back to file
            with pd.ExcelWriter(self.spreadsheet_path, engine=engine) as writer:
                df.to_excel(writer, sheet_name='TAGs', index=False)
            
            print(f"Successfully added tag '{tag_text}' to category '{category}' in spreadsheet")
            return True
            
        except Exception as e:
            print(f"Error updating spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_add_keyword_dialog():
    """Test function for the Add Keyword Dialog"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create and show the dialog
    dialog = AddKeywordDialog()
    
    # Connect signal to see when tags are added
    def on_tag_added(text, color, category):
        print(f"Tag added: '{text}' with color '{color}' in category '{category}'")
    
    dialog.tagAdded.connect(on_tag_added)
    
    result = dialog.exec_()
    print(f"Dialog result: {result}")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_add_keyword_dialog()
