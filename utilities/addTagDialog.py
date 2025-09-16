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
    
    def __init__(self, spreadsheet_path=None, parent=None, tags_data=None, initial_tag_text=""):
        super().__init__(parent)
        self.spreadsheet_path = spreadsheet_path
        self.existing_categories = []
        self.category_colors = {}  # Store category colors
        self.tags_data = tags_data  # Accept pre-parsed tags data
        self.initial_tag_text = initial_tag_text  # Store initial tag text
        
        # Require tags_data since button should only be enabled when available
        if not self.tags_data:
            raise ValueError("tags_data is required - AddKeywordDialog should only be opened when tags are loaded")
        
        self.init_ui()
        
        # Load categories from provided data
        self.load_categories_from_data()
        
        # Set initial tag text if provided
        if self.initial_tag_text.strip():
            self.tag_text_input.setText(self.initial_tag_text.strip())
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Add New Keyword")
        self.setModal(True)
        self.setFixedSize(400, 350)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Form layout for inputs
        form_layout = QFormLayout()
        
        # Tag text input
        self.tag_text_input = QLineEdit()
        self.tag_text_input.setPlaceholderText("Enter tag text...")
        self.tag_text_input.setMinimumHeight(30)
        form_layout.addRow("Tag Text:", self.tag_text_input)
        
        # Category selection combo (with NEW option)
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(30)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        form_layout.addRow("Category:", self.category_combo)
        
        # New category name input (hidden initially)
        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText("Enter new category name...")
        self.new_category_input.setMinimumHeight(30)
        self.new_category_input.setVisible(False)
        self.new_category_label = QLabel("New Category Name:")
        self.new_category_label.setVisible(False)
        form_layout.addRow(self.new_category_label, self.new_category_input)
        
        # Color picker (only for new categories)
        color_layout = QHBoxLayout()
        self.color_picker = ColorPickerButton("#DDA0DD")  # Default plum color
        self.color_picker_label = QLabel("Category Color:")
        self.color_picker.setEnabled(False)  # Initially disabled
        self.color_picker.setVisible(False)  # Initially hidden
        self.color_picker_label.setVisible(False)  # Initially hidden
        color_layout.addWidget(self.color_picker)
        color_layout.addStretch()
        form_layout.addRow(self.color_picker_label, color_layout)
        
        layout.addLayout(form_layout)
        
        # Information label
        self.info_label = QLabel("Select an existing category.")
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
        """Handle category change to show/hide new category controls"""
        print(f"[DEBUG] Category changed to: '{text}'")
        
        is_new_selected = text == "NEW"
        
        # Show/hide new category controls
        self.new_category_input.setVisible(is_new_selected)
        self.new_category_label.setVisible(is_new_selected)
        self.color_picker.setVisible(is_new_selected)
        self.color_picker_label.setVisible(is_new_selected)
        self.color_picker.setEnabled(is_new_selected)
        
        if is_new_selected:
            self.info_label.setText("Enter a new category name and select a color.")
        else:
            self.info_label.setText("Using existing category - color already set.")
        
        print(f"[DEBUG] New category controls visible: {is_new_selected}")
    
    def set_spreadsheet_path(self, path):
        """Set the path to the spreadsheet file"""
        print(f"[DEBUG] Setting spreadsheet path: {path}")
        self.spreadsheet_path = path
        if not self.tags_data:  # Only load from file if we don't have tags data
            self.load_existing_categories()
    
    def load_categories_from_data(self):
        """Load categories from the provided tags data structure"""
        if not self.tags_data:
            print("[DEBUG] No tags data provided")
            return
            
        self.existing_categories = []
        self.category_colors = {}
        
        try:
            # Extract categories and colors from the tags data structure
            # New structure: [(category_name, category_color, [tag_name, tag_name, ...]), ...]
            for category_name, category_color, tags_in_category in self.tags_data:
                if category_name and category_name.strip():
                    clean_category = category_name.strip()
                    self.existing_categories.append(clean_category)
                    self.category_colors[clean_category] = category_color
            
            print(f"[DEBUG] Loaded {len(self.existing_categories)} categories from tags data:")
            for category in self.existing_categories:
                color = self.category_colors.get(category, "N/A")
                print(f"[DEBUG]   - {category}: {color}")
                
            # Update the combo box with loaded categories
            if hasattr(self, 'category_combo'):
                self.category_combo.clear()
                self.category_combo.addItems(self.existing_categories)
                
                # Add NEW option with special styling
                self.category_combo.addItem("NEW")
                
                # Style the NEW option differently
                model = self.category_combo.model()
                item = model.item(len(self.existing_categories))  # Last item (NEW)
                item.setBackground(QColor("#E6F3FF"))  # Light blue background
                
                print(f"[DEBUG] Category combo populated with {len(self.existing_categories)} categories + NEW option")
                
        except Exception as e:
            print(f"[ERROR] Error in pandas update: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def _update_ods_targeted(self, tag_text, category, color, is_new_category):
        """Simplified precise cell update using pandas .at accessor to avoid format duplication"""
        try:
            import pandas as pd
            
            print(f"[DEBUG] Using simplified precise update for tag '{tag_text}' in category '{category}'")
            
            # Read the spreadsheet data only (no formatting)
            df = pd.read_excel(self.spreadsheet_path, sheet_name='TAGs', engine='odf', header=None)
            print(f"[DEBUG] Loaded {len(df)} rows from spreadsheet")
            
            # Find category row (skip header row 0)
            category_row_index = None
            for index in range(1, len(df)):  # Start from 1 to skip header
                if index < len(df) and len(df.columns) > 1:
                    cell_value = df.iloc[index, 1]  # Column B (category)
                    if pd.notna(cell_value) and str(cell_value).strip().lower() == category.lower():
                        category_row_index = index
                        print(f"[DEBUG] Found category at row {index}")
                        break
            
            if category_row_index is None:
                print(f"[ERROR] Category '{category}' not found")
                return False
            
            # Check for duplicates and find target column
            existing_tags = []
            target_column = None
            
            for col_idx in range(3, len(df.columns)):  # Start from column D (index 3)
                cell_value = df.iloc[category_row_index, col_idx]
                if pd.notna(cell_value) and str(cell_value).strip():
                    existing_tags.append(str(cell_value).strip().lower())
                elif target_column is None:
                    target_column = col_idx
                    break
            
            # Check for duplicate
            if tag_text.lower() in existing_tags:
                print(f"[ERROR] Tag '{tag_text}' already exists")
                return False
            
            if target_column is None:
                print("[ERROR] No empty cells found")
                return False
            
            print(f"[DEBUG] Will add '{tag_text}' at row {category_row_index}, column {target_column}")
            
            # Use .at accessor for precise single-cell assignment (should avoid format propagation)
            df.at[category_row_index, target_column] = tag_text
            
            print(f"[DEBUG] Added tag to cell [{category_row_index}, {target_column}]")
            
            # Write back with minimal disturbance
            with pd.ExcelWriter(self.spreadsheet_path, engine='odf', mode='w') as writer:
                df.to_excel(writer, sheet_name='TAGs', index=False, header=False)
            
            print(f"[DEBUG] Updated file successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error in simplified update: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def _update_xlsx_targeted(self, tag_text, category, color, is_new_category):
        """XLSX-specific update using openpyxl for precise cell updates without formatting issues"""
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import PatternFill
            
            print(f"[DEBUG] Using openpyxl for XLSX tag '{tag_text}' in category '{category}'")
            
            # Load workbook with openpyxl for precise cell control
            workbook = load_workbook(self.spreadsheet_path)
            
            # Get the TAGs worksheet
            if 'TAGs' not in workbook.sheetnames:
                print("[ERROR] TAGs sheet not found in workbook")
                return False
                
            worksheet = workbook['TAGs']
            
            # Find category row (skip header row 1)
            category_row_index = None
            max_row = worksheet.max_row
            
            for row_idx in range(2, max_row + 1):  # Start from row 2 (skip header)
                category_cell = worksheet.cell(row=row_idx, column=2)  # Column B
                if category_cell.value and str(category_cell.value).strip().lower() == category.lower():
                    category_row_index = row_idx
                    print(f"[DEBUG] Found category at row {row_idx}")
                    break
            
            if category_row_index is None:
                if not is_new_category:
                    print(f"[ERROR] Category '{category}' not found")
                    return False
                else:
                    # Create new category row with proper spacing and formatting
                    print(f"[DEBUG] Creating new category '{category}' with color '{color}'")
                    
                    # Find the next available row, then add one more for spacing
                    new_row_index = worksheet.max_row + 2  # +2 for spacing
                    
                    # Convert color to openpyxl PatternFill
                    if color.startswith('#'):
                        color_rgb = color[1:]  # Remove # prefix
                    else:
                        color_rgb = color
                    
                    # Create fill pattern for background color
                    fill = PatternFill(start_color=color_rgb, end_color=color_rgb, fill_type="solid")
                    
                    # Set category data: Column A = empty (no color text), Column B = category name, Column D = first tag
                    # Column A: Empty cell with background color (no text value)
                    color_cell = worksheet.cell(row=new_row_index, column=1)
                    color_cell.value = None  # No text value for color
                    color_cell.fill = fill
                    
                    # Column B: Category name with background color
                    category_cell = worksheet.cell(row=new_row_index, column=2)
                    category_cell.value = category
                    category_cell.fill = fill
                    
                    # Column C: Empty with background color for consistency
                    empty_cell = worksheet.cell(row=new_row_index, column=3)
                    empty_cell.fill = fill
                    
                    # Column D: First tag with background color
                    tag_cell = worksheet.cell(row=new_row_index, column=4)
                    tag_cell.value = tag_text
                    tag_cell.fill = fill
                    
                    # Apply background color to the entire row (up to reasonable column limit)
                    max_columns = worksheet.max_column + 10  # Extend beyond current max for future use
                    for col_idx in range(5, max_columns + 1):  # Start from column E onwards
                        cell = worksheet.cell(row=new_row_index, column=col_idx)
                        cell.fill = fill
                    
                    print(f"[DEBUG] Created new category row {new_row_index} with background color and tag '{tag_text}'")
                    
                    # Save the workbook
                    workbook.save(self.spreadsheet_path)
                    workbook.close()
                    
                    print(f"[DEBUG] New category and tag added successfully")
                    return True
            
            # Check for duplicates and find target column
            existing_tags = []
            target_column = None
            max_col = worksheet.max_column
            
            for col_idx in range(4, max_col + 2):  # Start from column D (4), check beyond max_col
                cell = worksheet.cell(row=category_row_index, column=col_idx)
                if cell.value and str(cell.value).strip():
                    existing_tags.append(str(cell.value).strip().lower())
                elif target_column is None:
                    target_column = col_idx
                    break
            
            # Check for duplicate
            if tag_text.lower() in existing_tags:
                print(f"[ERROR] Tag '{tag_text}' already exists")
                return False
            
            if target_column is None:
                print("[ERROR] No empty cells found")
                return False
            
            print(f"[DEBUG] Will add '{tag_text}' at row {category_row_index}, column {target_column}")
            
            # Get the target cell
            target_cell = worksheet.cell(row=category_row_index, column=target_column)
            
            # Preserve existing formatting by copying from adjacent cell
            if target_column > 4:  # If not the first tag column
                source_cell = worksheet.cell(row=category_row_index, column=target_column - 1)
                if hasattr(source_cell, 'fill') and source_cell.fill:
                    try:
                        # Create a new PatternFill with the same parameters
                        from openpyxl.styles import PatternFill
                        if hasattr(source_cell.fill, 'start_color') and source_cell.fill.start_color:
                            fill_color = source_cell.fill.start_color.rgb if hasattr(source_cell.fill.start_color, 'rgb') else None
                            if fill_color and fill_color != '00000000':  # Skip default/transparent fills
                                target_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                    except Exception as fill_error:
                        print(f"[DEBUG] Could not copy fill formatting: {fill_error}")
            else:
                # Copy formatting from category cell (column B) for consistency
                category_cell = worksheet.cell(row=category_row_index, column=2)
                if hasattr(category_cell, 'fill') and category_cell.fill:
                    try:
                        from openpyxl.styles import PatternFill
                        if hasattr(category_cell.fill, 'start_color') and category_cell.fill.start_color:
                            fill_color = category_cell.fill.start_color.rgb if hasattr(category_cell.fill.start_color, 'rgb') else None
                            if fill_color and fill_color != '00000000':  # Skip default/transparent fills
                                target_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                    except Exception as fill_error:
                        print(f"[DEBUG] Could not copy category fill formatting: {fill_error}")
            
            # Set the value in the specific cell
            target_cell.value = tag_text
            
            print(f"[DEBUG] Added tag to cell [{category_row_index}, {target_column}] with preserved formatting")
            
            # Save the workbook
            workbook.save(self.spreadsheet_path)
            workbook.close()
            
            print(f"[DEBUG] XLSX file updated successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error in XLSX update: {e}")
            import traceback
            traceback.print_exc()
            return False

    def add_tag(self):
        """Add the new tag to the spreadsheet"""
        print("[DEBUG] === ADD TAG FUNCTION CALLED ===")
        
        # Validate inputs
        tag_text = self.tag_text_input.text().strip()
        print(f"[DEBUG] Tag text: '{tag_text}'")
        if not tag_text:
            print("[ERROR] No tag text provided")
            QMessageBox.warning(self, "Invalid Input", "Please enter tag text.")
            return
        
        selected_category = self.category_combo.currentText().strip()
        print(f"[DEBUG] Selected category from combo: '{selected_category}'")
        
        # Check if NEW is selected
        if selected_category == "NEW":
            print("[DEBUG] NEW category selected")
            category = self.new_category_input.text().strip()
            print(f"[DEBUG] New category name: '{category}'")
            
            if not category:
                print("[ERROR] No new category name provided")
                QMessageBox.warning(self, "Invalid Input", "Please enter a name for the new category.")
                return
            
            # Check if new category already exists
            if category in self.existing_categories:
                print(f"[ERROR] Category '{category}' already exists")
                QMessageBox.warning(self, "Invalid Input", f"Category '{category}' already exists. Please choose a different name.")
                return
            
            is_new_category = True
            category_color = self.color_picker.get_color().name()
            print(f"[DEBUG] New category color: {category_color}")
            
        else:
            # Existing category selected
            category = selected_category
            is_new_category = False
            category_color = self.category_colors.get(category, "#DDA0DD")
            print(f"[DEBUG] Using existing category '{category}' with color {category_color}")
        
        if not category:
            print("[ERROR] No category selected or entered")
            QMessageBox.warning(self, "Invalid Input", "Please select an existing category or enter a new one.")
            return
        
        print(f"[DEBUG] Final values - Tag: '{tag_text}', Category: '{category}', Color: '{category_color}', Is New: {is_new_category}")
        
        # Try to update the spreadsheet
        print("[DEBUG] Attempting to update spreadsheet...")
        update_result = self.update_spreadsheet(tag_text, category, category_color, is_new_category)
        
        if update_result is True:
            print("[SUCCESS] Tag added successfully")
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
        elif update_result is False:
            # Specific case for duplicate tags or cell capacity issues
            print(f"[ERROR] Tag addition failed: '{tag_text}' in category '{category}'")
            QMessageBox.warning(self, "Cannot Add Tag", 
                              f"Cannot add tag '{tag_text}' to category '{category}'.\n\n"
                              f"This may be because:\n"
                              f"• The tag already exists in this category\n"
                              f"• No empty cells are available in the spreadsheet row\n"
                              f"• The spreadsheet structure is corrupted\n\n"
                              f"Try manually adding columns in LibreOffice or check for duplicate tags.")
        else:
            print("[ERROR] Failed to update spreadsheet")
            QMessageBox.critical(self, "Error", "Failed to add tag to spreadsheet.")
    
    def update_spreadsheet(self, tag_text, category, color, is_new_category):
        """Update the spreadsheet with the new tag while preserving formatting"""
        print(f"[DEBUG] === UPDATE SPREADSHEET FUNCTION ===")
        print(f"[DEBUG] Spreadsheet path: {self.spreadsheet_path}")
        print(f"[DEBUG] Tag: '{tag_text}', Category: '{category}', Color: '{color}', Is New: {is_new_category}")
        
        if not self.spreadsheet_path:
            print("[ERROR] No spreadsheet path specified")
            return False
        
        try:
            # Try to use ODF method first to preserve formatting
            if self.spreadsheet_path.lower().endswith('.ods'):
                return self._update_ods_preserving_format(tag_text, category, color, is_new_category)
            else:
                # Fall back to pandas for non-ODS files
                return self._update_with_pandas(tag_text, category, color, is_new_category)
                
        except Exception as e:
            print(f"[ERROR] Error updating spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _update_ods_preserving_format(self, tag_text, category, color, is_new_category):
        """Update ODS file while preserving cell formatting"""
        try:
            from odf.opendocument import load
            from odf.table import Table, TableRow, TableCell
            from odf.text import P
            
            print("[DEBUG] Using ODF method to preserve formatting...")
            print(f"[DEBUG] Looking for category '{category}' in spreadsheet")
            
            # Load the existing document
            doc = load(self.spreadsheet_path)
            
            # Find the TAGs sheet
            tags_sheet = None
            for table in doc.getElementsByType(Table):
                if table.getAttribute('name') == 'TAGs':
                    tags_sheet = table
                    break
            
            if not tags_sheet:
                print("[ERROR] TAGs sheet not found")
                return False
            
            # Get all rows
            rows = tags_sheet.getElementsByType(TableRow)
            category_row = None
            category_row_index = None
            
            # Find the category row
            for row_index, row in enumerate(rows):
                cells = row.getElementsByType(TableCell)
                if len(cells) > 1:
                    # Get text from the second cell (category column)
                    category_cell = cells[1]
                    category_text = ""
                    for p in category_cell.getElementsByType(P):
                        if p.firstChild:
                            category_text += str(p.firstChild)
                    
                    if category_text.strip().lower() == category.lower():
                        category_row = row
                        category_row_index = row_index
                        print(f"[DEBUG] Found category '{category}' at row {row_index}")
                        break
            
            if is_new_category:
                print("[ERROR] New category creation with ODF not implemented yet")
                # Fall back to pandas for new categories
                return self._update_with_pandas(tag_text, category, color, is_new_category)
            
            if category_row is None:
                print(f"[ERROR] Category '{category}' not found in file")
                return False
            
            # Find the first empty cell starting from column D (index 3)
            cells = category_row.getElementsByType(TableCell)
            tag_added = False
            
            # First, check if the tag already exists in this category
            existing_tags = []
            for cell_index in range(3, len(cells)):
                cell = cells[cell_index]
                cell_text = ""
                for p in cell.getElementsByType(P):
                    if p.firstChild:
                        cell_text += str(p.firstChild)
                
                if cell_text.strip():
                    existing_tags.append(cell_text.strip().lower())
            
            # Check for duplicate
            if tag_text.lower() in existing_tags:
                print(f"[ERROR] Tag '{tag_text}' already exists in category '{category}'")
                return False
            
            # Now find an empty cell to add the new tag
            for cell_index in range(3, len(cells)):
                cell = cells[cell_index]
                # Check if cell is empty
                cell_text = ""
                for p in cell.getElementsByType(P):
                    if p.firstChild:
                        cell_text += str(p.firstChild)
                
                if not cell_text.strip():
                    # Found empty cell, add the tag
                    # Clear existing content
                    for p in cell.getElementsByType(P):
                        cell.removeChild(p)
                    
                    # Add new text
                    new_p = P()
                    new_p.addText(tag_text)
                    cell.appendChild(new_p)
                    
                    print(f"[DEBUG] Added tag '{tag_text}' to cell at column {cell_index}")
                    tag_added = True
                    break
            
            if not tag_added:
                print("[DEBUG] No empty cell found in existing row structure")
                print(f"[ERROR] Cannot add tag '{tag_text}' to category '{category}' - all available cells are occupied")
                print("[INFO] Please manually add more columns to the spreadsheet or remove unused tags first")
                return False
            
            # Save the document
            doc.save(self.spreadsheet_path)
            print("[SUCCESS] ODS file updated while preserving formatting")
            return True
            
        except Exception as e:
            print(f"[ERROR] ODF method failed: {e}")
            print(f"[ERROR] Cannot add tag '{tag_text}' - ODF operation failed and pandas fallback disabled to prevent formatting loss")
            return False
    
    def _update_with_pandas(self, tag_text, category, color, is_new_category):
        """Update spreadsheet using precise cell targeting to avoid format-based duplication"""
        try:
            # Determine file type and engine
            file_extension = os.path.splitext(self.spreadsheet_path)[1].lower().lstrip('.')
            print(f"[DEBUG] File extension: {file_extension}")
            
            if file_extension == 'ods':
                # For ODS files, use a hybrid approach to avoid format-based duplication
                return self._update_ods_targeted(tag_text, category, color, is_new_category)
            elif file_extension in ['xlsx', 'xlsm']:
                # For Excel files, use openpyxl for precise cell updates
                return self._update_xlsx_targeted(tag_text, category, color, is_new_category)
            elif file_extension == 'xls':
                engine = 'xlrd'
            else:
                engine = 'odf'
            
            print(f"[DEBUG] Using engine: {engine}")
            
            # Read the existing spreadsheet - IMPORTANT: Use header=None for files without header row
            if os.path.exists(self.spreadsheet_path):
                print("[DEBUG] Reading existing spreadsheet...")
                df = pd.read_excel(self.spreadsheet_path, sheet_name='TAGs', engine=engine, header=None)
                print(f"[DEBUG] Loaded {len(df)} rows from spreadsheet")
            else:
                print("[DEBUG] Creating new dataframe (file doesn't exist)")
                # Create new dataframe if file doesn't exist
                df = pd.DataFrame()
            
            # Find if category already exists (skip row 0 which is the header row)
            category_row_index = None
            for index, row in df.iterrows():
                # Skip the header row (index 0)
                if index == 0:
                    continue
                    
                if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip().lower() == category.lower():
                    category_row_index = index
                    print(f"[DEBUG] Found existing category at row {index}")
                    break
            
            if category_row_index is not None and not is_new_category:
                print("[DEBUG] Adding tag to existing category")
                # Category exists - add tag to the end of existing tags
                row = df.iloc[category_row_index]
                
                # First, check if the tag already exists in this category
                existing_tags = []
                for col_idx in range(3, len(df.columns)):
                    cell_value = row.iloc[col_idx]
                    if pd.notna(cell_value) and str(cell_value).strip():
                        existing_tags.append(str(cell_value).strip().lower())
                
                # Check for duplicate
                if tag_text.lower() in existing_tags:
                    print(f"[ERROR] Tag '{tag_text}' already exists in category '{category}'")
                    return False
                
                # Find the first empty column starting from column D (index 3)
                tag_added = False
                for col_idx in range(3, len(df.columns)):
                    if pd.isna(row.iloc[col_idx]) or str(row.iloc[col_idx]).strip() == '':
                        df.iloc[category_row_index, col_idx] = tag_text
                        print(f"[DEBUG] Added tag to column {col_idx}")
                        tag_added = True
                        break
                
                if not tag_added:
                    # No empty column found, add a new column
                    new_col_name = f"Tag_{len(df.columns)}"
                    df[new_col_name] = ""
                    df.iloc[category_row_index, len(df.columns)-1] = tag_text
                    print(f"[DEBUG] Added new column {new_col_name} and added tag")
            else:
                print("[DEBUG] Creating new category row")
                # Category doesn't exist or is new - create new row
                new_row = [""] * max(len(df.columns), 4)  # Ensure at least 4 columns
                new_row[0] = color  # Color in column A
                new_row[1] = category  # Category in column B
                new_row[3] = tag_text  # First tag in column D
                
                print(f"[DEBUG] New row data: {new_row[:4]}...")
                
                # Extend dataframe if needed
                while len(new_row) > len(df.columns):
                    df[f"Tag_{len(df.columns)}"] = ""
                    print(f"[DEBUG] Added column Tag_{len(df.columns)-1}")
                
                # Add the new row
                df.loc[len(df)] = new_row
                print(f"[DEBUG] Added new row at index {len(df)-1}")
            
            # Write back to file
            print(f"[DEBUG] Writing spreadsheet back to {self.spreadsheet_path}")
            
            # Ensure the directory exists before writing
            directory = os.path.dirname(self.spreadsheet_path)
            if directory and not os.path.exists(directory):
                print(f"[DEBUG] Creating directory: {directory}")
                try:
                    os.makedirs(directory, exist_ok=True)
                except OSError as dir_error:
                    print(f"[ERROR] Cannot create directory {directory}: {dir_error}")
                    # Fall back to local data directory
                    local_data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
                    os.makedirs(local_data_dir, exist_ok=True)
                    fallback_path = os.path.join(local_data_dir, os.path.basename(self.spreadsheet_path))
                    print(f"[DEBUG] Using fallback path: {fallback_path}")
                    self.spreadsheet_path = fallback_path
            
            with pd.ExcelWriter(self.spreadsheet_path, engine=engine) as writer:
                df.to_excel(writer, sheet_name='TAGs', index=False, header=False)
            
            print(f"[SUCCESS] Successfully added tag '{tag_text}' to category '{category}' in spreadsheet")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error updating spreadsheet: {e}")
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
