#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def comprehensive_spreadsheet_analysis():
    """Comprehensive analysis of the entire spreadsheet to find all instances of grumpy"""
    try:
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        print(f"[INFO] Comprehensive analysis of: {spreadsheet_path}")
        
        doc = load(spreadsheet_path)
        
        # Find the TAGs sheet
        tags_sheet = None
        for table in doc.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet = table
                break
        
        if not tags_sheet:
            print("[ERROR] TAGs sheet not found")
            return
        
        rows = tags_sheet.getElementsByType(TableRow)
        
        print(f"\n=== COMPLETE SPREADSHEET ANALYSIS ===")
        print(f"Total rows: {len(rows)}")
        
        # Track all instances of "grumpy" (case insensitive)
        grumpy_instances = []
        all_duplicate_words = {}
        
        for row_idx, row in enumerate(rows):
            cells = row.getElementsByType(TableCell)
            row_contents = []
            
            for col_idx, cell in enumerate(cells):
                cell_text = ""
                for p in cell.getElementsByType(P):
                    if p.firstChild:
                        cell_text += str(p.firstChild)
                
                cell_text = cell_text.strip()
                if cell_text:
                    row_contents.append(f"Col{col_idx+1}:'{cell_text}'")
                    
                    # Check for grumpy
                    if cell_text.lower() == "grumpy":
                        grumpy_instances.append((row_idx + 1, col_idx + 1, cell_text))
                    
                    # Track word frequency for duplicate detection
                    word_lower = cell_text.lower()
                    if word_lower not in all_duplicate_words:
                        all_duplicate_words[word_lower] = []
                    all_duplicate_words[word_lower].append((row_idx + 1, col_idx + 1, cell_text))
            
            if row_contents:
                print(f"Row {row_idx + 1}: {' | '.join(row_contents)}")
        
        print(f"\n=== GRUMPY INSTANCES ===")
        print(f"Found {len(grumpy_instances)} instances of 'grumpy':")
        for row, col, text in grumpy_instances:
            print(f"  - Row {row}, Column {col}: '{text}'")
        
        # Find any duplicates in the same row
        print(f"\n=== ROW-LEVEL DUPLICATE ANALYSIS ===")
        for row_idx, row in enumerate(rows):
            cells = row.getElementsByType(TableCell)
            row_words = []
            
            for col_idx, cell in enumerate(cells):
                cell_text = ""
                for p in cell.getElementsByType(P):
                    if p.firstChild:
                        cell_text += str(p.firstChild)
                
                cell_text = cell_text.strip()
                if cell_text and col_idx >= 3:  # Only check tag columns (D+)
                    row_words.append((col_idx + 1, cell_text))
            
            # Check for duplicates in this row
            word_counts = {}
            for col, word in row_words:
                word_lower = word.lower()
                if word_lower not in word_counts:
                    word_counts[word_lower] = []
                word_counts[word_lower].append((col, word))
            
            # Report duplicates in this row
            for word_lower, occurrences in word_counts.items():
                if len(occurrences) > 1:
                    print(f"Row {row_idx + 1} has duplicate '{word_lower}':")
                    for col, original_word in occurrences:
                        print(f"    Column {col}: '{original_word}'")
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze spreadsheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    comprehensive_spreadsheet_analysis()