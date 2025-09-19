#!/usr/bin/env python3

import sys
import os
import pandas as pd
sys.path.append('.')

def debug_spreadsheet():
    """Debug the spreadsheet to see its actual structure"""
    spreadsheet_path = "/Volumes/Marketing/06. Databases/TAGs final.ods"
    
    print(f"Checking spreadsheet: {spreadsheet_path}")
    print(f"File exists: {os.path.exists(spreadsheet_path)}")
    
    if not os.path.exists(spreadsheet_path):
        print("❌ Spreadsheet file not found!")
        return
    
    try:
        # Try to read the spreadsheet
        print("\n--- Reading spreadsheet with ODF engine ---")
        df = pd.read_excel(spreadsheet_path, sheet_name='TAGs', engine='odf')
        
        print(f"DataFrame shape: {df.shape}")
        print(f"Column names: {list(df.columns)}")
        print("\nFirst 10 rows:")
        print(df.head(10))
        
        print("\n--- Analyzing column data ---")
        for i in range(min(5, len(df.columns))):
            col_data = df.iloc[:, i]
            print(f"Column {i} ({df.columns[i] if i < len(df.columns) else 'unnamed'}):")
            print(f"  Non-null values: {col_data.notna().sum()}")
            if col_data.notna().sum() > 0:
                print(f"  Sample values: {col_data.dropna().head(3).tolist()}")
        
        print("\n--- Looking for category patterns ---")
        # Check column B (index 1) for categories
        if len(df.columns) > 1:
            categories_col = df.iloc[:, 1]
            unique_categories = categories_col.dropna().unique()
            print(f"Unique values in column B: {unique_categories}")
        
        # Check column A (index 0) for colors
        if len(df.columns) > 0:
            colors_col = df.iloc[:, 0]
            unique_colors = colors_col.dropna().unique()
            print(f"Unique values in column A: {unique_colors}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error reading spreadsheet: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_spreadsheet()
