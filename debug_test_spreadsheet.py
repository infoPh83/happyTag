#!/usr/bin/env python3

import pandas as pd
import os

def debug_test_spreadsheet():
    """Debug the test spreadsheet structure"""
    
    spreadsheet_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/test images/Cloudinary tags.ods"
    
    print(f"Checking spreadsheet: {spreadsheet_path}")
    print(f"File exists: {os.path.exists(spreadsheet_path)}")
    
    if not os.path.exists(spreadsheet_path):
        return
    
    try:
        # Check if it has multiple sheets
        excel_file = pd.ExcelFile(spreadsheet_path, engine='odf')
        print(f"Available sheets: {excel_file.sheet_names}")
        
        # Try reading the first sheet (or 'TAGs' if it exists)
        sheet_name = 'TAGs' if 'TAGs' in excel_file.sheet_names else excel_file.sheet_names[0]
        print(f"Reading sheet: '{sheet_name}'")
        
        df = pd.read_excel(spreadsheet_path, sheet_name=sheet_name, engine='odf')
        
        print(f"Spreadsheet shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        print("\nFirst few rows:")
        print(df.head(10))
        
        print("\nData types:")
        print(df.dtypes)
        
        print("\nSample data from each column:")
        for i, col in enumerate(df.columns):
            print(f"Column {i} ({col}):")
            # Show first few non-null values
            non_null_values = df[col].dropna().head(5)
            for idx, val in non_null_values.items():
                print(f"  Row {idx}: '{val}' (type: {type(val)})")
            print()
        
        # Look for category patterns
        print("Looking for category patterns...")
        if len(df.columns) > 1:
            # Check column B (index 1) for categories
            categories = df.iloc[:, 1].dropna().unique()
            print(f"Unique values in column B (potential categories): {categories}")
        
        if len(df.columns) > 0:
            # Check column A (index 0) for colors
            colors = df.iloc[:, 0].dropna().unique()
            print(f"Unique values in column A (potential colors): {colors}")
        
    except Exception as e:
        print(f"Error reading spreadsheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_test_spreadsheet()
