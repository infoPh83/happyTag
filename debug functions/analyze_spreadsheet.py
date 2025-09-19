#!/usr/bin/env python3
"""
Analyze the updated spreadsheet structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.settings_dialog import SettingsDialog
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
from odf.style import Style, TableCellProperties
import pandas as pd

def analyze_new_spreadsheet_structure():
    """Analyze the updated spreadsheet structure"""
    
    settings = SettingsDialog.get_saved_settings()
    cloudinary_tags_path = settings.get('cloudinary_tags_path')
    
    if not cloudinary_tags_path or not os.path.exists(cloudinary_tags_path):
        print(f"[ERROR] Cloudinary tags file not found: {cloudinary_tags_path}")
        return False
    
    print(f"[INFO] Analyzing updated spreadsheet: {cloudinary_tags_path}")
    
    try:
        # First, check with pandas to see the basic structure
        print("\n=== PANDAS ANALYSIS ===")
        df = pd.read_excel(cloudinary_tags_path, engine='odf', sheet_name='TAGs', header=None)
        print(f"Spreadsheet has {len(df)} rows and {len(df.columns)} columns")
        
        row_count = 0
        for index, row in df.iterrows():
            if row_count >= 15:  # Only show first 15 rows
                break
            row_count += 1
            if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip():
                category = str(row.iloc[1]).strip()
                print(f"\nRow {index}: Category '{category}'")
                # Show content of first 8 columns
                for col in range(min(8, len(row))):
                    value = row.iloc[col]
                    if pd.notna(value) and str(value).strip():
                        print(f"  Col {col}: '{str(value).strip()}'")
        
        # Now check with ODF to see background colors
        print("\n=== ODF COLOR ANALYSIS ===")
        doc = load(cloudinary_tags_path)
        tables = doc.getElementsByType(Table)
        
        if tables:
            table = tables[0]
            rows = table.getElementsByType(TableRow)
            
            for row_index, row in enumerate(rows[:15]):
                cells = row.getElementsByType(TableCell)
                if len(cells) > 1:
                    # Get category name from column B
                    category_cell = cells[1]
                    category_text = ""
                    for p in category_cell.getElementsByType(P):
                        if p.firstChild:
                            category_text += str(p.firstChild)
                    
                    if category_text.strip():
                        print(f"\nRow {row_index}: Category '{category_text.strip()}'")
                        
                        # Check background colors for first few cells
                        for col_index in range(min(6, len(cells))):
                            cell = cells[col_index]
                            style_name = cell.getAttribute('stylename')
                            
                            # Get cell content
                            cell_content = ""
                            for p in cell.getElementsByType(P):
                                if p.firstChild:
                                    cell_content += str(p.firstChild)
                            
                            # Get background color
                            bg_color = None
                            if style_name:
                                for style in doc.automaticstyles.getElementsByType(Style):
                                    if style.getAttribute('name') == style_name:
                                        for prop in style.getElementsByType(TableCellProperties):
                                            color = prop.getAttribute('backgroundcolor')
                                            if color:
                                                bg_color = color
                                                break
                            
                            if cell_content.strip() or bg_color:
                                print(f"  Col {col_index}: '{cell_content.strip()}' (bg: {bg_color or 'none'})")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze spreadsheet: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_new_spreadsheet_structure()