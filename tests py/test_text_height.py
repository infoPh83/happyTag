#!/usr/bin/env python3

"""
Test script to verify text field height behavior
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt

def test_text_field_height():
    """Test text field auto-height behavior"""
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Text Field Height Test")
    window.resize(400, 300)
    
    layout = QVBoxLayout(window)
    
    # Create test text field
    text_field = QTextEdit()
    text_field.setFixedWidth(300)
    text_field.setFixedHeight(28)
    text_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    text_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    text_field.setPlaceholderText("Type some text to test auto-height...")
    
    def update_height():
        """Auto-height update function"""
        content = text_field.toPlainText()
        if not content:
            text_field.setFixedHeight(28)
            return
            
        # Force document to recalculate size
        text_field.document().adjustSize()
        
        # Calculate required height based on document content  
        doc_height = int(text_field.document().size().height())
        margins = text_field.contentsMargins()
        padding = 8
        new_height = doc_height + margins.top() + margins.bottom() + padding
        
        # Set minimum height but no maximum - always show all content
        final_height = max(28, new_height)
        text_field.setFixedHeight(final_height)
        print(f"Content lines: {content.count(chr(10))+1}, Height: {final_height}")
    
    # Connect text change to height update
    text_field.textChanged.connect(update_height)
    
    layout.addWidget(text_field)
    
    window.show()
    
    print("Text Field Height Test")
    print("======================")
    print("1. Type text to see auto-height expansion")
    print("2. Press Enter to create new lines")
    print("3. All text should always be visible")
    print("4. Close window to exit")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_text_field_height()
